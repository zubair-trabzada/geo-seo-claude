/**
 * Premier Equipment — Cloudflare Worker
 *
 * Public endpoints (no auth):
 *   POST /api/chat         live AI grounded in brain.json
 *   POST /api/lead         website lead capture (buyer/seller/contact/quote)
 *   GET  /files/:token     download a quote/PO/BOL PDF from R2 (HMAC-validated)
 *
 * Admin endpoints (Cloudflare Access JWT, ADMIN_TOKEN bearer in dev):
 *   GET  /api/admin/me                       who am I (auth probe)
 *   GET  /api/admin/clients                  list
 *   POST /api/admin/clients                  create
 *   GET  /api/admin/clients/:id              read (+ recent docs)
 *   PUT  /api/admin/clients/:id              update
 *   DELETE /api/admin/clients/:id            delete (only if no docs)
 *   GET  /api/admin/documents                list (filterable by client_id, kind)
 *   POST /api/admin/documents                upload PDF to R2 + insert row (base64-encoded body)
 *   GET  /api/admin/documents/:id            read
 *   PUT  /api/admin/documents/:id            update status / amount / title
 *   POST /api/admin/documents/:id/rotate     rotate share_secret (revokes existing links)
 *   DELETE /api/admin/documents/:id          delete (removes R2 + row)
 *   GET  /api/admin/dashboard                aggregated KPIs + today's briefing
 *   GET  /api/admin/briefings                history of past briefings (last 30)
 *   POST /api/admin/briefing/run             manually regenerate today's briefing
 *   GET  /api/admin/bookings                 voice-booked callbacks
 *   PUT  /api/admin/bookings/:id             update booking status
 *   GET  /api/admin/calls                    call transcripts
 *   GET  /api/admin/calls/:id                single call (transcript + summary)
 *   POST /api/admin/clients/:id/upload-link  generate (or fetch) the client's upload URL
 *   DELETE /api/admin/clients/:id/upload-link rotate the client's upload secret
 *   GET  /api/admin/uploads                  recent customer uploads (filter ?client_id=)
 *   GET  /api/admin/uploads/:id/file         download a customer-uploaded file (from R2)
 *
 * Voice (Retell webhook secret):
 *   POST /api/voice/lookup_machine           inventory lookup tool
 *   POST /api/voice/book_call                book a callback for Nicole
 *   POST /api/voice/create_lead              capture a lead from the call
 *   POST /api/voice/post_call                Retell post-call webhook (transcript)
 *
 * Public customer upload (HMAC-validated):
 *   POST /api/upload/:token                  multipart files for a specific client folder
 *
 * Scheduled (cron, defined in wrangler.toml [triggers]):
 *   Daily — generate the morning briefing, store it, email Nicole.
 *
 * Deploy:  cd worker && wrangler deploy   (see ../DEPLOY-PHASE2.md)
 */
import brain from "./brain.json";

// ---------- helpers ---------------------------------------------------------

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, Cf-Access-Jwt-Assertion",
};
const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json", ...CORS } });
const err = (msg, status = 400) => json({ error: msg }, status);

const trim = (v, n) => String(v == null ? "" : v).slice(0, n);
const now  = () => new Date().toISOString();

function randHex(bytes) {
  const u = new Uint8Array(bytes);
  crypto.getRandomValues(u);
  return Array.from(u, b => b.toString(16).padStart(2, "0")).join("");
}
const newClientId    = () => "c_" + randHex(6);
const newDocId       = () => "d_" + randHex(6);
const newBriefingId  = () => "b_" + randHex(6);
const newBookingId   = () => "bk_" + randHex(6);
const newCallRecId   = () => "cr_" + randHex(6);
const newUploadId    = () => "up_" + randHex(6);

const safeFilename = (s) => String(s || "file").replace(/[^a-zA-Z0-9._-]+/g, "_").slice(0, 120);
const MAX_UPLOAD_BYTES = 20 * 1024 * 1024;   // 20 MB per file (defensive)
const MAX_UPLOAD_FILES = 12;

// Days between two ISO timestamps (rounded down)
function ageDays(iso) {
  if (!iso) return 0;
  return Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
}
function todayUtc() { return new Date().toISOString().slice(0, 10); }

async function hmacHex(secret, msg) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(msg));
  return Array.from(new Uint8Array(sig), b => b.toString(16).padStart(2, "0")).join("");
}

// constant-time hex compare
function safeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

// ---------- Cloudflare Access JWT verification ------------------------------

let JWKS_CACHE = null;        // { team, keys: { [kid]: CryptoKey }, expiresAt }

async function loadJWKS(team) {
  if (JWKS_CACHE && JWKS_CACHE.team === team && JWKS_CACHE.expiresAt > Date.now()) return JWKS_CACHE.keys;
  const r = await fetch(`https://${team}/cdn-cgi/access/certs`);
  if (!r.ok) throw new Error("jwks fetch failed");
  const data = await r.json();
  const keys = {};
  for (const k of data.keys || []) {
    try {
      keys[k.kid] = await crypto.subtle.importKey(
        "jwk", k, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]
      );
    } catch {}
  }
  JWKS_CACHE = { team, keys, expiresAt: Date.now() + 60 * 60 * 1000 };
  return keys;
}

function b64urlDecode(s) {
  s = s.replace(/-/g, "+").replace(/_/g, "/");
  while (s.length % 4) s += "=";
  return Uint8Array.from(atob(s), c => c.charCodeAt(0));
}

async function verifyAccessJWT(jwt, env) {
  if (!env.CF_ACCESS_TEAM || !env.CF_ACCESS_AUD) return null;
  const parts = String(jwt || "").split(".");
  if (parts.length !== 3) return null;
  let header, payload;
  try {
    header  = JSON.parse(new TextDecoder().decode(b64urlDecode(parts[0])));
    payload = JSON.parse(new TextDecoder().decode(b64urlDecode(parts[1])));
  } catch { return null; }
  const keys = await loadJWKS(env.CF_ACCESS_TEAM);
  const key = keys[header.kid];
  if (!key) return null;
  const sig = b64urlDecode(parts[2]);
  const signedData = new TextEncoder().encode(parts[0] + "." + parts[1]);
  const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, sig, signedData);
  if (!ok) return null;
  if (payload.exp && payload.exp * 1000 < Date.now()) return null;
  const audOk = Array.isArray(payload.aud)
    ? payload.aud.includes(env.CF_ACCESS_AUD)
    : payload.aud === env.CF_ACCESS_AUD;
  if (!audOk) return null;
  const issOk = String(payload.iss || "").includes(env.CF_ACCESS_TEAM);
  if (!issOk) return null;
  return payload;
}

async function requireAdmin(request, env) {
  // Prod path: Cloudflare Access JWT
  if (env.CF_ACCESS_TEAM && env.CF_ACCESS_AUD) {
    const jwt = request.headers.get("Cf-Access-Jwt-Assertion")
            || (request.headers.get("Cookie") || "").match(/CF_Authorization=([^;]+)/)?.[1];
    const claims = await verifyAccessJWT(jwt, env);
    if (!claims) return { ok: false, status: 401, msg: "Cloudflare Access required" };
    return { ok: true, email: claims.email || "" };
  }
  // Dev fallback: shared bearer token
  if (env.ADMIN_TOKEN) {
    const got = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
    if (got && safeEqual(got, env.ADMIN_TOKEN)) return { ok: true, email: "dev-admin" };
    return { ok: false, status: 401, msg: "Bearer token required" };
  }
  return { ok: false, status: 503, msg: "admin not configured (set CF_ACCESS_TEAM+AUD or ADMIN_TOKEN)" };
}

// ---------- public: chat ----------------------------------------------------

function brainContext() {
  const c = brain.company || {};
  const machines = (brain.machines || [])
    .map(m => `- ${m.tonnage}-ton ${m.brand} ${m.model}: ${m.year}, ${m.shot_size} shot, ${m.controller} control, ${m.hours} hrs, ${m.condition}. ${m.summary}`)
    .join("\n");
  const faqs = (brain.faqs || []).map(f => `Q: ${f.q}\nA: ${f.a}`).join("\n");
  return `You are the assistant for ${c.name}, ${c.city} ${c.region} — a dealer of used injection molding machines. ` +
    `Be concise, friendly, and accurate. Only use the inventory and facts below. If asked about a machine not listed, say it's not currently in stock and offer a callback. ` +
    `Always offer to have ${c.owner_name || "Nicole"} call the buyer back and ask for their name and phone.\n\nINVENTORY:\n${machines}\n\nFAQS:\n${faqs}`;
}

// ---------- public: lead ----------------------------------------------------

function subjectFor(type, name, phone) {
  const who = name || "anonymous";
  if (type === "seller")  return `New SELL inquiry: ${who} ${phone}`;
  if (type === "contact") return `New website message: ${who} ${phone}`;
  if (type === "quote")   return `New quote request: ${who} ${phone}`;
  return `New callback lead: ${who} ${phone}`;
}
function leadEmailBody(lead) {
  const lines = [
    `Type: ${lead.type || "buyer"}`,
    `Name: ${lead.name || ""}`,
    `Company: ${lead.company || ""}`,
    `Phone: ${lead.phone || ""}`,
    `Email: ${lead.email || ""}`,
  ];
  if (lead.type === "seller") {
    lines.push(`Machine: ${[lead.machine_year, lead.machine_tonnage && lead.machine_tonnage + "-ton", lead.machine_brand, lead.machine_model].filter(Boolean).join(" ")}`);
  } else if (lead.machine) {
    lines.push(`Machine of interest: ${lead.machine}`);
  }
  lines.push(`Message: ${lead.note || lead.message || ""}`);
  if (lead.source) lines.push(`Source: ${lead.source}`);
  return lines.join("\n");
}

// ---------- admin: clients --------------------------------------------------

async function listClients(env) {
  if (!env.DB) return [];
  const r = await env.DB.prepare(
    "SELECT id, company, contact, email, phone, city, region, created FROM clients ORDER BY company ASC"
  ).all();
  return r.results || [];
}
async function createClient(env, body) {
  const id = newClientId();
  const c = {
    id,
    company: trim(body.company, 200),
    contact: trim(body.contact, 160),
    email:   trim(body.email, 160),
    phone:   trim(body.phone, 40),
    city:    trim(body.city, 80),
    region:  trim(body.region, 8),
    notes:   trim(body.notes, 1000),
    created: now(), updated: now(),
  };
  if (!c.company) throw new Error("company required");
  await env.DB.prepare(
    "INSERT INTO clients (id,company,contact,email,phone,city,region,notes,created,updated) VALUES (?,?,?,?,?,?,?,?,?,?)"
  ).bind(c.id, c.company, c.contact, c.email, c.phone, c.city, c.region, c.notes, c.created, c.updated).run();
  return c;
}
async function getClient(env, id) {
  const c = await env.DB.prepare("SELECT * FROM clients WHERE id = ?").bind(id).first();
  if (!c) return null;
  const docs = await env.DB.prepare(
    "SELECT id,kind,number,title,amount_cents,status,created FROM documents WHERE client_id = ? ORDER BY created DESC"
  ).bind(id).all();
  return { ...c, documents: docs.results || [] };
}
async function updateClient(env, id, body) {
  const fields = ["company","contact","email","phone","city","region","notes"];
  const updates = [], values = [];
  for (const f of fields) if (f in body) { updates.push(`${f} = ?`); values.push(trim(body[f], 1000)); }
  if (!updates.length) return await env.DB.prepare("SELECT * FROM clients WHERE id = ?").bind(id).first();
  updates.push("updated = ?"); values.push(now());
  values.push(id);
  await env.DB.prepare(`UPDATE clients SET ${updates.join(", ")} WHERE id = ?`).bind(...values).run();
  return await env.DB.prepare("SELECT * FROM clients WHERE id = ?").bind(id).first();
}
async function deleteClient(env, id) {
  const has = await env.DB.prepare("SELECT COUNT(*) AS n FROM documents WHERE client_id = ?").bind(id).first();
  if ((has?.n || 0) > 0) throw new Error("client has documents; delete those first");
  await env.DB.prepare("DELETE FROM clients WHERE id = ?").bind(id).run();
}

// ---------- admin: documents ------------------------------------------------

async function nextDocNumber(env, kind) {
  const prefix = kind === "po" ? "PO" : kind === "bol" ? "BOL" : "Q";
  const year = new Date().getUTCFullYear();
  const r = await env.DB.prepare(
    "SELECT COUNT(*) AS n FROM documents WHERE kind = ? AND created LIKE ?"
  ).bind(kind, `${year}-%`).first();
  const seq = String(((r?.n || 0) + 1)).padStart(4, "0");
  return `${prefix}-${year}-${seq}`;
}

async function uploadDocument(env, body, request) {
  // body fields: client_id, kind, title, amount_cents, payload (any JSON), pdf_b64 (PDF bytes base64)
  const clientId = trim(body.client_id, 32);
  const kind     = trim(body.kind, 8); // 'quote' | 'po' | 'bol'
  if (!clientId || !["quote","po","bol"].includes(kind)) throw new Error("client_id and valid kind required");
  const client = await env.DB.prepare("SELECT id, company FROM clients WHERE id = ?").bind(clientId).first();
  if (!client) throw new Error("client not found");
  if (!body.pdf_b64) throw new Error("pdf_b64 required");

  const id     = newDocId();
  const number = trim(body.number, 32) || await nextDocNumber(env, kind);
  const title  = trim(body.title, 240);
  const amount = body.amount_cents != null ? Math.round(Number(body.amount_cents)) : null;
  const r2_key = `clients/${clientId}/${kind}s/${id}.pdf`;
  const secret = randHex(16);

  // Base64 → bytes
  const raw = atob(String(body.pdf_b64).replace(/\s/g, ""));
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  await env.FILES.put(r2_key, bytes, {
    httpMetadata: { contentType: "application/pdf", contentDisposition: `inline; filename="${number}.pdf"` },
  });

  const payload = body.payload ? JSON.stringify(body.payload).slice(0, 64 * 1024) : null;
  await env.DB.prepare(
    `INSERT INTO documents (id,client_id,kind,number,title,amount_cents,status,r2_key,share_secret,payload,created,updated)
     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`
  ).bind(id, clientId, kind, number, title, amount, "open", r2_key, secret, payload, now(), now()).run();

  const share_url_path = await buildShareURL(env, id, secret);
  const origin = request ? new URL(request.url).origin : "";
  const share_url_abs = origin + share_url_path;

  // Automation: ping Nicole / Missy on every new document so she has a copy + audit trail
  if (env.NOTIFY_EMAIL) {
    const kindLabel = kind === "po" ? "Purchase Order" : kind === "bol" ? "Bill of Lading" : "Quote";
    const amtLabel  = amount != null ? ` · $${(amount/100).toLocaleString(undefined,{minimumFractionDigits:2})}` : "";
    try {
      await fetch("https://api.mailchannels.net/tx/v1/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          personalizations: [{ to: [{ email: env.NOTIFY_EMAIL }] }],
          from: { email: "leads@buypremier.com", name: "Premier CRM" },
          subject: `${kindLabel} ${number} sent to ${client.company}${amtLabel}`,
          content: [{ type: "text/plain", value:
            `${kindLabel} ${number} created.\n` +
            `Client : ${client.company}\n` +
            `Title  : ${title}\n` +
            (amount != null ? `Amount : $${(amount/100).toLocaleString(undefined,{minimumFractionDigits:2})}\n` : "") +
            `Share  : ${share_url_abs}\n`
          }],
        }),
      });
    } catch {}
  }

  return { id, client_id: clientId, kind, number, title, amount_cents: amount, status: "open", r2_key, share_url: share_url_path, created: now() };
}

async function buildShareURL(env, docId, secret, base = "") {
  const sig = (await hmacHex(env.SHARE_SECRET + ":" + secret, docId)).slice(0, 32);
  return `${base}/files/${docId}.${sig}`;
}

async function listDocuments(env, filters) {
  let sql = "SELECT id,client_id,kind,number,title,amount_cents,status,created FROM documents";
  const where = [], vals = [];
  if (filters.client_id) { where.push("client_id = ?"); vals.push(filters.client_id); }
  if (filters.kind)      { where.push("kind = ?"); vals.push(filters.kind); }
  if (where.length) sql += " WHERE " + where.join(" AND ");
  sql += " ORDER BY created DESC LIMIT 200";
  const r = await env.DB.prepare(sql).bind(...vals).all();
  return r.results || [];
}
async function getDocument(env, id) {
  const d = await env.DB.prepare("SELECT * FROM documents WHERE id = ?").bind(id).first();
  if (!d) return null;
  d.share_url = await buildShareURL(env, d.id, d.share_secret);
  d.payload   = d.payload ? safeParse(d.payload) : null;
  delete d.share_secret;
  return d;
}
function safeParse(s) { try { return JSON.parse(s); } catch { return null; } }

async function updateDocument(env, id, body) {
  const allowed = ["status","title","amount_cents","number"];
  const updates = [], values = [];
  for (const f of allowed) if (f in body) { updates.push(`${f} = ?`); values.push(body[f]); }
  if (!updates.length) return await getDocument(env, id);
  updates.push("updated = ?"); values.push(now()); values.push(id);
  await env.DB.prepare(`UPDATE documents SET ${updates.join(", ")} WHERE id = ?`).bind(...values).run();
  return await getDocument(env, id);
}
async function rotateDocumentSecret(env, id) {
  const secret = randHex(16);
  await env.DB.prepare("UPDATE documents SET share_secret = ?, updated = ? WHERE id = ?")
    .bind(secret, now(), id).run();
  return { id, share_url: await buildShareURL(env, id, secret) };
}
async function deleteDocument(env, id) {
  const d = await env.DB.prepare("SELECT r2_key FROM documents WHERE id = ?").bind(id).first();
  if (!d) return;
  try { await env.FILES.delete(d.r2_key); } catch {}
  await env.DB.prepare("DELETE FROM documents WHERE id = ?").bind(id).run();
}

// ---------- voice receptionist (Retell webhooks) ----------------------------
//
// Each tool below is invoked by Retell as a "custom function" during a call.
// Auth: Retell sends a custom header you configure in their dashboard. We expect
// `Authorization: Bearer <RETELL_WEBHOOK_SECRET>` and reject any other request.

function requireVoiceAuth(request, env) {
  if (!env.RETELL_WEBHOOK_SECRET) return { ok: false, status: 503, msg: "voice not configured (set RETELL_WEBHOOK_SECRET)" };
  const got = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  return safeEqual(got, env.RETELL_WEBHOOK_SECRET) ? { ok: true } : { ok: false, status: 401, msg: "bad voice token" };
}

async function voiceLookupMachine(env, args) {
  const q = String(args?.query || "").toLowerCase();
  const tonMatch = q.match(/(\d{2,4})\s*-?\s*ton/);
  const tonNum = tonMatch ? +tonMatch[1] : null;
  const machines = (brain.machines || []).map(m => {
    let s = 0;
    if (tonNum != null && Math.abs(m.tonnage - tonNum) <= 50) s += 3;
    if (q.includes(m.brand.toLowerCase())) s += 3;
    if (q.includes(m.model.toLowerCase())) s += 2;
    return { m, s };
  }).filter(x => x.s > 0).sort((a, b) => b.s - a.s).slice(0, 3).map(x => x.m);
  return {
    found: machines.length,
    machines: machines.map(m => ({
      brand: m.brand, model: m.model, tonnage: m.tonnage, year: m.year,
      shot_size: m.shot_size, controller: m.controller, hours: m.hours,
      condition: m.condition, summary: m.summary,
    })),
    fallback_message: machines.length
      ? null
      : "Not currently in stock — I can have Nicole check with our network and call back.",
  };
}

async function voiceBookCall(env, args, callInfo) {
  const b = {
    id: newBookingId(),
    name:    trim(args?.name, 120),
    phone:   trim(args?.phone, 40),
    email:   trim(args?.email, 160),
    company: trim(args?.company, 160),
    topic:   trim(args?.topic, 400),
    when_iso: trim(args?.when_iso || args?.when || "", 80),
    status:  "open",
    source:  "voice",
    call_id: trim(callInfo?.call_id, 120),
    created: now(),
  };
  if (env.DB) {
    try {
      await env.DB.prepare(
        "INSERT INTO bookings (id,name,phone,email,company,topic,when_iso,status,source,call_id,created) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
      ).bind(b.id, b.name, b.phone, b.email, b.company, b.topic, b.when_iso, b.status, b.source, b.call_id, b.created).run();
    } catch {}
  }
  if (env.NOTIFY_EMAIL) {
    try {
      await fetch("https://api.mailchannels.net/tx/v1/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          personalizations: [{ to: [{ email: env.NOTIFY_EMAIL }] }],
          from: { email: "leads@buypremier.com", name: "Premier Receptionist" },
          subject: `Callback booked: ${b.name || b.phone || "caller"} — ${b.when_iso || "asap"}`,
          content: [{ type: "text/plain", value:
            `Name   : ${b.name}\nPhone  : ${b.phone}\nEmail  : ${b.email}\nCompany: ${b.company}\nTopic  : ${b.topic}\nWhen   : ${b.when_iso}\nCall id: ${b.call_id}` }],
        }),
      });
    } catch {}
  }
  return { booked: true, booking_id: b.id, confirmation: `OK — Nicole will call ${b.name || "you"} at ${b.phone} ${b.when_iso ? `around ${b.when_iso}` : "as soon as she can"}.` };
}

async function voiceCreateLead(env, args, callInfo) {
  const lead = {
    type:    trim(args?.type || "buyer", 16),
    name:    trim(args?.name, 120),
    company: trim(args?.company, 160),
    phone:   trim(args?.phone, 40),
    email:   trim(args?.email, 160),
    machine: trim(args?.machine, 200),
    machine_brand: trim(args?.machine_brand, 80),
    machine_model: trim(args?.machine_model, 80),
    machine_tonnage: trim(args?.machine_tonnage, 24),
    machine_year:   trim(args?.machine_year, 8),
    note:    trim(args?.note, 1000),
    source:  `voice:${callInfo?.call_id || "unknown"}`,
    created: now(),
  };
  if (env.DB) {
    try {
      await env.DB.prepare(
        `INSERT INTO leads (type,name,company,phone,email,machine,machine_brand,machine_model,machine_tonnage,machine_year,note,source,created)
         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)`
      ).bind(lead.type, lead.name, lead.company, lead.phone, lead.email, lead.machine,
             lead.machine_brand, lead.machine_model, lead.machine_tonnage, lead.machine_year,
             lead.note, lead.source, lead.created).run();
    } catch {}
  }
  return { ok: true };
}

async function voicePostCall(env, payload) {
  // Retell post-call webhook: stores transcript + summary + outcome
  const cr = {
    id: newCallRecId(),
    call_id:     trim(payload?.call_id || payload?.call?.call_id, 120),
    from_number: trim(payload?.from_number || payload?.call?.from_number, 40),
    to_number:   trim(payload?.to_number   || payload?.call?.to_number, 40),
    started:     trim(payload?.start_timestamp || payload?.call?.start_timestamp, 64),
    ended:       trim(payload?.end_timestamp   || payload?.call?.end_timestamp, 64),
    duration_sec: Number(payload?.duration_ms || payload?.call?.duration_ms || 0) / 1000 | 0,
    transcript:  trim(payload?.transcript || payload?.call?.transcript, 32 * 1024),
    summary:     trim(payload?.call_analysis?.call_summary || payload?.summary, 4000),
    outcome:     trim(payload?.call_analysis?.user_sentiment || "other", 32),
    metadata:    JSON.stringify(payload).slice(0, 32 * 1024),
    created:     now(),
  };
  if (!cr.call_id) return { ok: false, error: "missing call_id" };
  if (env.DB) {
    try {
      // upsert by call_id
      await env.DB.prepare("DELETE FROM call_records WHERE call_id = ?").bind(cr.call_id).run();
      await env.DB.prepare(
        `INSERT INTO call_records (id,call_id,from_number,to_number,started,ended,duration_sec,transcript,summary,outcome,metadata,created)
         VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`
      ).bind(cr.id, cr.call_id, cr.from_number, cr.to_number, cr.started, cr.ended, cr.duration_sec, cr.transcript, cr.summary, cr.outcome, cr.metadata, cr.created).run();
    } catch {}
  }
  return { ok: true };
}

async function listBookings(env, limit = 50) {
  if (!env.DB) return [];
  const r = await env.DB.prepare("SELECT * FROM bookings ORDER BY created DESC LIMIT ?").bind(limit).all();
  return r.results || [];
}
async function updateBookingStatus(env, id, status) {
  await env.DB.prepare("UPDATE bookings SET status = ? WHERE id = ?").bind(status, id).run();
  return await env.DB.prepare("SELECT * FROM bookings WHERE id = ?").bind(id).first();
}
async function listCallRecords(env, limit = 50) {
  if (!env.DB) return [];
  const r = await env.DB.prepare(
    "SELECT id,call_id,from_number,started,duration_sec,summary,outcome,created FROM call_records ORDER BY started DESC LIMIT ?"
  ).bind(limit).all();
  return r.results || [];
}

// ---------- customer upload portal ------------------------------------------
//
// Per-client upload links: token = "<client_id>.<hmac>" where hmac is
// HMAC(SHARE_SECRET + ":" + client.upload_secret, "upload:" + client_id).
// Client.upload_secret is a per-client 16-byte hex. Rotate it to revoke a link.

async function generateUploadLink(env, request, clientId) {
  const c = await env.DB.prepare("SELECT id, company, upload_secret FROM clients WHERE id = ?").bind(clientId).first();
  if (!c) throw new Error("client not found");
  let secret = c.upload_secret;
  if (!secret) {
    secret = randHex(16);
    await env.DB.prepare("UPDATE clients SET upload_secret = ?, updated = ? WHERE id = ?").bind(secret, now(), clientId).run();
  }
  const sig = (await hmacHex(env.SHARE_SECRET + ":" + secret, "upload:" + clientId)).slice(0, 32);
  const token = `${clientId}.${sig}`;
  const origin = request ? new URL(request.url).origin : "";
  // The public upload page is served by Pages at /upload.html; it submits to the Worker route below.
  return {
    token,
    upload_url: `${origin}/api/upload/${token}`,
    share_url:  `${origin}/upload.html?t=${token}&co=${encodeURIComponent(c.company || "")}`,
  };
}

async function rotateUploadSecret(env, request, clientId) {
  const secret = randHex(16);
  await env.DB.prepare("UPDATE clients SET upload_secret = ?, updated = ? WHERE id = ?").bind(secret, now(), clientId).run();
  return await generateUploadLink(env, request, clientId);
}

async function validateUploadToken(env, token) {
  const m = String(token || "").match(/^(c_[0-9a-f]+)\.([0-9a-f]+)$/i);
  if (!m) return null;
  const clientId = m[1], sig = m[2];
  const c = await env.DB.prepare("SELECT id, company, upload_secret FROM clients WHERE id = ?").bind(clientId).first();
  if (!c || !c.upload_secret) return null;
  const expected = (await hmacHex(env.SHARE_SECRET + ":" + c.upload_secret, "upload:" + clientId)).slice(0, 32);
  if (!safeEqual(sig, expected)) return null;
  return c;
}

async function receiveCustomerUpload(env, request, token) {
  const client = await validateUploadToken(env, token);
  if (!client) return err("invalid upload token", 404);
  const form = await request.formData().catch(() => null);
  if (!form) return err("expected multipart/form-data", 400);

  const uploader_name  = trim(form.get("name") || "", 120);
  const uploader_email = trim(form.get("email") || "", 160);
  const uploader_phone = trim(form.get("phone") || "", 40);
  const note           = trim(form.get("note") || "", 1000);
  const files          = form.getAll("files").filter(f => f && typeof f === "object" && f.size != null);
  if (!files.length)             return err("no files attached", 400);
  if (files.length > MAX_UPLOAD_FILES) return err(`too many files (max ${MAX_UPLOAD_FILES})`, 400);

  const saved = [];
  for (const f of files) {
    if (f.size > MAX_UPLOAD_BYTES) return err(`"${f.name}" exceeds the ${(MAX_UPLOAD_BYTES/1024/1024).toFixed(0)} MB per-file limit`, 413);
    const id      = newUploadId();
    const ts      = Date.now();
    const r2_key  = `clients/${client.id}/uploads/${ts}-${safeFilename(f.name)}`;
    const bytes   = new Uint8Array(await f.arrayBuffer());
    await env.FILES.put(r2_key, bytes, {
      httpMetadata: { contentType: f.type || "application/octet-stream" },
    });
    await env.DB.prepare(
      `INSERT INTO client_uploads (id,client_id,uploader_name,uploader_email,uploader_phone,filename,r2_key,size_bytes,content_type,note,created)
       VALUES (?,?,?,?,?,?,?,?,?,?,?)`
    ).bind(id, client.id, uploader_name, uploader_email, uploader_phone, f.name, r2_key, f.size, f.type, note, now()).run();
    saved.push({ id, filename: f.name, size_bytes: f.size, content_type: f.type, r2_key });
  }

  if (env.NOTIFY_EMAIL) {
    try {
      await fetch("https://api.mailchannels.net/tx/v1/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          personalizations: [{ to: [{ email: env.NOTIFY_EMAIL }] }],
          from: { email: "leads@buypremier.com", name: "Premier Uploads" },
          subject: `New upload (${saved.length} file${saved.length>1?"s":""}) from ${client.company}`,
          content: [{ type: "text/plain", value:
            `Client: ${client.company} (${client.id})\n` +
            `From:   ${uploader_name || "(no name)"} ${uploader_phone || ""} ${uploader_email || ""}\n` +
            (note ? `Note:   ${note}\n` : "") +
            "\nFiles:\n" + saved.map(s => `- ${s.filename} (${(s.size_bytes/1024).toFixed(0)} KB)`).join("\n") +
            "\n\nReview at /admin/uploads.html"
          }],
        }),
      });
    } catch {}
  }
  return json({ ok: true, count: saved.length, files: saved });
}

async function listUploads(env, filters = {}, limit = 200) {
  if (!env.DB) return [];
  let sql = `SELECT u.*, c.company FROM client_uploads u LEFT JOIN clients c ON c.id = u.client_id`;
  const where = [], vals = [];
  if (filters.client_id) { where.push("u.client_id = ?"); vals.push(filters.client_id); }
  if (where.length) sql += " WHERE " + where.join(" AND ");
  sql += " ORDER BY u.created DESC LIMIT ?";
  vals.push(limit);
  const r = await env.DB.prepare(sql).bind(...vals).all();
  return r.results || [];
}

async function serveUploadedFile(env, uploadId) {
  // Admin-only download, authenticated by the same admin auth as other /api/admin routes.
  const u = await env.DB.prepare("SELECT r2_key, filename, content_type FROM client_uploads WHERE id = ?").bind(uploadId).first();
  if (!u) return err("not found", 404);
  const obj = await env.FILES.get(u.r2_key);
  if (!obj) return err("file missing", 404);
  return new Response(obj.body, {
    headers: {
      "Content-Type": u.content_type || "application/octet-stream",
      "Content-Disposition": `attachment; filename="${u.filename}"`,
    },
  });
}

// ---------- dashboard + Claude morning briefing -----------------------------

async function dashboardSnapshot(env) {
  if (!env.DB) return null;
  const sinceIso = (days) => new Date(Date.now() - days * 86_400_000).toISOString();

  // KPIs
  const pipe = await env.DB.prepare(
    "SELECT COUNT(*) AS n, COALESCE(SUM(amount_cents),0) AS cents FROM documents WHERE kind='quote' AND status IN ('open','sent')"
  ).first();
  const aged = await env.DB.prepare(
    "SELECT COUNT(*) AS n FROM documents WHERE kind='quote' AND status IN ('open','sent') AND created < ?"
  ).bind(sinceIso(14)).first();
  const leads7 = await env.DB.prepare("SELECT COUNT(*) AS n FROM leads WHERE created >= ?").bind(sinceIso(7)).first();
  const docs7  = await env.DB.prepare("SELECT COUNT(*) AS n FROM documents WHERE created >= ?").bind(sinceIso(7)).first();
  const won30  = await env.DB.prepare(
    "SELECT COUNT(*) AS n, COALESCE(SUM(amount_cents),0) AS cents FROM documents WHERE kind='quote' AND status='accepted' AND updated >= ?"
  ).bind(sinceIso(30)).first();

  // Aged opportunities (open/sent quotes > 7 days old, sorted by age)
  const agedList = (await env.DB.prepare(
    `SELECT d.id, d.number, d.title, d.amount_cents, d.status, d.created, c.company
       FROM documents d JOIN clients c ON c.id = d.client_id
       WHERE d.kind='quote' AND d.status IN ('open','sent') AND d.created < ?
       ORDER BY d.created ASC LIMIT 20`
  ).bind(sinceIso(7)).all()).results || [];

  // Recent leads
  const recentLeads = (await env.DB.prepare(
    "SELECT id,type,name,company,phone,email,machine,machine_brand,machine_model,machine_tonnage,machine_year,note,created FROM leads WHERE created >= ? ORDER BY created DESC LIMIT 20"
  ).bind(sinceIso(7)).all()).results || [];

  // Recent documents (any kind, any status, last 14 days) with company
  const recentDocs = (await env.DB.prepare(
    `SELECT d.id, d.kind, d.number, d.title, d.amount_cents, d.status, d.created, c.company
       FROM documents d JOIN clients c ON c.id = d.client_id
       WHERE d.created >= ? ORDER BY d.created DESC LIMIT 20`
  ).bind(sinceIso(14)).all()).results || [];

  // Open voice bookings (callbacks the receptionist scheduled)
  const openBookings = (await env.DB.prepare(
    "SELECT id,name,phone,company,topic,when_iso,created FROM bookings WHERE status = 'open' ORDER BY created DESC LIMIT 20"
  ).all()).results || [];

  // Recent customer uploads
  const recentUploads = (await env.DB.prepare(
    `SELECT u.id,u.filename,u.size_bytes,u.created,c.company FROM client_uploads u
       LEFT JOIN clients c ON c.id = u.client_id
       WHERE u.created >= ? ORDER BY u.created DESC LIMIT 20`
  ).bind(sinceIso(7)).all()).results || [];

  return {
    kpis: {
      pipeline_open_cents: pipe?.cents || 0,
      open_quotes:        pipe?.n || 0,
      aged_count:         aged?.n || 0,
      leads_7d:           leads7?.n || 0,
      docs_7d:            docs7?.n || 0,
      accepted_30d_count: won30?.n || 0,
      accepted_30d_cents: won30?.cents || 0,
      open_bookings:      openBookings.length,
      uploads_7d:         recentUploads.length,
    },
    aged_opportunities: agedList.map(d => ({ ...d, age_days: ageDays(d.created) })),
    recent_leads: recentLeads,
    recent_documents: recentDocs,
    open_bookings: openBookings,
    recent_uploads: recentUploads,
  };
}

async function getBriefingForDate(env, date) {
  if (!env.DB) return null;
  return await env.DB.prepare("SELECT * FROM briefings WHERE date = ?").bind(date).first();
}

function moneyCents(c) { return "$" + ((c || 0) / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }

function buildBriefingPrompt(snapshot, today) {
  const k = snapshot.kpis;
  const lines = [];
  lines.push(`Date: ${today}`);
  lines.push("");
  lines.push("KPIs:");
  lines.push(`- Open quote pipeline: ${moneyCents(k.pipeline_open_cents)} across ${k.open_quotes} quotes`);
  lines.push(`- Aged quotes (>14d, still open/sent): ${k.aged_count}`);
  lines.push(`- New leads last 7d: ${k.leads_7d}`);
  lines.push(`- Documents created last 7d: ${k.docs_7d}`);
  lines.push(`- Accepted quotes last 30d: ${k.accepted_30d_count} (${moneyCents(k.accepted_30d_cents)})`);
  lines.push("");
  lines.push("AGED / OPEN QUOTES (sorted oldest first):");
  if (!snapshot.aged_opportunities.length) lines.push("- (none)");
  snapshot.aged_opportunities.forEach(d => {
    lines.push(`- ${d.number} ${d.company} — ${moneyCents(d.amount_cents)} · ${d.status} · ${d.age_days}d old · "${(d.title||'').slice(0,80)}"`);
  });
  lines.push("");
  lines.push("RECENT LEADS (last 7d):");
  if (!snapshot.recent_leads.length) lines.push("- (none)");
  snapshot.recent_leads.forEach(l => {
    const machine = l.type === "seller"
      ? `selling ${[l.machine_year, l.machine_tonnage && l.machine_tonnage + "-ton", l.machine_brand, l.machine_model].filter(Boolean).join(" ")}`
      : (l.machine ? `wants ${l.machine}` : "");
    lines.push(`- [${l.type}] ${l.name || "?"} @ ${l.company || "?"} (${l.phone || l.email || "no contact"}) ${machine} — note: "${(l.note||'').slice(0,120)}"`);
  });
  lines.push("");
  lines.push("RECENT DOCUMENTS (last 14d):");
  if (!snapshot.recent_documents.length) lines.push("- (none)");
  snapshot.recent_documents.forEach(d => {
    lines.push(`- ${d.number} (${d.kind}) ${d.company} — ${moneyCents(d.amount_cents)} · ${d.status}`);
  });
  lines.push("");
  lines.push("OPEN VOICE BOOKINGS (callbacks Nicole still owes):");
  if (!snapshot.open_bookings || !snapshot.open_bookings.length) lines.push("- (none)");
  (snapshot.open_bookings || []).forEach(b => {
    lines.push(`- ${b.name || "(no name)"} ${b.phone || ""} @ ${b.company || ""} — ${b.topic || ""} · when: ${b.when_iso || "asap"}`);
  });
  lines.push("");
  lines.push("RECENT UPLOADS (customer files dropped, last 7d):");
  if (!snapshot.recent_uploads || !snapshot.recent_uploads.length) lines.push("- (none)");
  (snapshot.recent_uploads || []).forEach(u => {
    lines.push(`- ${u.company || "(unknown client)"} uploaded ${u.filename}`);
  });
  return lines.join("\n");
}

const BRIEFING_SYSTEM = `You are the morning briefer for Nicole Haas, owner of Premier Equipment LLC — a Beachwood, OH dealer of used injection molding machines (https://buypremier.com). Premier buys AND sells inspected used machines.

Your output is a SHORT, action-oriented daily briefing Nicole reads with her morning coffee. Format STRICTLY:

Line 1: a single-sentence summary, no markdown, max 140 chars.
Line 2: blank.
Lines 3+: 3 to 6 bullets starting with "- ". Each bullet starts with an action verb (Call, Follow up, Quote, Reach out, Send, Close, Triage, Re-engage), names a specific company and dollar amount when relevant, and explains *why* this matters today.

Rules:
- Be concrete. If a quote is aged, name the company and amount and say "stale".
- Prioritize: aged quotes > new leads > general housekeeping.
- Never invent facts. Only use the data provided.
- No greetings, no preamble, no signoff. Output exactly the format above.
- If the data is empty (slow day), say so and suggest 2-3 outbound prospecting actions specific to plastics machinery.`;

async function callClaude(env, prompt) {
  // Prefer Anthropic API if a key is configured; fall back to Workers AI llama
  if (env.ANTHROPIC_API_KEY) {
    const model = env.ANTHROPIC_MODEL || "claude-sonnet-4-6";
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": env.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model,
        max_tokens: 700,
        system: BRIEFING_SYSTEM,
        messages: [{ role: "user", content: prompt }],
      }),
    });
    if (!r.ok) throw new Error("anthropic error: " + r.status + " " + (await r.text()).slice(0, 300));
    const j = await r.json();
    const text = (j.content && j.content[0] && j.content[0].text) || "";
    return { text, model };
  }
  if (env.AI) {
    const res = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
      messages: [
        { role: "system", content: BRIEFING_SYSTEM },
        { role: "user", content: prompt },
      ],
    });
    return { text: (res && res.response) || "", model: "workers-ai-llama-3.1-8b" };
  }
  throw new Error("no LLM available (set ANTHROPIC_API_KEY or bind AI)");
}

async function generateBriefing(env, { force = false } = {}) {
  if (!env.DB) throw new Error("DB not bound");
  const date = todayUtc();
  if (!force) {
    const existing = await getBriefingForDate(env, date);
    if (existing) return existing;
  }
  const snapshot = await dashboardSnapshot(env);
  const prompt   = buildBriefingPrompt(snapshot, date);
  const { text, model } = await callClaude(env, prompt);

  const summary = text.split(/\r?\n/).map(s => s.trim()).find(s => s.length > 0) || "(no briefing)";
  const body_md = text.trim();
  const id      = newBriefingId();
  const generated_at = now();

  // upsert (one row per day)
  await env.DB.prepare(
    "DELETE FROM briefings WHERE date = ?"
  ).bind(date).run();
  await env.DB.prepare(
    "INSERT INTO briefings (id,date,generated_at,model,data,body_md,summary) VALUES (?,?,?,?,?,?,?)"
  ).bind(id, date, generated_at, model, JSON.stringify(snapshot).slice(0, 64*1024), body_md, summary).run();

  // Email Nicole
  if (env.NOTIFY_EMAIL) {
    try {
      await fetch("https://api.mailchannels.net/tx/v1/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          personalizations: [{ to: [{ email: env.NOTIFY_EMAIL }] }],
          from: { email: "leads@buypremier.com", name: "Premier Morning Briefing" },
          subject: `Premier briefing · ${date} · ${summary.slice(0, 80)}`,
          content: [{ type: "text/plain", value: body_md + "\n\n— Generated by " + model + " at " + generated_at }],
        }),
      });
    } catch {}
  }

  return { id, date, generated_at, model, body_md, summary };
}

async function listBriefings(env, limit = 30) {
  if (!env.DB) return [];
  const r = await env.DB.prepare(
    "SELECT id,date,generated_at,model,summary FROM briefings ORDER BY date DESC LIMIT ?"
  ).bind(limit).all();
  return r.results || [];
}

// ---------- /files/:token : public download with HMAC -----------------------

async function serveSharedFile(env, token) {
  const m = String(token || "").match(/^(d_[0-9a-f]+)\.([0-9a-f]+)$/i);
  if (!m) return err("invalid token", 404);
  const docId = m[1], sig = m[2];
  const d = await env.DB.prepare("SELECT r2_key, share_secret, number, kind FROM documents WHERE id = ?")
    .bind(docId).first();
  if (!d) return err("not found", 404);
  const expected = (await hmacHex(env.SHARE_SECRET + ":" + d.share_secret, docId)).slice(0, 32);
  if (!safeEqual(sig, expected)) return err("invalid token", 404);
  const obj = await env.FILES.get(d.r2_key);
  if (!obj) return err("file missing", 404);
  return new Response(obj.body, {
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": `inline; filename="${d.number || d.kind}.pdf"`,
      "Cache-Control": "private, max-age=300",
    },
  });
}

// ---------- router ----------------------------------------------------------

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
    const url = new URL(request.url);
    const p = url.pathname;
    const method = request.method;

    try {
      // ---- public ----
      if (p === "/api/chat" && method === "POST") {
        const { message } = await request.json();
        if (!env.AI) return json({ reply: "" });
        const res = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
          messages: [
            { role: "system", content: brainContext() },
            { role: "user", content: String(message || "").slice(0, 500) },
          ],
        });
        return json({ reply: (res && res.response) || "" });
      }

      if (p === "/api/lead" && method === "POST") {
        const raw = await request.json().catch(() => ({}));
        const lead = {
          type: trim(raw.type || "buyer", 16),
          name: trim(raw.name, 120), company: trim(raw.company, 160),
          phone: trim(raw.phone, 40), email: trim(raw.email, 160),
          machine: trim(raw.machine, 200),
          machine_brand: trim(raw.machine_brand, 80), machine_model: trim(raw.machine_model, 80),
          machine_tonnage: trim(raw.machine_tonnage, 24), machine_year: trim(raw.machine_year, 8),
          note: trim(raw.note || raw.message, 1000),
          source: trim(raw.source || request.headers.get("referer") || "", 240),
          created: now(),
        };
        if (env.DB) {
          try {
            await env.DB.prepare(
              `INSERT INTO leads (type,name,company,phone,email,machine,machine_brand,machine_model,machine_tonnage,machine_year,note,source,created)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)`
            ).bind(lead.type, lead.name, lead.company, lead.phone, lead.email, lead.machine,
                   lead.machine_brand, lead.machine_model, lead.machine_tonnage, lead.machine_year,
                   lead.note, lead.source, lead.created).run();
          } catch {}
        }
        if (env.NOTIFY_EMAIL) {
          try {
            await fetch("https://api.mailchannels.net/tx/v1/send", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                personalizations: [{ to: [{ email: env.NOTIFY_EMAIL }] }],
                from: { email: "leads@buypremier.com", name: "Premier Website" },
                subject: subjectFor(lead.type, lead.name, lead.phone),
                content: [{ type: "text/plain", value: leadEmailBody(lead) }],
              }),
            });
          } catch {}
        }
        return json({ ok: true });
      }

      // /files/:token  — share link, no auth, HMAC-validated
      const fileMatch = p.match(/^\/files\/(.+)$/);
      if (fileMatch && method === "GET") return await serveSharedFile(env, fileMatch[1]);

      // /api/upload/:token — public customer upload, no auth (HMAC-validated)
      const upMatch = p.match(/^\/api\/upload\/(.+)$/);
      if (upMatch && method === "POST") return await receiveCustomerUpload(env, request, upMatch[1]);

      // ---- voice receptionist (Retell webhooks) ----
      if (p.startsWith("/api/voice/")) {
        const auth = requireVoiceAuth(request, env);
        if (!auth.ok) return err(auth.msg, auth.status);
        const body = await request.json().catch(() => ({}));
        const args = body.args || body.parameters || body;
        const call = body.call || { call_id: body.call_id };

        if (p === "/api/voice/lookup_machine") return json(await voiceLookupMachine(env, args));
        if (p === "/api/voice/book_call")      return json(await voiceBookCall(env, args, call));
        if (p === "/api/voice/create_lead")    return json(await voiceCreateLead(env, args, call));
        if (p === "/api/voice/post_call")      return json(await voicePostCall(env, body));
        return err("voice route not found", 404);
      }

      // ---- admin (gated) ----
      if (p.startsWith("/api/admin")) {
        const auth = await requireAdmin(request, env);
        if (!auth.ok) return err(auth.msg, auth.status);

        if (p === "/api/admin/me")       return json({ ok: true, email: auth.email });

        // Clients
        if (p === "/api/admin/clients" && method === "GET")  return json({ clients: await listClients(env) });
        if (p === "/api/admin/clients" && method === "POST") return json({ client: await createClient(env, await request.json()) }, 201);

        const cm = p.match(/^\/api\/admin\/clients\/([^\/]+)$/);
        if (cm) {
          const id = cm[1];
          if (method === "GET")    { const c = await getClient(env, id); return c ? json({ client: c }) : err("not found", 404); }
          if (method === "PUT")    return json({ client: await updateClient(env, id, await request.json()) });
          if (method === "DELETE") { await deleteClient(env, id); return json({ ok: true }); }
        }

        // Documents
        if (p === "/api/admin/documents" && method === "GET") {
          const filters = { client_id: url.searchParams.get("client_id"), kind: url.searchParams.get("kind") };
          return json({ documents: await listDocuments(env, filters) });
        }
        if (p === "/api/admin/documents" && method === "POST") {
          const doc = await uploadDocument(env, await request.json(), request);
          return json({ document: doc }, 201);
        }

        const dm = p.match(/^\/api\/admin\/documents\/([^\/]+)(\/rotate)?$/);
        if (dm) {
          const id = dm[1], rotate = !!dm[2];
          if (rotate && method === "POST") return json(await rotateDocumentSecret(env, id));
          if (method === "GET")    { const d = await getDocument(env, id); return d ? json({ document: d }) : err("not found", 404); }
          if (method === "PUT")    return json({ document: await updateDocument(env, id, await request.json()) });
          if (method === "DELETE") { await deleteDocument(env, id); return json({ ok: true }); }
        }

        // Dashboard + briefings
        if (p === "/api/admin/dashboard" && method === "GET") {
          const snapshot = await dashboardSnapshot(env);
          const briefing = await getBriefingForDate(env, todayUtc());
          return json({
            snapshot,
            briefing: briefing ? {
              id: briefing.id, date: briefing.date, generated_at: briefing.generated_at,
              model: briefing.model, body_md: briefing.body_md, summary: briefing.summary,
            } : null,
          });
        }
        if (p === "/api/admin/briefings" && method === "GET") {
          return json({ briefings: await listBriefings(env) });
        }
        if (p === "/api/admin/briefing/run" && method === "POST") {
          const b = await generateBriefing(env, { force: true });
          return json({ briefing: b });
        }

        // Bookings (voice receptionist calls)
        if (p === "/api/admin/bookings" && method === "GET")  return json({ bookings: await listBookings(env) });
        const bkMatch = p.match(/^\/api\/admin\/bookings\/([^\/]+)$/);
        if (bkMatch && method === "PUT") {
          const body = await request.json();
          return json({ booking: await updateBookingStatus(env, bkMatch[1], trim(body.status, 16)) });
        }

        // Call transcripts
        if (p === "/api/admin/calls" && method === "GET") return json({ calls: await listCallRecords(env) });
        const callDetail = p.match(/^\/api\/admin\/calls\/([^\/]+)$/);
        if (callDetail && method === "GET") {
          const c = await env.DB.prepare("SELECT * FROM call_records WHERE id = ?").bind(callDetail[1]).first();
          return c ? json({ call: c }) : err("not found", 404);
        }

        // Upload links + admin views of customer uploads
        const ulink = p.match(/^\/api\/admin\/clients\/([^\/]+)\/upload-link$/);
        if (ulink && method === "POST")   return json(await generateUploadLink(env, request, ulink[1]));
        if (ulink && method === "DELETE") return json(await rotateUploadSecret(env, request, ulink[1]));

        if (p === "/api/admin/uploads" && method === "GET") {
          const filters = { client_id: url.searchParams.get("client_id") };
          return json({ uploads: await listUploads(env, filters) });
        }
        const upFile = p.match(/^\/api\/admin\/uploads\/([^\/]+)\/file$/);
        if (upFile && method === "GET") return await serveUploadedFile(env, upFile[1]);
      }

      // health / fallthrough
      if (p === "/" || p === "/api/health") return json({ ok: true, service: "Premier Equipment Worker" });
      return err("not found", 404);
    } catch (e) {
      return err(String(e.message || e), 500);
    }
  },

  /**
   * Cron-triggered. Schedule lives in wrangler.toml under [triggers] crons.
   * Generates today's briefing (idempotent — if a briefing for today already exists, skips).
   */
  async scheduled(event, env, ctx) {
    ctx.waitUntil((async () => {
      try {
        await generateBriefing(env, { force: false });
      } catch (e) {
        // Best-effort: log to Workers Analytics by re-throwing? We just swallow to avoid retries that double-send emails.
        console.error("scheduled briefing failed:", e && e.message || e);
      }
    })());
  },
};

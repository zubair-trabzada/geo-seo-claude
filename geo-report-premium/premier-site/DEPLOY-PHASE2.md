# Premier Equipment — Phase 2 (AI chat, leads, quotes, newsletter, CRM)

Phase 2 turns the site into a real working tool: public AI chat + lead capture, plus a gated CRM where Nicole manages clients and ships quotes / POs / BOLs from her phone. Everything is built — the parts below describe the one-time setup.

## The full build command (run in order)
```
python run.py                  # build everything (same as 4 manual steps below)
# or:
python build.py        # generate the static site from inventory.json
python make_brain.py   # build the Nicole Brain (brain.json) from inventory
python add_widget.py   # inject the AI chat widget into every public page
python content.py      # newsletter + blog post + social drafts
```
Then deploy:
```
python run.py --all            # build + deploy Pages + deploy Worker
# or piecemeal:
npx wrangler pages deploy site --project-name=premier-equipment
cd worker && npx wrangler deploy
```

## What works the moment you deploy the static site (no Worker needed)
- **AI chat widget** on every page. Out of the box it answers from the brain (inventory + FAQs) entirely in the browser and captures callback leads.
- **Public Quick Quote** at `/quote.html` — phone-friendly, builds a branded quote PDF client-side.
- **Newsletter + social** — `content.py` writes `marketing/newsletter-DATE.html` and `marketing/social-DATE.md`, plus a blog post under `site/blog/`.

## Turn on LIVE AI + stored leads — the Worker (~10 min)
1. From the `worker/` folder:
   ```
   cd worker
   npx wrangler d1 create premier-leads
   ```
   Copy the `database_id` it prints into `wrangler.toml`.

2. **Create the R2 bucket** for quote / PO / BOL PDFs and customer uploads:
   ```
   npx wrangler r2 bucket create premier-files
   ```

3. **Create the tables** (one D1 schema covers leads + CRM):
   ```
   npx wrangler d1 execute premier-leads --file=schema.sql
   ```
   *(If you already deployed an earlier schema, see the `ALTER TABLE` block at the bottom of `schema.sql`.)*

4. **Set worker secrets**:
   ```
   npx wrangler secret put SHARE_SECRET     # paste any 32-char random — signs /files/:token links
   npx wrangler secret put ADMIN_TOKEN      # dev-only fallback bearer; skip once CF Access is up
   ```

5. **Set the notify email** in `wrangler.toml` (`NOTIFY_EMAIL`) — every lead and every new quote/PO/BOL pings this address.

6. **Deploy**:
   ```
   npx wrangler deploy
   ```
   It prints a URL like `https://premier-equipment.<you>.workers.dev`. Test it:
   ```
   curl https://premier-equipment.<you>.workers.dev/api/health
   ```

7. **Wire the public chat to the Worker**: open `add_widget.py`, set
   ```python
   API = "https://premier-equipment.<you>.workers.dev"
   ```
   then re-run `python add_widget.py && npx wrangler pages deploy site --project-name=premier-equipment`.

Now the chat uses real AI (free Workers AI) and every public lead is saved to D1 + emailed.

## Turn on the CRM — Cloudflare Access (production auth)
The `/admin/*` pages and `/api/admin/*` endpoints are designed to live behind Cloudflare Access. This gives Nicole SSO (email / Google) and the Worker enforces the JWT on every request.

1. **Add a custom Worker route on the Pages domain** so the Worker is reachable at `buypremier.com/api/*` and `buypremier.com/files/*`:
   - Cloudflare dashboard → Workers & Pages → `premier-equipment` → **Settings → Triggers**
   - Add two routes (your zone):
     - `buypremier.com/api/*`
     - `buypremier.com/files/*`
   - Putting the Worker on the same hostname as the Pages site means CF Access cookies are sent automatically.

2. **Create a Cloudflare Access Application** for the admin:
   - Zero Trust dashboard → **Access → Applications → Add an application → Self-hosted**
   - Application domain: `buypremier.com/admin*` (and add `buypremier.com/api/admin*` as an additional include path)
   - Identity providers: enable **Google** and/or **One-Time PIN** (email)
   - Policy: `Include → Emails → nicole@buypremier.com, missy@finemarkgroup.com`
   - Session duration: 24 hours (recommended)
   - **Copy the Application Audience (AUD) tag** from the overview screen.

3. **Tell the Worker about Access** — update `worker/wrangler.toml`:
   ```toml
   [vars]
   CF_ACCESS_TEAM = "yourteam.cloudflareaccess.com"
   CF_ACCESS_AUD  = "<the AUD tag you copied>"
   ```
   then `npx wrangler deploy` again.

Now hitting `https://buypremier.com/admin/` redirects through CF Access, and the Worker verifies the JWT (RS256, JWKS) on every admin call. If the JWT is missing or invalid → 401.

**Dev mode (skip CF Access):** leave `CF_ACCESS_TEAM` blank and the Worker accepts `Authorization: Bearer <ADMIN_TOKEN>` instead. Go to `/admin/login.html`, paste the token; it's saved in your browser only.

## Morning Claude briefing (the cron Worker)

Every morning, the Worker generates a "today's priorities" briefing tailored to your actual pipeline, stores it in D1, and emails you. The dashboard pulls today's briefing on load.

1. **Set the Anthropic API key** for Claude-quality briefings (recommended). Get one at https://console.anthropic.com.
   ```
   npx wrangler secret put ANTHROPIC_API_KEY
   ```
   If you skip this, the Worker falls back to free Workers AI (llama-3.1-8b) — works, but the prose is rougher.

2. **The cron is already configured** in `wrangler.toml`:
   ```toml
   [triggers]
   crons = ["0 11 * * *"]   # 11:00 UTC = 7am EDT / 6am EST
   ```
   Adjust the cron string (https://crontab.guru/) and re-deploy. Cloudflare always runs crons in UTC.

3. **Test it manually** before tomorrow morning:
   ```
   curl -X POST -H "Authorization: Bearer <ADMIN_TOKEN>" \
     https://premier-equipment.<you>.workers.dev/api/admin/briefing/run
   ```
   You should see JSON with `body_md` populated, and an email should arrive at `NOTIFY_EMAIL`.

4. **Optional model override** — set `ANTHROPIC_MODEL = "claude-sonnet-4-6"` (or any current model id) in `wrangler.toml` `[vars]`. Defaults to `claude-sonnet-4-6`.

The dashboard at `/admin/` shows today's briefing at the top, a KPI strip (open pipeline $, # quotes, aged > 14d, leads this week), an aged-opportunities list, and a unified activity feed of leads + documents. Tap **Regenerate** on the briefing card to re-run it on demand.

## AI receptionist (Retell voice agent)

The Worker exposes four endpoints under `/api/voice/*` that the [Retell](https://www.retellai.com) agent invokes during a call. Nicole's main number forwards to Retell's number, the agent talks to the caller, calls Premier inventory live, books a callback, captures leads, and ships a transcript afterwards.

1. **Create a Retell account** at https://retellai.com → buy a phone number.
2. **Configure the agent** with the system prompt in [retell/agent-prompt.md](retell/agent-prompt.md). The voice, tempo, and rules are tuned for plastics-machinery buyers/sellers.
3. **Add four custom functions** in Retell (one-by-one):
   - Copy each entry from [retell/functions.json](retell/functions.json) — name, URL, method, parameters.
   - URL: `https://buypremier.com/api/voice/<name>` (or your `*.workers.dev` URL during dev).
   - Each function gets a custom HTTP header `Authorization: Bearer <RETELL_WEBHOOK_SECRET>`.
4. **Configure Retell's post-call webhook** → URL `https://buypremier.com/api/voice/post_call`, same Authorization header. Transcripts and summaries land in the `call_records` table; the dashboard's morning briefing surfaces open callbacks.
5. **Set the Worker secret**:
   ```
   npx wrangler secret put RETELL_WEBHOOK_SECRET
   ```
   Pick something random; paste the same value into all four Retell function headers.
6. **Forward Premier's main line** to the Retell number during after-hours (start with 6pm–8:30am + weekends, expand once you trust it).

Test from the admin: the **Calls** tab shows the bookings + transcripts as they arrive. Mark callbacks "done" when handled.

## Customer document-upload portal

A texting-friendly intake: Nicole copies a per-client upload link from the CRM and texts it to a buyer or seller. The customer opens it, drops photos / PDFs / tag plate / W-9, hits send. Files land in R2 under `clients/{client_id}/uploads/{ts}-{filename}`, the database logs every upload, and Nicole gets an email.

1. **No new secrets needed** — uses the existing `SHARE_SECRET`.
2. **Generate a link**: in `/admin/clients.html?id=<client>`, tap **Upload link** → tap **Share / Text** to fire your phone's share sheet, or **Copy link**.
3. **Customer experience**: opens `buypremier.com/upload.html?t=<token>&co=<company>`, sees their company name confirmed, picks multiple files (drag-drop on desktop, native picker on phone), submits. Success screen lists what they sent.
4. **Limits**: 12 files per upload, 20 MB per file (enforced both client-side and Worker-side).
5. **Review** in `/admin/uploads.html` — tap any row to download.
6. **Revoke a link**: in the same client's detail screen, tap **Rotate (revoke)** under the upload link. All previously sent links die immediately.

## Using the CRM
- **`/admin/`** — dashboard with recent activity and quick-add buttons
- **`/admin/clients.html`** — add and manage clients (companies you sell to or buy from)
- **`/admin/quote.html`** — phone-friendly quote builder. Pick a client, tap any inventory chip to auto-add a line item, set price, tap **Generate & Send** → branded PDF generates client-side → uploads to R2 under `clients/{id}/quotes/{docId}.pdf` → server returns a permanent HMAC-signed share URL → your phone's native share sheet opens so you can text or email it. Nicole gets a copy in her inbox automatically.
- **`/admin/po.html`** and **`/admin/bol.html`** — same flow for purchase orders and bills of lading. POs file under the vendor, BOLs under the consignee.
- **Share links never expire by clock** but every doc has its own `share_secret`. Tap **Rotate link** on the doc to invalidate the old URL.

Recent activity at the Worker level:
```
npx wrangler d1 execute premier-leads --command="SELECT id,kind,number,title,amount_cents,created FROM documents ORDER BY created DESC LIMIT 20"
```

## Make the newsletter send itself (optional)
- Free email tools: MailerLite or Brevo (free to ~1,000 contacts). Paste the generated newsletter HTML, or connect via their API.
- To auto-run weekly, add a Cloudflare Cron Trigger (or a Windows Task Scheduler job) that runs `python run.py --deploy`.

## File map
```
premier-site/
  inventory.json         <- single source of truth (edit here or via admin.html)
  admin.html             <- phone-friendly add/remove machines
  build.py               <- generates the static site
  make_brain.py          <- builds the AI brain from inventory
  add_widget.py          <- injects the chat widget (set API here to go live)
  content.py             <- newsletter + blog + social drafts
  run.py                 <- one-command build + deploy orchestrator
  static/                <- hand-written pages copied verbatim into site/
    quote.html           <- public quick quote (jsPDF)
    admin/               <- the gated CRM (CF Access)
      login.html, index.html, clients.html, quote.html, po.html, bol.html
      _shared.css, _shared.js
  site/                  <- the published website (deploy this folder)
    assets/chat.js, brain.json
    blog/                <- weekly posts
  worker/                <- Cloudflare Worker
    index.js, wrangler.toml, schema.sql, brain.json
  marketing/             <- newsletter + social drafts (not published)
  .claude/launch.json    <- dev server configs (static :8000, worker :8787)
```

*Built for Premier Equipment by La Crown Inc. — be the human in the equation.*

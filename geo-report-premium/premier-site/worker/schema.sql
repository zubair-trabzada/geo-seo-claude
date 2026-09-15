-- Premier Equipment D1 schema.
-- Apply on a fresh DB:  wrangler d1 execute premier-leads --file=schema.sql
-- Existing DBs: run only the ALTER TABLE block at the bottom.

-- ===== Website leads (chat widget + sell/contact forms) =====
CREATE TABLE IF NOT EXISTS leads (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  type      TEXT,        -- 'buyer' | 'seller' | 'contact' | 'chat' | 'quote'
  name      TEXT,
  company   TEXT,
  phone     TEXT,
  email     TEXT,
  machine   TEXT,
  machine_brand    TEXT,
  machine_model    TEXT,
  machine_tonnage  TEXT,
  machine_year     TEXT,
  note      TEXT,
  source    TEXT,
  created   TEXT
);

-- ===== CRM: clients (companies Nicole is selling to or buying from) =====
CREATE TABLE IF NOT EXISTS clients (
  id          TEXT PRIMARY KEY,         -- 'c_' + 12 hex (generated in Worker)
  company     TEXT NOT NULL,
  contact     TEXT,                     -- primary contact name
  email       TEXT,
  phone       TEXT,
  city        TEXT,
  region      TEXT,                     -- state abbreviation
  notes       TEXT,
  upload_secret TEXT,                   -- per-client HMAC secret for /upload/:token links (null until generated)
  created     TEXT,
  updated     TEXT
);

CREATE INDEX IF NOT EXISTS idx_clients_company ON clients(company);

-- ===== CRM: documents (quotes, POs, BOLs) =====
CREATE TABLE IF NOT EXISTS documents (
  id            TEXT PRIMARY KEY,        -- 'd_' + 12 hex
  client_id     TEXT NOT NULL,
  kind          TEXT NOT NULL,           -- 'quote' | 'po' | 'bol'
  number        TEXT,                    -- 'Q-2026-0007', 'PO-2026-0042', 'BOL-2026-0019'
  title         TEXT,                    -- summary line for lists ('500-Ton Milacron Magna 500')
  amount_cents  INTEGER,                 -- total (cents) — for quotes/POs; 0 or NULL for BOLs
  status        TEXT DEFAULT 'open',     -- 'open' | 'sent' | 'accepted' | 'declined' | 'void'
  r2_key        TEXT NOT NULL,           -- 'clients/{client_id}/{kind}s/{id}.pdf'
  share_secret  TEXT NOT NULL,           -- random 16-byte hex; HMAC key for /files/:token
  payload       TEXT,                    -- JSON snapshot of the form (line items, terms, etc.) for regeneration
  created       TEXT,
  updated       TEXT,
  FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE INDEX IF NOT EXISTS idx_documents_client_kind ON documents(client_id, kind);
CREATE INDEX IF NOT EXISTS idx_documents_created    ON documents(created DESC);

-- ===== Daily Claude briefings (morning "what to do today") =====
CREATE TABLE IF NOT EXISTS briefings (
  id           TEXT PRIMARY KEY,         -- 'b_' + 12 hex
  date         TEXT NOT NULL,            -- YYYY-MM-DD (UTC), one row per day
  generated_at TEXT NOT NULL,
  model        TEXT,                     -- 'claude-sonnet-4-6' | 'workers-ai-llama-3.1-8b'
  data         TEXT,                     -- JSON snapshot of the dashboard inputs
  body_md      TEXT,                     -- markdown briefing body
  summary      TEXT                      -- one-line summary for email subject + UI
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_briefings_date ON briefings(date);

-- ===== Voice receptionist (Retell) =====
-- Each row = one callback that the AI receptionist booked with Nicole.
CREATE TABLE IF NOT EXISTS bookings (
  id         TEXT PRIMARY KEY,         -- 'bk_' + 12 hex
  name       TEXT,
  phone      TEXT,
  email      TEXT,
  company    TEXT,
  topic      TEXT,                     -- "wants a 300-ton, mid-2010s"
  when_iso   TEXT,                     -- requested call time (free text from caller, ISO if parsed)
  status     TEXT DEFAULT 'open',      -- 'open' | 'done' | 'no-show'
  source     TEXT DEFAULT 'voice',     -- 'voice' | 'web' | 'manual'
  call_id    TEXT,                     -- Retell call id, if any
  created    TEXT
);

-- Each row = one call handled by the receptionist (post-call transcripts).
CREATE TABLE IF NOT EXISTS call_records (
  id            TEXT PRIMARY KEY,      -- our id, 'cr_' + 12 hex
  call_id       TEXT UNIQUE,           -- Retell's call_id
  from_number   TEXT,
  to_number     TEXT,
  started       TEXT,
  ended         TEXT,
  duration_sec  INTEGER,
  transcript    TEXT,
  summary       TEXT,
  outcome       TEXT,                  -- 'lead'|'booking'|'info_only'|'spam'|'other'
  metadata      TEXT,                  -- raw Retell payload (JSON, trimmed)
  created       TEXT
);
CREATE INDEX IF NOT EXISTS idx_call_records_started ON call_records(started DESC);

-- ===== Customer file uploads (R2 inbox per client) =====
CREATE TABLE IF NOT EXISTS client_uploads (
  id         TEXT PRIMARY KEY,         -- 'up_' + 12 hex
  client_id  TEXT,                     -- nullable: open intake supported later
  uploader_name  TEXT,
  uploader_email TEXT,
  uploader_phone TEXT,
  filename   TEXT,
  r2_key     TEXT,                     -- 'clients/{client_id}/uploads/{ts}-{safe_name}'
  size_bytes INTEGER,
  content_type TEXT,
  note       TEXT,
  created    TEXT
);
CREATE INDEX IF NOT EXISTS idx_uploads_client  ON client_uploads(client_id);
CREATE INDEX IF NOT EXISTS idx_uploads_created ON client_uploads(created DESC);

-- Clients gain an upload_secret column for revocable per-client upload links.
-- ALTER on existing DBs:
-- ALTER TABLE clients ADD COLUMN upload_secret TEXT;

-- ============================================================
-- If you already deployed the previous schema, run these once:
-- ============================================================
-- ALTER TABLE leads ADD COLUMN type TEXT;
-- ALTER TABLE leads ADD COLUMN company TEXT;
-- ALTER TABLE leads ADD COLUMN email TEXT;
-- ALTER TABLE leads ADD COLUMN machine_brand TEXT;
-- ALTER TABLE leads ADD COLUMN machine_model TEXT;
-- ALTER TABLE leads ADD COLUMN machine_tonnage TEXT;
-- ALTER TABLE leads ADD COLUMN machine_year TEXT;
-- ALTER TABLE leads ADD COLUMN source TEXT;
-- (the CRM tables above use CREATE TABLE IF NOT EXISTS — safe to re-run.)

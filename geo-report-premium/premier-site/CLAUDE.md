# CLAUDE.md — Premier Equipment AI Site

Context for Claude Code working in this repo. Read this first.

## What this is
A solo-run, low-overhead website + lead system for **Premier Equipment LLC** (Beachwood, OH) — a dealer of used injection molding machines. Built by La Crown Inc. (Millisa Nwokolo). **No Replit.** Static site generated from one data file, hosted free on **Cloudflare Pages**, with a Cloudflare **Worker** for live AI + lead storage.

Design principle: **one source of truth.** `inventory.json` feeds the website, the AI chat brain, the newsletter, and the social drafts. Edit it once → everything updates.

## Stack
- Site generator: **Python 3** (`build.py`) → static HTML in `site/`
- Hosting: **Cloudflare Pages** (free), deployed with `wrangler`
- Backend: **Cloudflare Worker** (`worker/`) — Workers AI for chat, D1 for leads, MailChannels for email
- Front-end chat: vanilla JS (`site/assets/chat.js`), works client-side, upgrades to the Worker when `PREMIER_API` is set
- Quote tool: client-side jsPDF (`site/quote.html`)
- No frameworks, no build tooling beyond Python + wrangler.

## Commands (RUN IN THIS ORDER)
```
python build.py        # 1. generate the site from inventory.json (wipes & rebuilds site/)
python make_brain.py   # 2. build brain.json (AI knowledge) into site/assets/ and worker/
python add_widget.py   # 3. inject the chat widget into every site/*.html
python content.py      # 4. newsletter + blog post + social drafts
wrangler pages deploy site --project-name=premier-equipment   # 5. publish
```
**Important:** `build.py` clears `site/` each run, so always run all four steps in order. Run `content.py` last (its blog post lives in `site/blog/`).

## Data model — `inventory.json`
- `company`: name, city, region, postal, phone, phone_e164, email, url, entity_line
- `machines[]`: id, brand, model, tonnage(int), year(int), shot_size, controller, hours(int), condition, price ("request"), summary, status ("available"|"sold")
- `faqs[]`: q, a

Only `status:"available"` machines are published. Machine page URL slug = `{tonnage}-ton-{brand}-{model}` (lowercased, hyphenated).

## File map
| File | Role |
|---|---|
| `inventory.json` | single source of truth |
| `build.py` | static-site generator (index, inventory, machine/*, faq, sitemap, robots, llms.txt) |
| `make_brain.py` | writes `brain.json` from inventory |
| `add_widget.py` | injects chat widget; **set `API` here to the Worker URL to go live** |
| `content.py` | newsletter (`marketing/`), blog post (`site/blog/`), social (`marketing/`) |
| `admin.html` | phone-friendly add/remove machines → exports `inventory.json` |
| `site/` | the published website (deploy this folder) |
| `site/quote.html` | mobile quote → branded PDF (jsPDF), client-side |
| `site/assets/chat.js`, `brain.json` | AI chat widget + brain |
| `worker/` | Cloudflare Worker: `/api/chat` (Workers AI), `/api/lead` (D1 + email) |
| `DEPLOY.md`, `DEPLOY-PHASE2.md` | deploy steps |

## Conventions
- **Brand colors:** teal `#1B8A7A` / dark `#0C2A2A` / orange accent `#F26A21` / light bg `#F6F9F9`. Logo `premier-logo.svg` is white-wordmark → only place it on dark backgrounds (header/footer).
- **SEO/GEO rules (do not regress):** every page has JSON-LD; machines use `Product` + `UsedCondition` + `additionalProperty` specs; **price is always "request a quote", never a number** (a prior audit failure was tonnage injected as price). Keep `llms.txt`, `sitemap.xml`, clean keyword URLs, FAQPage + ItemList schema, Open Graph tags.
- Fonts: Plus Jakarta Sans (body) + Fraunces (display).
- Keep everything dependency-light and free-tier.

## Gotchas
- Run the 4 build steps in order every time (build wipes `site/`).
- The chat widget answers locally until you set `API` in `add_widget.py` to the deployed Worker URL, then re-run steps 3–5.
- jsPDF is loaded from cdnjs; the quote tool needs internet to generate PDFs.
- Worker needs a D1 `database_id` pasted into `worker/wrangler.toml` before `wrangler deploy`.

## Prerequisites
- Python 3.9+
- Node.js + `npm install -g wrangler` (for deploy + Worker)
- A free Cloudflare account

## Backlog / next tasks (phase 3 ideas)
- Persist blog posts across rebuilds (move posts to a `posts/` source folder build.py renders).
- Auto-run the weekly build via Cloudflare Cron or Windows Task Scheduler.
- Real machine photos via Cloudflare R2 (referenced from `inventory.json`).
- Wire the Retell voice agent to the same `brain.json` so phone + web AI match.
- "Add a Machine" web form (Worker + D1) so no spreadsheet step.
- Optional CRM sync for captured leads.

## Voice / brand
Premier's site = professional, trustworthy, machinery-buyer focused. La Crown tagline for internal/footer touches: "Be the human in the equation."

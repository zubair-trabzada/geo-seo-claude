# Premier Equipment — AI Website & Lead System

A complete, solo-run site for a used injection molding machine dealer. Built with Claude Code + Cloudflare (free). One inventory file powers the website, the AI chat, the newsletter, and social posts.

## Start working on it with Claude Code
1. Open a terminal in this `premier-site` folder.
2. Run `claude` to start Claude Code (it auto-reads `CLAUDE.md` for full context).
3. Try a first prompt, for example:
   - *"Read CLAUDE.md, run the full build pipeline, and tell me if anything errors."*
   - *"Add a 250-ton Nissei to inventory.json and rebuild."*
   - *"Walk me through deploying this to Cloudflare Pages."*

## Run it yourself (4 steps + deploy)
```
python build.py        # generate the site
python make_brain.py   # build the AI brain
python add_widget.py   # add the chat widget to every page
python content.py      # newsletter + blog post + social drafts
wrangler pages deploy site --project-name=premier-equipment
```
Full details in **CLAUDE.md**, **DEPLOY.md**, and **DEPLOY-PHASE2.md**.

## What you get
- **Marketing site** — homepage, inventory, a page per machine, FAQ — all SEO + GEO optimized (schema, llms.txt, clean URLs, price-on-request).
- **AI chat ("Nicole Brain")** on every page — answers spec questions and captures callback leads.
- **/quote** — build and text a branded quote PDF from your phone (`site/quote.html`).
- **admin.html** — add/remove machines from your phone, no code.
- **Newsletter + social** — generated weekly from inventory.
- **Cloudflare Worker** — optional live AI + saved leads + email alerts.

## Prerequisites
Python 3.9+, Node.js with `wrangler` (`npm install -g wrangler`), and a free Cloudflare account.

## Daily loop (you or Nicole)
Open `admin.html` → add/remove machines → download `inventory.json` (replace the old one) → run the 4 build steps → deploy. Done.

*Built by La Crown Inc. — be the human in the equation.*

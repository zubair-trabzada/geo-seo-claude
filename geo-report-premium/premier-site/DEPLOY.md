# Premier Equipment Site — How To Run & Deploy

This is the whole system. No Replit. Free hosting on Cloudflare.

## What's in this folder
- `inventory.json` — the single source of truth (machines, company info, FAQs)
- `build.py` — turns the inventory into the full website
- `admin.html` — phone-friendly manager to add/remove machines
- `site/` — the generated website (this is what gets published)
- `premier-logo.svg` — the logo (kept in the folder above this one)

## The daily loop (the easy part — Nicole or you)
1. Open **admin.html** in any browser (works on your phone).
2. Click **Load your current list** and pick `inventory.json`.
3. Add or remove machines, then **Download inventory.json**.
4. Replace the old `inventory.json` in this folder with the new one.
5. Run the rebuild + publish (one line, below).

## Build + publish (one time to set up, then one line each update)

**First-time setup (10 minutes):**
1. Make a free account at https://dash.cloudflare.com
2. Install the deploy tool (one time):
   ```
   npm install -g wrangler
   wrangler login
   ```
3. From inside this `premier-site` folder, build and publish:
   ```
   python build.py
   wrangler pages deploy site --project-name=premier-equipment
   ```
   Cloudflare gives you a live URL instantly (e.g. premier-equipment.pages.dev).

**Every update after that — just two lines:**
```
python build.py
wrangler pages deploy site --project-name=premier-equipment
```

## Point buypremier.com at it
In the Cloudflare dashboard → your Pages project → **Custom domains** → add `buypremier.com`.
Cloudflare handles HTTPS and the http→https redirect automatically (one of the audit fixes, free).

## What's already handled for SEO + GEO
- Clean keyword URLs (`/machine/300-ton-van-dorn-300-rs.html`)
- Organization + LocalBusiness schema (name, address, phone, social)
- Product schema per machine — used condition + full specs + **price-on-request** (no fake price)
- ItemList on the inventory page, FAQPage on the FAQ page
- `llms.txt` with the disambiguating entity line (fixes the name-collision)
- `sitemap.xml`, `robots.txt` welcoming AI crawlers, Open Graph tags

## Coming next (phase 2)
- AI chat widget wired to the "Nicole Brain" + callback lead capture (Cloudflare Worker + D1)
- Weekly inventory newsletter + auto blog post (Cloudflare Cron)
- `/quote` mobile tool to build and text branded quotes
- "Add a Machine" form that writes straight to the site (no spreadsheet step)

*Built for Premier Equipment by La Crown Inc.*

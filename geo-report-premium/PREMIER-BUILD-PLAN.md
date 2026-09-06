# Premier Equipment — Solo Build Plan
### No Replit. Claude Code + Cloudflare (free). SEO + GEO built in.

The whole point: **one source of truth (your inventory), one free stack, zero monthly overhead.** You add a machine once and it shows up on the site, in the newsletter, and in the AI's answers. That's the solo-run model.

---

## 1. The stack (and why)

| Layer | Tool | Cost | Why |
|---|---|---|---|
| Build | **Claude Code**, on your computer | free | You already have it. No Replit, no lock-in. |
| Site | **Static HTML** generated from your inventory data | free | Fast + fully readable by Google AND AI crawlers = the GEO win the audit wanted. |
| Hosting | **Cloudflare Pages** | free | Global, instant HTTPS, auto http→https redirect (fixes an audit issue). |
| Database | **Cloudflare D1** (built-in SQLite) | free | Holds inventory + leads. No server to babysit. |
| Photos | **Cloudflare R2** | free to 10GB | Machine pictures. |
| Smart bits | **Cloudflare Workers** (+ Workers AI) | free tier | Powers the AI Q&A and lead capture. |

**Replacing Lead to Conversion:** they charge **$750–$3,500/mo** on 90-day contracts — and your audit still came back 40/100. This stack runs at roughly **$0–$20/mo**. That's the overhead you're trying to kill.

---

## 2. The one thing everything is built on: your inventory file

Everything below feeds off a single list of machines. Start as a simple file (`inventory.json`) or a Google Sheet you edit from your phone. Each machine has:

`id · brand · model · tonnage · year · shot_size · controller · hours · condition · price (or "request") · photos · one-line summary · status (available/sold)`

The site, the newsletter, and the AI all read from this **one list**. Update it once → everything updates. That's the magic of low overhead.

---

## 3. Your four features — how each gets built

### Feature 1 — Automated machine uploads
- **Tonight version:** you add a row to the Google Sheet (or a line in `inventory.json`). One command in Claude Code rebuilds the site and deploys it. New machine is live in ~30 seconds.
- **Next-week version:** a phone-friendly "Add a Machine" form. You snap photos, type the tonnage/specs, hit save — a Worker writes it to D1 and the site rebuilds itself. No spreadsheet needed.

### Feature 2 — Weekly inventory newsletter + post on the site
- A scheduled job (Cloudflare Cron, runs itself weekly) reads the inventory, pulls the new/featured machines, and:
  1. publishes a blog post to the site (great for SEO — fresh content the audit said you were missing), and
  2. emails your list via a free tool (MailerLite or Brevo, free up to ~1,000 contacts).
- Claude writes the copy each week. You approve and it sends.

### Feature 3 — The "Nicole Brain" + AI questions + callback leads
- The **brain** = your inventory + FAQs + policies, kept as structured data. It's literally the machine list plus answers to common questions.
- A chat widget on the site (the one already working in your demo) and your **Retell voice agent** both read from this same brain — so the website AI and the phone AI always agree.
- When someone asks about a machine and shows interest, it captures their name + number, drops it in your leads table, and texts/emails you and Nicole for a **callback**. Lead never gets lost.

### Feature 4 — Quote/Proposal PDF tool (build quotes from your phone)
- A private page on the site (`/quote`, behind a passphrase) with a short form.
- Fill it on your phone → it generates a **branded quote/proposal PDF** → you share it by text or email on the spot.
- This is your "quick quote from anywhere" tool — no laptop, no overhead.

---

## 4. SEO + GEO — baked in from day one (fixes your audit)

Because the site is static HTML built from data, we get these almost for free:

- **Clean keyword URLs** — e.g. `/inventory/300-ton-van-dorn-injection-molding-machine`
- **JSON-LD schema on every page:** Organization + LocalBusiness (real name, address, phone, social links), a Product block per machine with **brand, used-condition, and a full spec list** — and **price shown as "request a quote," never tonnage-as-price** (that was your #1 critical)
- **ItemList** on the inventory page so AI can read your whole catalog
- **FAQPage** schema on real buyer FAQs (replaces the demo-FAQ problem)
- **llms.txt** at the root with the disambiguating line: *"Premier Equipment LLC, Beachwood OH — used injection molding machines"* (fixes the name-collision problem)
- **sitemap.xml** (https, fresh dates), **robots.txt** welcoming AI crawlers, Open Graph tags, fast Core Web Vitals
- Cloudflare gives free HTTPS + the http→https redirect automatically

Net effect: the same site that wins buyers also scores high on the next GEO audit — which becomes your proof for the next client.

---

## 5. The all-nighter order (do it in this sequence)

**Tonight — the visible site (80% of the wow):**
1. Create the project folder + push to Cloudflare Pages → blank site is live on a Cloudflare URL.
2. Point buypremier.com (or a staging subdomain) at it.
3. Drop in the homepage we already built + generate the inventory/Product pages from your machine list.
4. Add the schema, llms.txt, sitemap, robots, OG tags (the GEO fixes).

You'll have a real, live, AI-readable site by morning.

**This week — the automation (the moat):**
5. Wire the AI chat widget to the brain + lead capture (Worker + D1).
6. Build the `/quote` mobile tool.
7. Turn on the weekly newsletter job.
8. Add the phone "Add a Machine" form.

---

## 6. What I (Claude) do vs what you do

- **I build:** all the code, pages, schema, the generator that turns your inventory into the site, the Worker for the AI + leads, the quote tool, the newsletter job. I hand you copy-paste commands.
- **You do (accounts only):** create the free Cloudflare account, run a couple of deploy commands I give you, connect the domain, and set up the Retell voice agent + your phone number for the texts. I'll walk you through each.

---

## 7. Next step

Say the word and I'll **scaffold the live site first** — the folder, the Cloudflare Pages setup, and the inventory-driven pages with all the GEO fixes — so you have something real deployed tonight. Then we layer the AI, the quote tool, and the newsletter on top.

*Built for Premier Equipment by La Crown Inc. — be the human in the equation.*

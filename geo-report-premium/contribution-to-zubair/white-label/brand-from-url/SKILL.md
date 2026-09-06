---
name: brand-from-url
description: Extract a user's brand identity (company name, logo, primary/accent colors, tagline, contact info, address, social links) directly from their website and write it to a brand cache JSON file. Use this INSTEAD of asking the user to hand-edit `.imm_brand.json` or any other brand config. Triggers on phrases like "pull my brand from my website", "scrape my brand", "set up my brand from [url]", "get brand info from this site", "build my brand.json from my website", "auto-detect my brand", or any time a downstream skill needs `.imm_brand.json` and the cache doesn't exist yet. Always shows the user what was detected and waits for confirmation before writing the cache.
---

# Brand-From-URL

One-shot bootstrap skill that replaces the manual `.imm_brand.json` edit step. Give it a website URL, it scrapes the public homepage, and writes the same brand cache file every downstream skill (IMM agent, photo-watermark, brand-imprint, sales-proposal, GEO report, etc.) already reads.

## When this fires

- *"Pull my brand info from lacrown.ai"*
- *"Set up my brand from my website"*
- *"Auto-detect my brand"*
- A downstream skill needs `.imm_brand.json` and the file doesn't exist
- Anyone asking "can it scrape brand from a website instead of brand.json?"

## What it extracts

| Field | Source (in priority order) |
|---|---|
| `company_name` | `og:site_name` → `<title>` (split on separators) → hostname |
| `tagline` | `og:title` extra after separator |
| `description` | `og:description` → `<meta name="description">` |
| `logo_url` | `og:image` → `apple-touch-icon` → `<img>` with "logo" in src/alt/class → `<link rel="icon">` |
| `favicon_url` | `<link rel="icon">` / `shortcut icon` |
| `primary_color` | meta `theme-color` → CSS `--brand`/`--primary`/`--accent` vars → darkest non-neutral color in logo |
| `accent_color` | Same sources, chosen to maximize luminance contrast vs. primary |
| `contact_email` | regex over page text, prefers `@<sitedomain>` matches |
| `contact_phone` | regex over page text |
| `address` | schema.org `PostalAddress` JSON-LD (when present) |
| `social_links` | `<a href>` matching linkedin/x/twitter/facebook/instagram/youtube/tiktok |

## Flow (every invocation)

1. **Get the URL.** If the user didn't give one, ask: *"What's your company website?"*

2. **Run the extractor:**
   ```bash
   python3 scripts/brand_extractor.py <URL> /tmp/brand_preview.json
   ```

3. **Show the user what was detected** as a clean readable table:
   ```
   Detected from https://lacrown.ai:
     Company:     La Crown Inc.
     Tagline:     AI Automation for Freight Brokerage
     Logo:        https://lacrown.ai/assets/logo.svg
     Primary:     #0A1E3F  (deep navy)
     Accent:      #D4AF37  (gold)
     Email:       missy@finemarkgroup.com
     Phone:       (574) 555-0142
     LinkedIn:    https://linkedin.com/in/millisa-nwokolo
     Twitter/X:   https://x.com/lacrownai

   Look right? I'll write this to .imm_brand.json on confirm.
   (Reply with corrections — e.g. "primary is #1A2B5C", "phone is wrong", etc.)
   ```

4. **Wait for confirm or corrections.** Apply any edits.

5. **Write the cache** to `/mnt/user-data/uploads/.imm_brand.json` (or the path the user/calling-skill specified). Mention the file is now ready and every downstream skill will pick it up.

## Calling from another skill

If a downstream skill (IMM agent, photo-watermark, etc.) discovers `.imm_brand.json` is missing, it should NOT prompt the user for individual fields. Instead it should call this skill:

```
"Before I build the spec sheet — what's your company website?
 I'll pull your brand colors and contact info so the PDF is white-labeled.
 (Or paste 'skip' for generic branding.)"
```

Then on URL → invoke `scripts/brand_extractor.py` → show preview → confirm → write cache → continue with the original task.

## Output schema (`.imm_brand.json`)

```json
{
  "source_url": "https://lacrown.ai",
  "company_name": "La Crown Inc.",
  "tagline": "AI Automation for Freight Brokerage",
  "description": "...",
  "logo_url": "https://lacrown.ai/assets/logo.svg",
  "favicon_url": "https://lacrown.ai/favicon.ico",
  "primary_color": "#0A1E3F",
  "accent_color": "#D4AF37",
  "all_extracted_colors": ["#0A1E3F", "#D4AF37", "#FFFFFF"],
  "contact_email": "missy@finemarkgroup.com",
  "contact_phone": "(574) 555-0142",
  "address": "12345 Main St, Goshen, IN 46526",
  "social_links": {
    "linkedin": "https://linkedin.com/in/millisa-nwokolo",
    "twitter": "https://x.com/lacrownai",
    "facebook": null,
    "instagram": null,
    "youtube": null,
    "tiktok": null
  },
  "warnings": []
}
```

## Caveats to share with the user upfront

- **JS-heavy sites are flakier.** Squarespace/Webflow/Wix usually expose everything in static HTML. A heavy React/Next site behind client-side rendering may need the user to paste fields manually for anything the homepage doesn't ship in the initial HTML.
- **Auto-detected colors are right ~80% of the time.** Always confirm before locking the cache, otherwise downstream PDFs come out off-brand.
- **The cache is local.** No data leaves the user's machine; the only outbound call is the one HTTP GET to their own homepage (and one GET per logo image).

## Requirements

```
requests
beautifulsoup4
Pillow
cairosvg   # only needed if logo is SVG
```

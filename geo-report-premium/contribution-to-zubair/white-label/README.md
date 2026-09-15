# White-Label Branding for GEO Reports

A small, framework-agnostic helper that lets agencies and resellers rebrand the
GEO reports they generate — agency name, contact details, and colors — from a
single `brand.json` file, **without editing any generator code**.

GEO agencies built on this tool typically deliver reports under their own brand.
Today that means editing colors in the generator by hand; this drops that into
one config file each reseller keeps — and a companion skill that **generates
that config straight from the reseller's website** so there's no JSON to write
by hand at all.

## Two ways to set up your brand

### 1. Auto-extract from your website (recommended)

The `brand-from-url/` skill scrapes your homepage once and writes the
`brand.json` for you — company name, logo URL, primary/accent colors pulled
from the logo image itself + CSS variables, contact phone, address from
schema.org markup, and social links.

```bash
python brand-from-url/scripts/brand_extractor.py https://youragency.com brand.json
```

Example run against `lacrown.ai`:

```
--- Brand summary ---
  Company:  La Crown Inc.
  Tagline:  AI Voice Agents & Automation for Service Businesses
  Logo URL: https://lacrown.ai/images/la-crown-logo-v2.png
  Primary:  #302010
  Accent:   #D0A050
  Address:  Fort Wayne, IN, 46802, US
Wrote: brand.json
```

The output is the same `brand.json` schema described below, so
`brand_config.load_brand()` reads it with zero changes. Detected rich data
(tagline, description, logo URL, all colors, social links, address) is
preserved under an `_extracted` key for any generator that wants it —
`load_brand()` ignores underscore-prefixed keys, so it's invisible to the
merge.

**Confirm before locking it in.** Auto-detected colors are right ~80% of the
time; open the generated `brand.json`, eyeball the primary/secondary hexes,
and tweak anything off before running a report. Most fields are right on the
first pass for sites with proper OpenGraph + schema.org markup.

**Caveats:**
- JS-heavy sites (heavy React/Next behind client-side rendering) may not ship
  the brand stuff in static HTML. In that case fall back to the manual config.
- The extractor only fetches the homepage and the logo image — no other
  outbound calls.

Dependencies (the skill ships its own `requirements.txt`):

```
requests
beautifulsoup4
Pillow
cairosvg   # only needed if your logo is SVG
```

### 2. Manual config (fallback)

Copy `brand.example.json` to `brand.json` and edit. Any field you omit keeps
its default, so a reseller can override as little as a single color:

```json
{
  "name": "Your Agency Inc.",
  "website": "youragency.com",
  "phone": "555-123-4567",
  "contact_name": "Your Name",
  "colors": {
    "primary": "#19C3B2",
    "text_accent": "#19C3B2"
  }
}
```

Keys: `name`, `cover_tag`, `website`, `phone`, `contact_name`, and a `colors`
object (merged key-by-key). Keys starting with `_` (like `_comment`) are
ignored.

## How `load_brand()` works

`brand_config.py` exposes one function, `load_brand()`, that returns a plain
dict and deep-merges an optional `brand.json` over sensible defaults:

```python
from brand_config import load_brand

brand = load_brand("brand.json")        # or load_brand() for defaults

agency   = brand["name"]                 # "La Crown Inc."
primary  = brand["colors"]["primary"]    # "#302010"
contact  = brand["contact_name"]
```

Because it's just a dict, you can feed it into any report generator —
ReportLab, HTML/Playwright, or anything else — wherever you currently
hard-code colors or a company name.

## Try it

```bash
# Auto-extract path
python brand-from-url/scripts/brand_extractor.py https://youragency.com brand.json
python brand_config.py brand.json        # prints the merged brand dict

# Manual path
cp brand.example.json brand.json
# edit brand.json
python brand_config.py brand.json
```

## Credit

Contributed as a thank-you by Millisa Nwokolo (La Crown Inc.), built on top of
the GEO-SEO Claude engine by Zubair Trabzada. MIT licensed.

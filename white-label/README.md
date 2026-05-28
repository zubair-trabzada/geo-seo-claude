# White-Label Branding for GEO Reports

A small, framework-agnostic helper that lets agencies and resellers rebrand the
GEO reports they generate — agency name, contact details, and colors — from a
single `brand.json` file, **without editing any generator code**.

This is useful because GEO agencies built on this tool typically deliver reports
under their own brand. Today that means editing colors in the generator by hand;
this drops that into one config file each reseller can keep.

## How it works

`brand_config.py` exposes one function, `load_brand()`, that returns a plain dict
and deep-merges an optional `brand.json` over sensible defaults:

```python
from brand_config import load_brand

brand = load_brand("brand.json")        # or load_brand() for defaults

agency   = brand["name"]                 # "Your Agency Inc."
primary  = brand["colors"]["primary"]    # "#19C3B2"
contact  = brand["contact_name"]
```

Because it's just a dict, you can feed it into any report generator — ReportLab,
HTML/Playwright, or anything else — wherever you currently hard-code colors or a
company name.

## Config

Copy `brand.example.json` to `brand.json` and edit. Any field you omit keeps its
default, so a reseller can override as little as a single color:

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
object (merged key-by-key). Keys starting with `_` (like `_comment`) are ignored.

## Try it

```bash
python brand_config.py brand.json    # prints the merged brand dict
```

## Credit

Contributed as a thank-you by Millisa Nwokolo (La Crown Inc.), built on top of the
GEO-SEO Claude engine by Zubair Trabzada. MIT licensed.

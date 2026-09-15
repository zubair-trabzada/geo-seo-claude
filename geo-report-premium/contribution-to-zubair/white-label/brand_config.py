"""
White-label brand config loader for GEO-SEO Claude report generators.

Lets agencies/resellers rebrand generated reports — name, contact details, and
colors — from an external brand.json file, with no need to edit generator code.
Framework-agnostic: works with any report generator (ReportLab, HTML/Playwright,
etc.) by exposing a plain dict.

Usage
-----
    from brand_config import load_brand

    brand = load_brand("brand.json")     # deep-merges over DEFAULT_BRAND
    title_color = brand["colors"]["primary"]
    agency_name = brand["name"]

Any field a config omits keeps its default, so a reseller can override as little
as a single color. Keys beginning with "_" (e.g. "_comment") are ignored.

Contributed by Millisa Nwokolo (La Crown Inc.) as a thank-you, built on top of
the GEO-SEO Claude engine by Zubair Trabzada. MIT licensed.
"""

import json
import os
import copy

DEFAULT_BRAND = {
    "name": "Your Agency",
    "cover_tag": "Generative Engine Optimization Audit",
    "website": "youragency.com",
    "phone": "",
    "contact_name": "",
    "colors": {
        "primary":        "#E8A87C",   # headers, accents
        "primary_bright": "#F0B98A",   # hover/highlight variant
        "secondary":      "#E94560",   # gauges, CTAs
        "bg_deep":        "#0A0A0F",
        "bg_dark":        "#111118",
        "bg_card":        "#1A1A28",
        "border":         "#2A2A3A",
        "text_primary":   "#F0EDE8",
        "text_secondary": "#A09898",
        "text_accent":    "#E8A87C",
    },
}


def load_brand(config_path=None):
    """Return a brand dict. If config_path points to a JSON file, deep-merge it
    over the defaults (colors merge key-by-key; everything else overrides)."""
    brand = copy.deepcopy(DEFAULT_BRAND)
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        for key, value in cfg.items():
            if key.startswith("_"):
                continue
            if key == "colors" and isinstance(value, dict):
                brand["colors"].update(value)
            else:
                brand[key] = value
    return brand


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else None
    print(json.dumps(load_brand(path), indent=2))

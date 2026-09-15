#!/usr/bin/env python3
"""Generate brain.json (the 'Nicole Brain') from inventory.json.
This single file feeds the website chat widget AND the Cloudflare Worker AI.
Run after build.py:  python make_brain.py"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "inventory.json"), encoding="utf-8"))
brain = {
    "company": DATA["company"],
    "machines": [
        {"id": m["id"], "brand": m["brand"], "model": m["model"], "tonnage": m["tonnage"],
         "year": m["year"], "shot_size": m["shot_size"], "controller": m["controller"],
         "hours": m["hours"], "condition": m["condition"], "summary": m["summary"]}
        for m in DATA["machines"] if m.get("status") == "available"],
    "faqs": DATA["faqs"],
}
for d in [os.path.join(HERE, "site", "assets"), os.path.join(HERE, "worker")]:
    os.makedirs(d, exist_ok=True)
    json.dump(brain, open(os.path.join(d, "brain.json"), "w", encoding="utf-8"), indent=2)
print(f"brain.json written ({len(brain['machines'])} machines, {len(brain['faqs'])} FAQs) to site/assets/ and worker/")

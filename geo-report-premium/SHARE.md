# geo-report-premium
### A Premium PDF Layer for GEO-SEO Claude
**Built by Millisa Nwokolo · La Crown Inc. · lacrown.ai**

---

## What This Is

This is a premium client-facing PDF report layer that sits on top of Zubair Trabzada's
[GEO-SEO Claude](https://github.com/zubair-trabzada/geo-seo-claude) audit skill.

Zubair's skill does the heavy lifting — 11 sub-skills, 5 parallel agents, citability scoring,
AI crawler analysis, full audit engine. This layer takes that raw output and turns it into
a **branded, client-ready PDF** you can send the same day.

---

## What You Get

| File | What It Does |
|------|-------------|
| `SKILL.md` | Claude Code skill — defines the parse → beautify workflow and JSON schema |
| `beautifier.py` | Python script — takes JSON data, outputs a premium dark-branded PDF |
| `sample-data.json` | Working example of the full data schema |
| `SETUP.md` | One-time setup steps and usage instructions |

---

## The Workflow

**Step 1** — Run Zubair's audit as normal:
```
/geo audit yourprospect.com
```

**Step 2** — Tell Claude Code to parse it:
```
Parse that audit output into the JSON schema in my
geo-report-premium/SKILL.md and save it as geo-data-{company}.json
```

**Step 3** — Run the beautifier:
```bash
python beautifier.py geo-data-company.json \
  --output GEO-Report-Company-Premium.pdf
```

Done. Premium PDF in your folder in about 10 seconds.

---

## One-Time Setup

```bash
pip install playwright
python -m playwright install chromium
```

That's it. No other dependencies beyond what Zubair's skill already uses.

---

## Branding

Default branding is La Crown Inc. (dark background, gold accents, coral score gauges).

To white-label with your own brand, open `beautifier.py` and edit the `BRAND` block at
the top — name, tagline, website, phone, and hex color values. Full color guide is in `SKILL.md`.

---

## Naming Convention

```
GEO-Report-{CompanyName}-Premium_{YYYY-MM-DD}.pdf
```

---

## Credits

The analysis engine — 11 sub-skills, 5 parallel agents, citability scoring, AI crawler
monitoring, platform readiness scoring — is entirely the work of
**[Zubair Trabzada](https://github.com/zubair-trabzada/geo-seo-claude)**.

This premium layer adds: branded presentation, two-stage parse/beautify workflow,
dark-gold visual identity, and client-ready PDF packaging.

---

## Questions

Millisa Nwokolo · La Crown Inc.
260-782-8390 · lacrown.ai/geo-upward

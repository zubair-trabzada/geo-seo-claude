# GEO Report Premium — Setup & Usage Guide
# La Crown Inc. · lacrown.ai/geo-upward

---

## What's in This Package

| File | Purpose |
|------|---------|
| `SKILL.md` | Claude Code skill — defines the parse→beautify workflow |
| `beautifier.py` | Python script — takes JSON data, outputs premium PDF |
| `sample-data-ascendtms.json` | Example JSON showing the full data schema |
| `SETUP.md` | This file |

---

## One-Time Setup (Do This Once)

```bash
# 1. Install Python dependencies
pip install playwright

# 2. Install Chromium browser (needed for PDF rendering)
python -m playwright install chromium

# 3. Place these files somewhere accessible:
#    Option A: In your GEO-SEO Claude skills folder
#    ~/.claude/skills/geo-report-premium/
#
#    Option B: In a dedicated working directory
#    ~/geo-reports/
```

---

## Every Time You Run a Report

### Step 1 — Run your GEO audit as normal

Use Zubair's GEO-SEO Claude skill to run the audit:
```
/geo audit <url>
```

Or you can run the audit any way you normally do and collect the raw output.

---

### Step 2 — Parse the audit data into JSON

Tell Claude Code:

```
Parse this GEO audit output into the JSON schema defined in
~/.claude/skills/geo-report-premium/SKILL.md
and save it as geo-data-{company}.json
```

Claude Code reads the SKILL.md schema, extracts all scores/findings/actions from 
the raw audit, and creates a clean JSON file.

---

### Step 3 — Run the beautifier

```bash
python beautifier.py geo-data-{company}.json \
  --output GEO-Report-{Company}-Premium.pdf

# With client logo:
python beautifier.py geo-data-{company}.json \
  --output GEO-Report-{Company}-Premium.pdf \
  --client-logo client-logo.png
```

That's it. You get a premium PDF in ~10 seconds.

---

## Naming Your Output Files

Follow this convention:

```
GEO-Report-{CompanyName}-Premium_{YYYY-MM-DD}.pdf
```

Examples:
```
GEO-Report-MachineryNetwork-Premium_2026-03-05.pdf
GEO-Report-AscendTMS-Premium_2026-03-07.pdf
```

---

## Customizing the Brand (One-Time Per Client)

To white-label for a different brand, open `beautifier.py` and edit the `BRAND` dict at the top:

```python
BRAND = {
    "name":         "Your Agency Name",
    "tagline":      "Your Tagline",
    "website":      "youragency.com",
    "phone":        "555-555-5555",
    "contact_name": "Your Name",
    "colors": {
        "primary":   "#E8A87C",  # Change this to your brand color
        "secondary": "#E94560",  # Change this to your secondary color
        ...
    }
}
```

See the color table in SKILL.md for what each color controls.

---

## Telling Claude Code to Use This Skill

Add this to your system prompt or reference it directly:

```
When generating GEO reports, use the two-stage workflow defined in
~/.claude/skills/geo-report-premium/SKILL.md:
1. Parse the raw audit output into the JSON schema
2. Run beautifier.py to generate the premium PDF
```

Or trigger it per-conversation:

```
/geo report-premium <url>
```

Claude Code will:
1. Check if a prior audit exists for that URL
2. Parse the audit data into JSON
3. Run the beautifier
4. Return the PDF file path

---

## Troubleshooting

**"playwright not found"**
```bash
pip install playwright
python -m playwright install chromium
```

**Fonts not loading in PDF**
The script uses Google Fonts (DM Serif Display, Outfit). If you're offline or on a 
network that blocks fonts.googleapis.com, the PDF will fall back to Georgia/sans-serif.
For offline use, download and embed the fonts locally.

**PDF page breaks are off**
Reduce the font size in beautifier.py: find `html {{ font-size: 13px; }}` and change to `12px`.

**Want HTML preview before PDF**
```bash
python beautifier.py data.json --html-only
# Opens geo-report-premium.html — view in Chrome, then Print → Save as PDF
```

---

## Questions

Millisa Nwokolo · La Crown Inc.
260-782-8390 · lacrown.ai/geo-upward

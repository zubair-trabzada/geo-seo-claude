---
name: geo-report-pdf
description: Generate a professional PDF report from a GEO audit using pandoc + Chrome headless. Converts GEO-AUDIT-REPORT.md into a styled, client-ready PDF with a cover page, color-coded score tables, severity-tagged findings, and a 90-day roadmap.
version: 2.0.0
author: geo-seo-claude
tags: [geo, pdf, report, client-deliverable, professional]
allowed-tools: Read, Grep, Glob, Bash, Write
---

# GEO PDF Report Generator (pandoc pipeline)

## Prerequisites

- **pandoc** — `brew install pandoc`
- **Google Chrome** — must be installed at `/Applications/Google Chrome.app/`

No Python dependencies. No ReportLab. No JSON data wrangling.

## How It Works

1. Read `GEO-AUDIT-REPORT.md` in the current directory (created by `/geo audit`)
2. Extract cover metadata from the report (brand name, domain, GEO score, date, locations)
3. Run `pandoc` with the bundled CSS + HTML template to produce a self-contained `GEO-REPORT.html`
4. Run Chrome headless to print the HTML to `GEO-REPORT.pdf`

The pandoc template (`~/.claude/skills/geo/templates/geo-report-template.html`) injects:
- A full-bleed dark navy cover section with the GEO score badge
- Per-section cover metadata (date, business type, locations, platform)
- JavaScript that runs inside Chrome before printing to color-code score cells and severity-tag finding sections

## Workflow

### Step 1: Check for audit report

Look for `GEO-AUDIT-REPORT.md` in the current directory. If absent, tell the user to run `/geo audit <url>` first.

### Step 2: Extract cover metadata from the report

Read the top of `GEO-AUDIT-REPORT.md` and extract:

| Field | Where to find it |
|---|---|
| `brand_name` | First H1 title (after "GEO Audit Report:") |
| `domain` | Second bold line (e.g. `**Domain:** alexamediasolutions.com`) |
| `geo_score` | Line matching `## Overall GEO Score: XX / 100` |
| `score_label` | Word after the score on that same line (e.g. "Poor", "Fair", "Good") |
| `date` | `**Audit Date:**` line |
| `business_type` | `**Business Type:**` line |
| `locations` | `**Locations:**` line |
| `platform` | `**CMS:**` line |

### Step 3: Run pandoc

```bash
pandoc GEO-AUDIT-REPORT.md \
  --to html5 \
  --standalone \
  --embed-resources \
  --template ~/.claude/skills/geo/templates/geo-report-template.html \
  --css ~/.claude/skills/geo/templates/geo-report-style.css \
  --metadata title="GEO Audit Report — <brand_name>" \
  --metadata brand_name="<brand_name>" \
  --metadata domain="<domain>" \
  --metadata geo_score="<geo_score>" \
  --metadata score_label="<score_label>" \
  --metadata date="<date>" \
  --metadata business_type="<business_type>" \
  --metadata locations="<locations>" \
  --metadata platform="<platform>" \
  -o GEO-REPORT.html
```

Replace `<field>` placeholders with values extracted in Step 2. If a field is not found in the report, omit that `--metadata` flag — the template has sensible defaults.

### Step 4: Run Chrome headless

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new \
  --disable-gpu \
  --no-sandbox \
  --print-to-pdf="$(pwd)/GEO-REPORT.pdf" \
  --print-to-pdf-no-header \
  --no-pdf-header-footer \
  --virtual-time-budget=5000 \
  "file://$(pwd)/GEO-REPORT.html"
```

### Step 5: Report completion

Tell the user:
- `GEO-REPORT.pdf` was generated in the current directory
- File size
- Optionally: `open GEO-REPORT.pdf` to preview it

## What the PDF Contains

- **Cover page** — Dark navy gradient, brand name, domain, GEO score badge (colored by score), audit date, business type, locations, CMS platform
- **Score tables** — Cells containing `XX/100` are color-coded: ≥80 green, ≥65 blue, ≥50 amber, ≥35 orange, <35 red
- **Finding sections** — `h3` headings containing "Critical / High / Medium / Low" get severity-colored left-border callout blocks (red / orange / yellow / green)
- **Section page breaks** — Major sections (High Priority, 90-Day Roadmap, Component Score Summary, Generated Schema) break to new pages automatically
- **Code blocks** — JSON schema templates render with dark theme monospace styling
- **Page footer** — Brand name · GEO Audit · date + page numbers (via CSS `@page`)

## Customizing the Report

- **Colors / typography** — Edit `~/.claude/skills/geo/templates/geo-report-style.css`
- **Cover layout** — Edit `~/.claude/skills/geo/templates/geo-report-template.html`
- **Score thresholds for color-coding** — Edit the `scoreColor()` function in the template's `<script>` block
- **Which sections get page breaks** — Edit the `breakBefore` array in the template's `<script>` block

## Troubleshooting

| Problem | Fix |
|---|---|
| `pandoc: command not found` | `brew install pandoc` |
| Chrome not found | Check path: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` |
| PDF is blank / empty | Increase `--virtual-time-budget` to 8000 |
| Cover metadata missing | Check GEO-AUDIT-REPORT.md has the standard header format |
| Fonts not loading | PDF is rendered offline; system fonts are used as fallback — this is expected |

---
name: geo-report-pdf
description: Generate a professional PDF report from GEO audit data using ReportLab. Creates a polished, client-ready PDF with score gauges, bar charts, platform readiness visualizations, color-coded tables, and prioritized action plans.
version: 1.0.0
author: geo-seo-claude
tags: [geo, pdf, report, client-deliverable, professional]
allowed-tools: Read, Grep, Glob, Bash, WebFetch, Write
---

# GEO PDF Report Generator

## Purpose

This skill generates a professional, visually polished PDF report from GEO audit data. The PDF includes score gauges, bar charts, platform readiness visualizations, color-coded tables, and a prioritized action plan — ready to deliver directly to clients.

## Prerequisites

- **ReportLab** must be installed: `pip install reportlab`
- The PDF generation script is located at: `~/.claude/skills/geo/scripts/generate_pdf_report.py`
- Run a full GEO audit first (using `/geo-audit`) to have data to include in the report

## How to Generate a PDF Report

### Step 1: Collect Audit Data

After running a full `/geo-audit`, collect all scores, findings, and recommendations into a JSON structure. The JSON data must follow this schema:

```json
{
    "url": "https://example.com",
    "brand_name": "Example Company",
    "date": "2026-02-18",
    "geo_score": 65,
    "scores": {
        "ai_citability": 62,
        "brand_authority": 78,
        "content_eeat": 74,
        "technical": 72,
        "schema": 45,
        "platform_optimization": 59
    },
    "platforms": {
        "Google AI Overviews": 68,
        "ChatGPT": 62,
        "Perplexity": 55,
        "Gemini": 60,
        "Bing Copilot": 50
    },
    "executive_summary": "A 4-6 sentence summary of the audit findings...",
    "findings": [
        {
            "severity": "critical",
            "title": "Finding Title",
            "description": "Description of the finding and its impact."
        }
    ],
    "quick_wins": [
        "Action item 1",
        "Action item 2"
    ],
    "medium_term": [
        "Action item 1",
        "Action item 2"
    ],
    "strategic": [
        "Action item 1",
        "Action item 2"
    ],
    "crawler_access": {
        "GPTBot": {"platform": "ChatGPT", "status": "Allowed", "recommendation": "Keep allowed"},
        "ClaudeBot": {"platform": "Claude", "status": "Blocked", "recommendation": "Unblock for visibility"}
    }
}
```

### Step 2: Write JSON Data to a Temp File

Write the collected audit data to a temporary JSON file:

```bash
# Write audit data to temp file
cat > /tmp/geo-audit-data.json << 'EOF'
{ ... audit JSON data ... }
EOF
```

### Step 3: Generate the PDF

Run the PDF generation script:

```bash
python3 ~/.claude/skills/geo/scripts/generate_pdf_report.py /tmp/geo-audit-data.json GEO-REPORT-[brand].pdf
```

The script will produce a professional PDF report with:
- **Cover Page** — Brand name, URL, date, overall GEO score with visual gauge
- **Executive Summary** — Key findings and top recommendations
- **Score Breakdown** — Table and bar chart of all 6 scoring categories
- **AI Platform Readiness** — Visual horizontal bar chart per platform with scores
- **AI Crawler Access** — Color-coded table (green=allowed, red=blocked)
- **Key Findings** — Severity-coded findings list (critical/high/medium/low)
- **Prioritized Action Plan** — Quick wins, medium-term, and strategic initiatives
- **Appendix** — Methodology, data sources, and glossary

### Step 4: Return the PDF Path

After generation, tell the user where the PDF was saved and its file size.

## Complete Workflow Example

When the user runs this skill, follow this exact sequence:

1. **Check for existing audit data** — Look for recent GEO audit reports in the current directory:
   - `GEO-CLIENT-REPORT.md`
   - `GEO-AUDIT-REPORT.md`
   - Or any `GEO-*.md` files from a recent audit

2. **If no audit data exists** — Tell the user to run `/geo-audit <url>` first, then come back for the PDF.

3. **If audit data exists** — Parse the markdown report to extract:
   - Overall GEO score
   - Category scores (citability, brand authority, content/E-E-A-T, technical, schema, platform)
   - Platform readiness scores (Google AIO, ChatGPT, Perplexity, Gemini, Bing Copilot)
   - AI crawler access status
   - Key findings with severity levels
   - Quick wins, medium-term, and strategic action items
   - Executive summary

4. **Build the JSON** — Structure all data into the JSON schema shown above.

5. **Write JSON to temp file** — Save to `/tmp/geo-audit-data.json`

6. **Run the PDF generator**:
   ```bash
   python3 ~/.claude/skills/geo/scripts/generate_pdf_report.py /tmp/geo-audit-data.json "GEO-REPORT-[brand_name].pdf"
   ```

7. **Report success** — Tell the user the PDF was generated, its location, and file size.

## If the User Provides a URL

If the user runs `/geo-report-pdf https://example.com` with a URL:
1. First run a full audit: invoke the `geo-audit` skill for that URL
2. Then collect all the audit data from the generated report files
3. Generate the PDF as described above

## Parsing Markdown Audit Data

When extracting data from existing GEO markdown reports, look for these patterns:

- **GEO Score**: Look for "GEO Score: XX/100" or "Overall: XX/100" or "GEO Readiness Score: XX"
- **Category Scores**: Look for score tables with columns like "Component | Score | Weight"
- **Platform Scores**: Look for tables with "Google AI Overviews", "ChatGPT", "Perplexity", etc.
- **Crawler Status**: Look for tables with "Allowed" or "Blocked" status for crawlers like GPTBot, ClaudeBot
- **Findings**: Look for sections titled "Key Findings", "Critical Issues", "Recommendations"
- **Action Items**: Look for sections titled "Quick Wins", "Action Plan", "Recommendations"

## Notes

- If ReportLab is not installed, run: `pip install reportlab`
- The PDF is designed for US Letter size (8.5" x 11")
- Color palette: Navy primary (#1a1a2e), Blue accent (#0f3460), Coral highlight (#e94560), Green success (#00b894)
- Each page has a header line, page numbers, "Confidential" watermark, and generation date
- Score gauges use traffic-light colors: green (80+), blue (60-79), yellow (40-59), red (below 40)

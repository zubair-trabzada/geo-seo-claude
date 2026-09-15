# GEO Report Premium — SKILL.md
# La Crown Inc. · lacrown.ai/geo-upward
# Version 2.0 — Two-Stage Workflow (Parse → Beautify)

---

## Purpose

This skill transforms any raw GEO audit output into a **premium branded PDF** matching
the La Crown dark-gold visual identity. It works in two stages:

1. **Parse** — Extract structured data from the raw audit output (text, markdown, or basic PDF)
2. **Beautify** — Inject that data into the premium HTML template and render to PDF

The result: a client-ready deliverable every time, consistent branding, no manual formatting.

---

## When to Invoke This Skill

Trigger: `/geo report-premium <url_or_raw_audit_data>`

Claude Code should run this skill after a GEO audit has been completed and its raw output
is available. If no prior audit exists, run the core GEO audit first, then invoke this skill.

---

## Two-Stage Workflow

### STAGE 1 — PARSE (Claude Code does this)

Read the raw audit output and extract a JSON object matching the schema below.
The raw audit may be:
- A markdown report in the conversation
- A basic PDF (use pdfplumber to extract text)
- Plain text output from the core GEO-SEO Claude skill

**Parse into this exact JSON schema:**

```json
{
  "company_name": "Machinery Network Inc.",
  "url": "machinerynetwork.com",
  "audit_date": "March 05, 2026",
  "overall_score": 38,
  "company_tagline": "Brief framing line about the company's real-world authority vs AI gap",
  "stats": [
    {"value": "38 Yrs", "label": "Industry Experience"},
    {"value": "$1B+",   "label": "Lifetime Transactions"},
    {"value": "4",      "label": "Critical Issues Found"}
  ],
  "executive_summary": "Full paragraph. Bold key phrases with <strong> tags. This is the 'The Problem' narrative — contrast real-world authority with AI invisibility. Be specific about the root causes.",
  "dimensions": [
    {
      "name": "AI Citability & Visibility",
      "description": "Can AI platforms find and quote your content?",
      "score": 35,
      "weight": "25%",
      "weighted_score": "8.8"
    },
    {
      "name": "Brand Authority Signals",
      "description": "External signals that validate who you are",
      "score": 30,
      "weight": "20%",
      "weighted_score": "6.0"
    },
    {
      "name": "Content Quality & E-E-A-T",
      "description": "Depth, expertise, and trustworthiness of content",
      "score": 38,
      "weight": "20%",
      "weighted_score": "7.6"
    },
    {
      "name": "Technical Foundations",
      "description": "Server-side rendering, sitemaps, crawlability",
      "score": 58,
      "weight": "15%",
      "weighted_score": "8.7"
    },
    {
      "name": "Schema & Structured Data",
      "description": "Schema markup giving AI systems structured facts",
      "score": 30,
      "weight": "10%",
      "weighted_score": "3.0"
    },
    {
      "name": "Platform Optimization",
      "description": "Presence on platforms AI systems index",
      "score": 37,
      "weight": "10%",
      "weighted_score": "3.7"
    }
  ],
  "platforms": [
    {"name": "Google AI Overviews", "score": 44},
    {"name": "ChatGPT",            "score": 30},
    {"name": "Perplexity",         "score": 32},
    {"name": "Gemini",             "score": 38},
    {"name": "Bing Copilot",       "score": 39}
  ],
  "crawlers": [
    {
      "name": "GPTBot",
      "platform": "ChatGPT / OpenAI",
      "status": "Not Mentioned",
      "recommendation": "Add explicit Allow directive"
    },
    {
      "name": "ClaudeBot",
      "platform": "Claude / Anthropic",
      "status": "Not Mentioned",
      "recommendation": "Add explicit Allow directive"
    },
    {
      "name": "PerplexityBot",
      "platform": "Perplexity AI",
      "status": "Not Mentioned",
      "recommendation": "Add explicit Allow directive"
    },
    {
      "name": "Google-Extended",
      "platform": "Google Gemini",
      "status": "Not Mentioned",
      "recommendation": "Add explicit Allow directive"
    },
    {
      "name": "Googlebot",
      "platform": "Google Search",
      "status": "Allowed",
      "recommendation": "Keep allowed"
    }
  ],
  "findings": [
    {
      "severity": "CRITICAL",
      "title": "No llms.txt File",
      "description": "The site returns a 404 for /llms.txt. AI systems like ChatGPT, Claude, and Perplexity have no structured summary of the business. This is the single highest-ROI fix available."
    },
    {
      "severity": "CRITICAL",
      "title": "Zero Source Citations Across All Content",
      "description": "All 10 blog articles contain zero external citations. AI systems heavily penalize unsourced factual claims and will not cite them as authoritative."
    },
    {
      "severity": "HIGH",
      "title": "No Wikipedia or Wikidata Entity",
      "description": "No Wikipedia article and no Wikidata entity exist. These are primary structured knowledge sources AI models use for entity recognition."
    }
  ],
  "action_plan": {
    "quick_wins": [
      {
        "title": "Create /llms.txt file at domain root",
        "description": "Describe company, services, key content, and team expertise. Gives AI systems a structured summary. 30-minute implementation, immediate AI visibility boost.",
        "time_estimate": "30 min"
      }
    ],
    "medium_term": [
      {
        "title": "Add 5-10 external citations per blog article",
        "description": "Link to OEM specs, MDNA resources, industry reports, and BLS data. Transforms unsourced claims into verifiable, citable content.",
        "time_estimate": ""
      }
    ],
    "strategic": [
      {
        "title": "Publish quarterly industry report",
        "description": "Proprietary data from actual transactions. Creates the definitive industry resource AI systems will cite.",
        "time_estimate": ""
      }
    ]
  },
  "methodology": "This GEO audit analyzed the website across six weighted dimensions: AI Citability & Visibility (25%), Brand Authority Signals (20%), Content Quality & E-E-A-T (20%), Technical Foundations (15%), Schema & Structured Data (10%), and Platform Optimization (10%). Platforms assessed: Google AI Overviews, ChatGPT Web Search, Perplexity AI, Google Gemini, Bing Copilot."
}
```

---

### PARSING RULES

When extracting from raw audit text, follow these rules:

**Scores:** Extract numeric scores only (e.g. "34/100" → 34). Never round or estimate.

**Severity levels:** Map exactly to: CRITICAL / HIGH / MEDIUM / LOW (uppercase)

**executive_summary:** Write the "The Problem" narrative paragraph. Lead with the company's real-world authority (years, revenue, awards, memberships), then hard pivot to "But AI can't see any of it." Name the specific technical root causes. Use `<strong>` tags around specific failure points for visual emphasis (e.g. `<strong>zero external citations</strong>`).

**company_tagline:** A single punchy line that captures the authority-vs-AI-gap tension. Example: "38 years and $1B+ in deals. AI search engines can't see any of it."

**stats:** Pull 3-5 of the most impressive credibility signals from the audit (years in business, transaction volume, review counts, certifications, user counts). These appear as bold badges on the cover page.

**findings:** Include ALL findings from the audit. Order: CRITICAL first, then HIGH, then MEDIUM, then LOW.

**crawlers:** Extract all crawlers mentioned. Map status values:
  - "Allowed" → "Allowed"  
  - "Blocked" → "Blocked"
  - "Not Mentioned" / not in robots.txt → "Not Mentioned"
  - Crawl delay present → "Xs Crawl Delay"

---

### STAGE 2 — BEAUTIFY (Run the Python script)

After building the JSON, run:

```bash
# Basic usage
python beautifier.py audit_data.json --output GEO-Report-{CompanyName}-Premium.pdf

# With client logo
python beautifier.py audit_data.json \
  --output GEO-Report-{CompanyName}-Premium.pdf \
  --client-logo client-logo.png

# HTML preview only (faster iteration)
python beautifier.py audit_data.json --html-only
```

The script requires:
- Python 3.9+
- playwright (`pip install playwright && python -m playwright install chromium`)

If playwright is unavailable, use `--html-only` and open the HTML in Chrome, then Print → Save as PDF.

---

## File Naming Convention

```
GEO-Report-{CompanyName}-Premium_{YYYY-MM-DD}.pdf
```

Examples:
- `GEO-Report-MachineryNetwork-Premium_2026-03-05.pdf`
- `GEO-Report-AscendTMS-Premium_2026-03-07.pdf`
- `GEO-Report-SethGeller-Premium_2026-03-10.pdf`

---

## Brand Configuration

The beautifier.py file contains a `BRAND` dict at the top. Current defaults:

```python
BRAND = {
    "name":         "La Crown Inc.",
    "tagline":      "AI-Powered Growth",
    "website":      "lacrown.ai/geo-upward",
    "phone":        "260-782-8390",
    "contact_name": "Millisa Nwokolo",
    "colors": {
        "primary":    "#E8A87C",   # warm gold — headers, accents
        "secondary":  "#E94560",   # coral red — score gauges, CTAs
        "bg_dark":    "#111118",   # page background
        "bg_card":    "#1A1A28",   # card backgrounds
        ...
    }
}
```

To white-label for a reseller, edit only this block.

---

## Score Color System

| Range   | Color     | Label        |
|---------|-----------|--------------|
| 85–100  | #2ECC71   | EXCELLENT    |
| 70–84   | #3498DB   | GOOD         |
| 55–69   | #F39C12   | MODERATE     |
| 40–54   | #E67E22   | DEVELOPING   |
| 0–39    | #E74C3C   | CRITICAL     |

---

## Quality Checklist (Before Delivering to Client)

- [ ] Overall score matches the raw audit exactly
- [ ] All dimension scores and weighted scores are correct
- [ ] Platform scores match (check each: Google AIO, ChatGPT, Perplexity, Gemini, Copilot)
- [ ] All CRITICAL findings are present
- [ ] Action plan has at least 3 items in each tier
- [ ] Client name and URL appear correctly on cover page
- [ ] Audit date is correct
- [ ] Methodology paragraph references the correct URL and date
- [ ] File is named with the correct date suffix

---

## Troubleshooting

**Playwright not rendering fonts:**
Add a 2-second delay: `page.wait_for_timeout(2000)` before `page.pdf()`

**PDF pages cutting off content:**
The template uses `page-break-after: always` on each section. If content overflows,
either trim the findings list or reduce font size in the `html` style block (`html { font-size: 12px; }`).

**Missing score in raw audit:**
If a dimension score is missing, use 0. Never fabricate a score. Note the gap in the methodology section.

**Client logo not showing:**
Supported formats: PNG, JPG, SVG. Pass the full path to `--client-logo`. 
Max display size: 200px wide × 52px tall (auto-scaled).

---

## Credits

Premium report layer by Millisa Nwokolo / La Crown Inc.
Built on top of the GEO-SEO Claude analysis engine by Zubair Trabzada.
Original: github.com/zubair-trabzada/geo-seo-claude

---

## White-Label / Reseller Branding (`--brand-config`)

Resellers can rebrand the entire report **without editing `beautifier.py`**. Create a
`brand.json` file with any subset of fields and pass it with `--brand-config`:

```bash
python beautifier.py audit_data.json \
  --output GEO-Report-{CompanyName}-Premium.pdf \
  --client-logo client-logo.png \
  --brand-config brand.json
```

`brand.json` (copy `brand.example.json` and edit). Any field you omit keeps the
La Crown default, so a customer can override as little as one color:

```json
{
  "name": "Your Agency Inc.",
  "cover_tag": "Generative Engine Optimization Audit",
  "website": "youragency.com",
  "phone": "555-123-4567",
  "contact_name": "Your Name",
  "colors": {
    "primary": "#FFC72C",
    "primary_bright": "#FFD75E",
    "text_accent": "#FFC72C"
  }
}
```

What it controls:
- `name` → cover header brand line, all page footers, and the © copyright line
- `cover_tag` → small line under the brand name on the cover (defaults to "Generative Engine Optimization Audit")
- `website`, `phone`, `contact_name` → cover footer contact block
- `colors.*` → the same color keys documented in Brand Configuration (override any subset)

The config is deep-merged over the defaults at runtime, so each customer keeps their own
`brand.json` and never touches the Python.

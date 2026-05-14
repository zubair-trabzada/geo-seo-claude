---
name: seo-page
description: >
  Deep single-page SEO analysis covering on-page elements, content quality,
  technical meta tags, schema, images, and performance. Use when user says
  "analyze this page", "check page SEO", or provides a single URL for review.
---

# Single Page Analysis

Apply `resources/references/llm-audit-rubric.md` for evidence standards, confidence labels, severity mapping, and report structure.

## What to Analyze

### On-Page SEO
- Title tag: 50-60 characters, includes primary keyword, unique
- Meta description: 150-160 characters, compelling, includes keyword
- H1: exactly one, matches page intent, includes keyword
- H2-H6: logical hierarchy (no skipped levels), descriptive
- URL: short, descriptive, hyphenated, no parameters
- Internal links: sufficient, relevant anchor text, no orphan pages
- External links: to authoritative sources, reasonable count

### Content Quality
- Word count vs page type minimums (see quality-gates.md)
- Readability: Flesch Reading Ease score, grade level
- Keyword density: natural (1-3%), semantic variations present
- E-E-A-T signals: author bio, credentials, first-hand experience markers
- Content freshness: publication date, last updated date

### Technical Elements
- Canonical tag: present, self-referencing or correct
- Meta robots: index/follow unless intentionally blocked
- Open Graph: og:title, og:description, og:image, og:url
- Twitter Card: twitter:card, twitter:title, twitter:description
- Hreflang: if multi-language, correct implementation

### Schema Markup
- Detect all types (JSON-LD preferred)
- Validate required properties
- Identify missing opportunities
- NEVER recommend HowTo (deprecated) or FAQ (restricted to gov/health)

### Images
- Alt text: present, descriptive, includes keywords where natural
- File size: flag >200KB (warning), >500KB (critical)
- Format: recommend WebP/AVIF over JPEG/PNG
- Dimensions: width/height set for CLS prevention
- Lazy loading: loading="lazy" on below-fold images

### Core Web Vitals (reference only — not measurable from HTML alone)
- Flag potential LCP issues (huge hero images, render-blocking resources)
- Flag potential INP issues (heavy JS, no async/defer)
- Flag potential CLS issues (missing image dimensions, injected content)

## Output

### Output Files (Required)
- `FULL-AUDIT-REPORT.md` — Full single-page findings with evidence, severity, and confidence labels
- `ACTION-PLAN.md` — Prioritized implementation plan (Critical → High → Medium → Low)
- `SEO-REPORT.html` — Optional interactive dashboard path (when `generate_report.py` is executed)

### Page Score Card
```
Overall Score: XX/100

On-Page SEO:     XX/100  ████████░░
Content Quality: XX/100  ██████████
Technical:       XX/100  ███████░░░
Schema:          XX/100  █████░░░░░
Images:          XX/100  ████████░░
```

### Issues Found
Organized by priority: Critical → High → Medium → Low

### Recommendations
Specific, actionable improvements with expected impact

### Schema Suggestions
Ready-to-use JSON-LD code for detected opportunities

## Execution Plan

When invoked as an agent to analyze a specific URL, execute these steps:
1. Run `scripts/parse_html.py "$URL" --json` to get title, meta, links, headings, alt text, and schema.
2. Run `scripts/readability.py "$URL" --json` for text metrics and grade level.
3. Run `scripts/pagespeed.py "$URL" --strategy mobile --json` for Core Web Vitals.
4. If applicable, run `scripts/article_seo.py "$URL" --json` for a deeper dive on content scoring.
5. Summarize all findings into the Page Score Card and Issues Found according to the evidence rules.

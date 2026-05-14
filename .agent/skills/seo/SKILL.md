---
name: seo
description: >
  Deterministic LLM-first SEO audits for websites, blog posts, and GitHub
  repositories. Use this when the user asks to "perform SEO analysis", "run SEO
  audit", "analyze SEO", "check technical SEO", "review schema", "Core Web
  Vitals", "E-E-A-T", "hreflang", "GEO", "AEO", or GitHub repository SEO
  optimization. For full/page/repo audits, run bundled scripts for evidence and
  return prioritized, confidence-labeled fixes.
---

# SEO Skill (Agentic / Claude / Codex)

LLM-first SEO analysis skill with 16 specialized sub-skills, 10 specialist agents, and 33 scripts for website, blog, and GitHub repository optimization.

## Deterministic Trigger Mapping

For prompt reliability in Codex/agent IDEs, map common user wording to a fixed workflow:

- If user says `perform seo analysis on <url>` (or similar generic SEO request with a URL), treat it as a **single-URL full audit**.
- If no explicit sub-skill is specified, run the full/page audit path with **LLM-first reasoning** and script-backed evidence.
- For full/page audits, always produce:
  - `FULL-AUDIT-REPORT.md` (detailed findings)
  - `ACTION-PLAN.md` (prioritized fixes)
- If `generate_report.py` is run, also return the saved HTML path (for example `SEO-REPORT.html`).

## Available Commands

| Command | Sub-Skill | Description |
|---------|-----------|-------------|
| `seo audit <url>` | [seo-audit](resources/skills/seo-audit.md) | Full website audit with scoring |
| `seo page <url>` | [seo-page](resources/skills/seo-page.md) | Deep single-page analysis |
| `seo technical <url>` | [seo-technical](resources/skills/seo-technical.md) | Technical SEO checks |
| `seo content <url>` | [seo-content](resources/skills/seo-content.md) | Content quality & E-E-A-T |
| `seo schema <url>` | [seo-schema](resources/skills/seo-schema.md) | Schema detection/validation/generation |
| `seo sitemap <url>` | [seo-sitemap](resources/skills/seo-sitemap.md) | Sitemap analysis & generation |
| `seo images <url>` | [seo-images](resources/skills/seo-images.md) | Image optimization audit |
| `seo geo <url>` | [seo-geo](resources/skills/seo-geo.md) | AI search optimization (GEO) |
| `seo programmatic <url>` | [seo-programmatic](resources/skills/seo-programmatic.md) | Programmatic SEO safeguards |
| `seo competitors <url>` | [seo-competitor-pages](resources/skills/seo-competitor-pages.md) | Comparison/alternatives pages |
| `seo hreflang <url>` | [seo-hreflang](resources/skills/seo-hreflang.md) | International SEO validation |
| `seo plan <url>` | [seo-plan](resources/skills/seo-plan.md) | Strategic SEO planning |
| `seo github <repo_or_url>` | [seo-github](resources/skills/seo-github.md) | GitHub repository discoverability, README, topics, community health, and traffic archival |
| `seo article <url>` | [seo-article](resources/skills/seo-article.md) | Article data extraction & LLM optimization |
| `seo links <url>` | [seo-links](resources/skills/seo-links.md) | External backlink profile & link health |
| `seo aeo <url>` | [seo-aeo](resources/skills/seo-aeo.md) | Answer Engine Optimization (Featured Snippets, PAA, Knowledge Panel) |

---

## Orchestration Logic

When the user requests SEO analysis, follow this routing:

### Step 1 — Identify the Task

Parse the user's request to determine which sub-skill(s) to activate:

- **Full audit**: Read `resources/skills/seo-audit.md` — crawl multiple pages, delegate to agents, score and report
- **Single page**: Read `resources/skills/seo-page.md` — deep dive on one URL
- **Specific area**: Read the matching `resources/skills/seo-*.md` file
- **Strategic plan**: Read `resources/skills/seo-plan.md` and the matching `resources/templates/*.md` for the detected industry
- **GitHub repository SEO**: Read `resources/skills/seo-github.md` and use GitHub scripts with `--provider auto` for API/`gh` fallback.
- **Generic `perform seo analysis on <url>` request**: treat as single-page full audit, read `resources/skills/seo-page.md`, and generate `FULL-AUDIT-REPORT.md` + `ACTION-PLAN.md`.

### Step 2 — Collect Evidence

**Primary method (LLM-first)** — use the built-in `read_url_content` tool first:
```
read_url_content(url)  →  returns parsed HTML content directly
```
Use this as the baseline evidence for reasoning.

**Deterministic verification (recommended when script execution is available)**:
```bash
# Fetch/parse raw HTML for structured checks
python3 <SKILL_DIR>/scripts/fetch_page.py <url> --output /tmp/page.html
python3 <SKILL_DIR>/scripts/parse_html.py /tmp/page.html --url <url> --json

# Optional: generate shareable HTML dashboard artifact
python3 <SKILL_DIR>/scripts/generate_report.py <url> --output SEO-REPORT.html
```

> **Do not use third-party mirrors (e.g., `r.jina.ai`) as primary evidence when direct site fetch or bundled scripts are available.**
> `<SKILL_DIR>` = absolute path to this skill directory (the folder containing this SKILL.md).

### Step 3 — Perform LLM-First Analysis

Use the LLM as the primary SEO analyst:

1. Synthesize evidence from page content, metadata, and optional script outputs.
2. Produce findings with explicit proof:
   - `Finding`
   - `Evidence` (specific element, metric, or snippet)
   - `Impact` (why it matters for ranking/indexing/UX)
   - `Fix` (clear implementation step)
3. Prioritize by impact and implementation effort.
4. Separate confirmed issues, likely issues, and unknowns (missing data).

Always read and apply `resources/references/llm-audit-rubric.md` to keep scoring, severity, confidence, and output structure consistent across audit types.

### Step 4 — Run Baseline Verification Scripts (When execution is available)

For full/page audits, run baseline checks to avoid hypothesis-only reporting. Do not replace LLM reasoning with script-only scoring.

```bash
# Check robots.txt and AI crawler management
python3 <SKILL_DIR>/scripts/robots_checker.py <url>

# Check llms.txt for AI search readiness
python3 <SKILL_DIR>/scripts/llms_txt_checker.py <url>

# Get Core Web Vitals from PageSpeed Insights (free API, no key needed)
python3 <SKILL_DIR>/scripts/pagespeed.py <url> --strategy mobile

# Check security headers (HSTS, CSP, X-Frame-Options, etc.)
python3 <SKILL_DIR>/scripts/security_headers.py <url>

# Detect broken links on a page (404s, timeouts, connection errors)
python3 <SKILL_DIR>/scripts/broken_links.py <url> --workers 5

# Trace redirect chains, detect loops and mixed HTTP/HTTPS
python3 <SKILL_DIR>/scripts/redirect_checker.py <url>

# Analyze readability from fetched HTML (Flesch-Kincaid, grade level, sentence stats)
python3 <SKILL_DIR>/scripts/readability.py /tmp/page.html --json

# Validate Open Graph and Twitter Card meta tags
python3 <SKILL_DIR>/scripts/social_meta.py <url>

# Analyze internal link structure, find orphan pages
python3 <SKILL_DIR>/scripts/internal_links.py <url> --depth 1 --max-pages 20

# Extract article content and perform keyword research for LLM-driven optimization
python3 <SKILL_DIR>/scripts/article_seo.py <url> --keyword "<optional_target_keyword>" --json

# GitHub repository SEO (provider fallback: auto|api|gh)
# Auth setup (choose one):
# export GITHUB_TOKEN="ghp_xxx"   # or export GH_TOKEN="ghp_xxx"
# gh auth login -h github.com && gh auth status -h github.com
python3 <SKILL_DIR>/scripts/github_repo_audit.py --repo <owner/repo> --provider auto --json
python3 <SKILL_DIR>/scripts/github_readme_lint.py README.md --json
python3 <SKILL_DIR>/scripts/github_community_health.py --repo <owner/repo> --provider auto --json
# Benchmark/competitor inputs should be provided by LLM/web-search discovery when possible.
# If omitted, github_seo_report.py auto-derives repo-specific benchmark queries.
python3 <SKILL_DIR>/scripts/github_search_benchmark.py --repo <owner/repo> --query "<llm_or_web_query>" --provider auto --json
python3 <SKILL_DIR>/scripts/github_competitor_research.py --repo <owner/repo> --query "<llm_or_web_query>" --provider auto --top-n 6 --json
python3 <SKILL_DIR>/scripts/github_competitor_research.py --repo <owner/repo> --competitor <owner/repo> --competitor <owner/repo> --provider auto --json
python3 <SKILL_DIR>/scripts/github_traffic_archiver.py --repo <owner/repo> --provider auto --archive-dir .github-seo-data --json
python3 <SKILL_DIR>/scripts/github_seo_report.py --repo <owner/repo> --provider auto --markdown GITHUB-SEO-REPORT.md --action-plan GITHUB-ACTION-PLAN.md --json
# Optional: increase/reduce auto-derived query volume (default: 6)
# python3 <SKILL_DIR>/scripts/github_seo_report.py --repo <owner/repo> --provider auto --auto-query-max 8 --markdown GITHUB-SEO-REPORT.md --action-plan GITHUB-ACTION-PLAN.md --json
```

If a check fails due network, DNS, permissions, or API rate limits:
- Report it explicitly as an **environment limitation**, not a confirmed site issue.
- Keep confidence as `Hypothesis` for impacted categories.
- Continue with available evidence instead of stopping the audit.
- Do not enter repeated fallback loops. Retry a failed source at most once, then finalize the audit.
- Do not pivot into repeated web-search scraping loops for the same URL.

**Visual analysis** (requires Playwright — use `conda activate pentest` if available):
```bash
# Capture screenshots (desktop, laptop, tablet, mobile)
python3 <SKILL_DIR>/scripts/capture_screenshot.py <url> --all

# Analyze visual layout, above-the-fold, mobile responsiveness
python3 <SKILL_DIR>/scripts/analyze_visual.py <url> --json
```

**HTML Report Generator** — generates a self-contained interactive HTML dashboard:
```bash
# Generate full SEO report (runs scripts automatically, saves HTML to PWD)
python3 <SKILL_DIR>/scripts/generate_report.py <url>
python3 <SKILL_DIR>/scripts/generate_report.py <url> --output custom-report.html
```

### Step 5 — Delegate to Specialist Agents

For comprehensive audits, read the relevant agent file from `resources/agents/` to adopt the specialist role:

| Agent | File | Focus Area |
|-------|------|------------|
| Technical SEO | [seo-technical.md](resources/agents/seo-technical.md) | Crawlability, indexability, security, URLs, mobile, CWV, JS rendering |
| Content Quality | [seo-content.md](resources/agents/seo-content.md) | E-E-A-T assessment, content metrics, AI content detection |
| Performance | [seo-performance.md](resources/agents/seo-performance.md) | Core Web Vitals (LCP, INP, CLS), optimization recommendations |
| Schema Markup | [seo-schema.md](resources/agents/seo-schema.md) | Detection, validation, generation of JSON-LD structured data |
| Sitemap | [seo-sitemap.md](resources/agents/seo-sitemap.md) | XML sitemap validation, generation, quality gates |
| Visual Analysis | [seo-visual.md](resources/agents/seo-visual.md) | Screenshots, above-the-fold, responsiveness, layout |
| Verifier (global) | [seo-verifier.md](resources/agents/seo-verifier.md) | Deduplicate findings, suppress contradictions, and validate evidence relevance before final report |

### Step 6 — Apply Quality Gates

Reference the quality standards in `resources/references/`:

- **Content minimums**: Read [quality-gates.md](resources/references/quality-gates.md) for word counts, unique content %, title/meta requirements
- **Schema validation**: Read [schema-types.md](resources/references/schema-types.md) for active/deprecated/restricted types
- **Core Web Vitals**: Read [cwv-thresholds.md](resources/references/cwv-thresholds.md) for current metric thresholds
- **E-E-A-T framework**: Read [eeat-framework.md](resources/references/eeat-framework.md) for scoring criteria
- **Google reference**: Read [google-seo-reference.md](resources/references/google-seo-reference.md) for quick reference
- **LLM report rubric**: Read [llm-audit-rubric.md](resources/references/llm-audit-rubric.md) for mandatory evidence format, confidence labels, and output contract

### Step 6.5 — Verify Findings (All Workflows)

Before writing final reports, run verification:

```bash
python3 <SKILL_DIR>/scripts/finding_verifier.py --findings-json <raw_findings.json> --json
```

Use verified output for final report tables, not raw findings.

### Step 7 — Score and Report

Use numeric scores as guidance, not as a replacement for evidence quality and judgment.

#### Default Scoring Weights (Full Audit)

> **Canonical source of truth** — These weights are defined here and in `resources/skills/seo-audit.md`.
> Do not modify weights in individual sub-skill files; update only these two locations to keep scores consistent.

| Category | Weight |
|----------|--------|
| Technical SEO | 25% |
| Content Quality | 20% |
| On-Page SEO | 15% |
| Schema / Structured Data | 15% |
| Performance (CWV) | 10% |
| Image Optimization | 10% |
| AI Search Readiness (GEO) | 5% |

> If using `scripts/generate_report.py`, the automated dashboard uses script-level category weights defined in that script. Keep the narrative audit LLM-first and evidence-first.

### Step 8 — Mandatory Deliverables

For `seo audit`, `seo page`, and generic `perform seo analysis on <url>` flows:

1. Create `FULL-AUDIT-REPORT.md` in the current working directory at the start of the audit, then update it as evidence is collected.
2. Create `ACTION-PLAN.md` in the current working directory at the start of the audit, then update it with prioritized fixes.
3. If HTML dashboard was generated, include its exact saved path (for example `SEO-REPORT.html` or an absolute path).
4. In the final response, explicitly list generated artifacts and paths.
5. If technical checks are blocked by environment limits, still write both markdown files and include an "Environment Limitations" section.

#### Score Interpretation
| Score | Rating |
|-------|--------|
| 90-100 | Excellent |
| 70-89 | Good |
| 50-69 | Needs Improvement |
| 30-49 | Poor |
| 0-29 | Critical |

---

## Industry Detection

When running `seo plan`, detect the business type and load the matching template:

| Industry | Template File |
|----------|---------------|
| SaaS / Software | [saas.md](resources/templates/saas.md) |
| Local Service Business | [local-service.md](resources/templates/local-service.md) |
| E-commerce / Retail | [ecommerce.md](resources/templates/ecommerce.md) |
| Publisher / Media | [publisher.md](resources/templates/publisher.md) |
| Agency / Consultancy | [agency.md](resources/templates/agency.md) |
| Other / Generic | [generic.md](resources/templates/generic.md) |

**Detection signals:**
- SaaS: pricing page, feature pages, /docs, /api, trial/demo CTAs
- Local: address, phone, Google Business Profile, service area pages
- E-commerce: product pages, cart, checkout, /collections, /categories
- Publisher: article dates, author pages, /news, high content volume
- Agency: case studies, /work, /portfolio, team pages, service offerings

---

## Schema Templates

Pre-built JSON-LD templates are available in [templates.json](resources/schema/templates.json) for:
- **Common**: BlogPosting, Article, Organization, LocalBusiness, BreadcrumbList, WebSite (with SearchAction)
- **Video**: VideoObject, BroadcastEvent, Clip, SeekToAction
- **E-commerce**: ProductGroup (variants), OfferShippingDetails, Certification
- **Other**: SoftwareSourceCode, ProfilePage (E-E-A-T author pages)

---

## Validation Scripts

Two validation scripts are available for CI/CD integration:

### Pre-commit SEO Check
```bash
bash <SKILL_DIR>/scripts/pre_commit_seo_check.sh
```
Checks staged HTML files for: placeholder text in schema, title tag length, missing alt text, deprecated schema types, FID references (should be INP), meta description length.

### Schema Validator
```bash
python3 <SKILL_DIR>/scripts/validate_schema.py <file_path>
```
Validates JSON-LD blocks in HTML files: JSON syntax, @context/@type presence, placeholder text, deprecated/restricted types.

---

## Output Format

All sub-skill reports should use consistent severity levels:
- 🔴 **Critical** — Directly impacts rankings or indexing (fix immediately)
- ⚠️ **Warning** — Optimization opportunity (fix within 1 month)
- ✅ **Pass** — Meets or exceeds standards
- ℹ️ **Info** — Not applicable or informational only

Structure reports as:
1. Summary table with element, value, and severity
2. Detailed findings grouped by category
3. Actionable recommendations ordered by impact

---

## Critical Rules

1. **INP not FID** — FID was removed September 9, 2024. The sole interactivity metric is INP (Interaction to Next Paint). Never reference FID.
2. **FAQ schema is restricted** — FAQPage schema is limited to government and healthcare authority sites only (August 2023). Do NOT recommend for commercial sites.
3. **HowTo schema is deprecated** — Rich results fully removed September 2023. Never recommend.
4. **JSON-LD only** — Always use `<script type="application/ld+json">`. Never recommend Microdata or RDFa.
5. **E-E-A-T everywhere** — As of December 2025, E-E-A-T applies to ALL competitive queries, not just YMYL.
6. **Mobile-first is complete** — 100% mobile-first indexing since July 5, 2024.
7. **Location page limits** — Warning at 30+ pages, hard stop at 50+ pages. Enforce unique content requirements.
8. **AI crawler management** — Check robots.txt for GPTBot, ClaudeBot, PerplexityBot, Applebot-Extended, Google-Extended, Bytespider, CCBot.
9. **LLM-first, resilient pipeline** — Start by reading the page with `read_url_content`, then always run relevant scripts for structured evidence. Scripts are the **preferred** evidence source — use them actively. However, if any script fails (timeout, network, parsing), the LLM MUST still produce a complete analysis using its own reasoning (confidence: `Likely`). Never block a report on a single script failure.
10. **Always produce file artifacts for audit flows** — `FULL-AUDIT-REPORT.md` and `ACTION-PLAN.md` are required outputs for full/page audit requests.
11. **Bound evidence retries** — Avoid long search/retry loops. If core checks fail due DNS/network, finalize promptly with confidence labels and file outputs.
12. **Avoid redundant web fallbacks** — If direct fetch/scripts fail and one fallback also fails, stop retrying and finish the report with explicit limitations.
13. **Signal freshness tracking** — Every reference file should contain a `<!-- Updated: YYYY-MM-DD -->` comment. Flag any reference file older than 90 days for review. When Google announces algorithm changes, verify affected reference files within 7 days. Key dates to track: core updates (quarterly), schema deprecations (schema-types.md), CWV threshold changes (cwv-thresholds.md).

---

## Dependencies

### Optional Script Dependencies
- Python 3.8+
- `requests` (for network analysis scripts)
- `beautifulsoup4` (for HTML parsing scripts)
- Playwright (for `capture_screenshot.py` and `analyze_visual.py`)
  ```bash
  pip install playwright && playwright install chromium
  ```
  Or if using conda: `conda activate pentest` (if Playwright is pre-installed)

### Install Script Dependencies
```bash
pip install requests beautifulsoup4
```

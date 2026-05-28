# Skills, Agents, Scripts, and Schemas

This reference describes every moving part in the `geo-seo-claude` skill bundle. The bundle optimizes websites for Generative Engine Optimization (GEO) — making content discoverable and citable by AI search platforms (ChatGPT, Perplexity, Google AI Overviews, Gemini, Bing Copilot) — while maintaining traditional SEO foundations. It is structured as one orchestrator skill, 14 sub-skills, 5 parallel subagents, 6 Python helper scripts, and 6 JSON-LD schema templates.

See [commands-reference.md](commands-reference.md) for the full slash-command reference and [architecture.md](architecture.md) for how the parallel subagent flow works during a full audit.

---

## Orchestrator

- **geo** (`geo/SKILL.md`) — Entry point for all GEO commands. Detects business type, dispatches sub-skills for individual commands, and coordinates the three-phase full-audit flow: discovery, parallel subagent delegation, and score synthesis. Produces a composite GEO Score (0–100) weighted across six categories.

---

## Sub-skills

### geo-audit

**Purpose:** Orchestrates a full GEO + SEO audit of a website by running discovery, delegating to five parallel subagents, and aggregating their scores into a single composite GEO Score.

**Inputs:** A URL. Optionally, pre-crawled page data.

**Outputs:** `GEO-AUDIT-REPORT.md` — composite score, per-category breakdown, issue severity list (Critical / High / Medium / Low), 30-day action plan, and an appendix of pages analyzed.

**Scoring weights:**
- AI Citability 25%, Brand Authority 20%, Content E-E-A-T 20%, Technical GEO 15%, Structured Data 10%, Platform Optimization 10%

**Dependencies:** Delegates to all five subagents (`geo-ai-visibility`, `geo-platform-analysis`, `geo-technical`, `geo-content`, `geo-schema`).

See [commands-reference.md](commands-reference.md) for `/geo audit`.

---

### geo-citability

**Purpose:** Scores individual content passages on a 0–100 scale for AI citation readiness. Measures how likely an AI system is to extract and quote a passage verbatim.

**Inputs:** A URL (fetched with WebFetch).

**Outputs:** `GEO-CITABILITY-SCORE.md` — per-section scores, top citation-ready passages, weakest blocks with rewrite suggestions, and a citability coverage percentage.

**Scoring dimensions (per passage):** Answer Block Quality (30%), Self-Containment (25%), Structural Readability (20%), Statistical Density (15%), Uniqueness (10%).

**Key threshold:** Optimal AI-cited passages are 134–167 words, self-contained, fact-rich, and answer a question in the first 1–2 sentences.

See [commands-reference.md](commands-reference.md) for `/geo citability`.

---

### geo-crawlers

**Purpose:** Audits which AI crawlers can access the site by parsing `robots.txt`, meta robots tags, and HTTP `X-Robots-Tag` headers. Produces a complete access map across 14 crawlers in three tiers.

**Inputs:** A domain URL.

**Outputs:** `GEO-CRAWLER-ACCESS.md` — per-crawler status (Allowed / Blocked / Not Mentioned), AI Visibility Score, recommended `robots.txt` configuration, and JavaScript rendering assessment.

**Crawler tiers:**
- Tier 1 (search visibility): GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, PerplexityBot
- Tier 2 (broader AI ecosystem): Google-Extended, GoogleOther, Applebot-Extended, Amazonbot, FacebookBot
- Tier 3 (training-only): CCBot, anthropic-ai, Bytespider, cohere-ai

See [commands-reference.md](commands-reference.md) for `/geo crawlers`.

---

### geo-llmstxt

**Purpose:** Analyzes an existing `llms.txt` file for format compliance and completeness, or generates a new one from scratch by crawling the site. The `llms.txt` standard gives AI systems explicit guidance on site structure and key pages.

**Inputs:** A domain URL. Operates in analysis mode (file exists) or generation mode (file absent).

**Outputs (analysis mode):** `GEO-LLMSTXT-ANALYSIS.md` — format validation table, missing pages, overall llms.txt score (Completeness 40%, Accuracy 35%, Usefulness 25%).

**Outputs (generation mode):** A ready-to-deploy `llms.txt` file and `GEO-LLMSTXT-GENERATION.md` explaining page selection rationale.

**Dependencies:** `scripts/llmstxt_generator.py` provides validation and generation helpers.

See [commands-reference.md](commands-reference.md) for `/geo llmstxt`.

---

### geo-brand-mentions

**Purpose:** Scans brand presence across platforms that AI models use for entity recognition and citation decisions. Produces a Brand Authority Score based on platform-weighted presence.

**Inputs:** Brand name, domain URL, industry (gathered from the site if not provided).

**Outputs:** `GEO-BRAND-MENTIONS.md` — per-platform scores (YouTube 25%, Reddit 25%, Wikipedia/Wikidata 20%, LinkedIn 15%, Other 15%), sentiment assessment, composite Brand Authority Score, and prioritized recommendations.

**Key insight:** YouTube mention correlation with AI citation is ~0.737; Domain Rating correlation is ~0.266 (Ahrefs, December 2025 study of 75,000 brands).

**Dependencies:** `scripts/brand_scanner.py` provides the platform-check framework. Wikipedia checks use the Wikipedia API directly via Bash (web search alone produces false negatives).

See [commands-reference.md](commands-reference.md) for `/geo brands`.

---

### geo-platform-optimizer

**Purpose:** Audits readiness for each of the five major AI search platforms individually, since only 11% of domains are cited by both ChatGPT and Google AI Overviews for the same query.

**Inputs:** A URL and the site's primary topic or industry.

**Outputs:** `GEO-PLATFORM-OPTIMIZATION.md` — per-platform scores and gaps for Google AI Overviews, ChatGPT Web Search, Perplexity AI, Google Gemini, and Bing Copilot; a cross-platform priority action plan.

**Platform-specific top factors:** AIO → top-10 ranking + Q&A structure; ChatGPT → Wikipedia entity; Perplexity → Reddit presence + original research; Gemini → YouTube + Knowledge Panel; Bing Copilot → IndexNow + Bing Webmaster Tools.

See [commands-reference.md](commands-reference.md) for `/geo platforms`.

---

### geo-schema

**Purpose:** Detects, validates, and generates Schema.org structured data (JSON-LD preferred). Structured data is the primary machine-readable signal AI models use to identify and trust entities.

**Inputs:** A URL. Uses `scripts/fetch_page.py` to retrieve raw HTML including `<head>` content (WebFetch strips it).

**Outputs:** `GEO-SCHEMA-REPORT.md` — detected schemas with validation results, `sameAs` entity-linking audit, deprecated schema flags (HowTo removed Sep 2023, FAQPage restricted Aug 2023), and ready-to-paste JSON-LD code blocks.

**GEO-critical schemas:** Organization + `sameAs`, Article + Author (Person), speakable property, BreadcrumbList, WebSite + SearchAction.

**Dependencies:** `scripts/fetch_page.py` (raw HTML extraction); `schema/*.json` templates (used as generation references).

See [commands-reference.md](commands-reference.md) for `/geo schema`.

---

### geo-technical

**Purpose:** Audits eight categories of technical health with emphasis on factors that uniquely affect AI crawler visibility: server-side rendering and AI crawler access.

**Inputs:** A homepage URL plus 2–3 key inner pages.

**Outputs:** `GEO-TECHNICAL-AUDIT.md` — category scores, AI crawler access table, SSR assessment, Core Web Vitals risk (LCP / INP / CLS), security headers, and mobile optimization status.

**Scoring categories (max points):** Server-Side Rendering 15, Core Web Vitals 15, Crawlability 15, Indexability 12, Security 10, Mobile 10, Page Speed 15, URL Structure 8.

**Critical check:** AI crawlers do not execute JavaScript. A client-side SPA with no SSR renders an empty page to GPTBot, ClaudeBot, and PerplexityBot.

See [commands-reference.md](commands-reference.md) for `/geo technical`.

---

### geo-content

**Purpose:** Evaluates content quality through the E-E-A-T framework (Experience, Expertise, Authoritativeness, Trustworthiness) and measures content depth, readability, AI content indicators, and topical authority.

**Inputs:** A URL (fetched with WebFetch).

**Outputs:** `GEO-CONTENT-ANALYSIS.md` — E-E-A-T scores (25 points each), content metrics table, AI content assessment, topical authority rating, freshness assessment, and rewrite recommendations.

**Score modifiers:** Topical authority adds +10 to −5 points on top of the base 100-point E-E-A-T score.

See [commands-reference.md](commands-reference.md) for `/geo content`.

---

### geo-report

**Purpose:** Aggregates outputs from all audit sub-skills into a single client-facing deliverable written for business owners, not developers — technical findings are translated into business impact and dollar-value framing.

**Inputs:** Output files from `geo-platform-optimizer`, `geo-schema`, `geo-technical`, `geo-content`, and optionally `geo-llmstxt` and `geo-brand-mentions`.

**Outputs:** `GEO-CLIENT-REPORT.md` — executive summary, GEO Readiness Score, AI Visibility Dashboard, crawler access table, brand authority table, citability analysis, technical health summary, schema status, action plan with effort and platform impact, and a full glossary appendix. Target length: 3,000–6,000 words.

See [commands-reference.md](commands-reference.md) for `/geo report`.

---

### geo-report-pdf

**Purpose:** Generates a professionally formatted, client-ready PDF from GEO audit data using ReportLab. Includes score gauges, bar charts, and color-coded tables.

**Inputs:** Existing `GEO-AUDIT-REPORT.md` or `GEO-CLIENT-REPORT.md` files in the current directory. If a URL is passed, runs the full audit first.

**Outputs:** `GEO-REPORT-[brand].pdf` — cover page with score gauge, score breakdown with bar chart, AI platform readiness chart, crawler access table (green/red coded), findings by severity, action plan, and methodology appendix.

**Dependencies:** `scripts/generate_pdf_report.py` (requires `pip install reportlab`).

See [commands-reference.md](commands-reference.md) for `/geo report-pdf`.

---

### geo-prospect

**Purpose:** CRM-lite for managing GEO agency prospects through a five-stage sales pipeline (lead → qualified → proposal → won → lost). Persists all data in `~/.geo-prospects/prospects.json`.

**Inputs:** Domain names, contact details, status updates, and notes entered via sub-commands.

**Outputs:** Updates to `prospects.json`; audit snapshots in `~/.geo-prospects/audits/`; pipeline summary table printed to terminal.

**Key sub-commands:** `new`, `list`, `show`, `audit`, `note`, `status`, `won`, `lost`, `pipeline`.

**Dependencies:** `scripts/crm_dashboard.py` provides a rich terminal dashboard (requires `pip install rich`).

See [commands-reference.md](commands-reference.md) for `/geo prospect`.

---

### geo-proposal

**Purpose:** Auto-generates a client-ready GEO service proposal from audit data, including executive summary, score breakdown, three service tiers with pricing, ROI projection, and engagement timeline.

**Inputs:** Domain name or path to an existing audit file. Reads prospect record from `~/.geo-prospects/prospects.json` if available.

**Outputs:** `~/.geo-prospects/proposals/<domain>-proposal-<date>.md` — a complete proposal ready to send. Also updates the prospect record status to `proposal`.

**Tier recommendation logic:** Score 0–40 → Premium (€9,500/mo); 41–60 → Standard (€5,000/mo); 61–75 → Basic (€2,500/mo).

See [commands-reference.md](commands-reference.md) for `/geo proposal`.

---

### geo-compare

**Purpose:** Generates a monthly delta report comparing two GEO audits (baseline vs. current), tracking score improvements across all categories and action-item completion status.

**Inputs:** A domain name or two audit file paths. Reads files from `~/.geo-prospects/audits/` sorted by date if only domain is provided.

**Outputs:** `~/.geo-prospects/reports/<domain>-monthly-<YYYY-MM>.md` — score progress bar, before/after breakdown table, platform and crawler delta tables, action plan status, wins section, new issues discovered, and 6-month trajectory.

See [commands-reference.md](commands-reference.md) for `/geo compare`.

---

## Parallel Subagents

These five agents run simultaneously during a `/geo audit` to reduce total runtime. Each returns a structured markdown section and a category score (0–100) that feeds the composite GEO Score. See [architecture.md](architecture.md) for the parallel flow diagram.

### geo-ai-visibility

**File:** `agents/geo-ai-visibility.md`

**Role:** GEO specialist covering the four highest-weighted AI visibility dimensions.

**Dispatched when:** Phase 2 of `/geo audit` begins.

**What it does:** Scores every content block for citability (5-dimension rubric), parses `robots.txt` for 12 AI crawlers, validates `llms.txt` format and completeness, and scans brand presence on YouTube, Reddit, Wikipedia, and LinkedIn.

**Returns:** AI Visibility Score = Citability (35%) + Brand Mentions (30%) + Crawler Access (25%) + llms.txt (10%).

**Sub-skills used:** geo-citability, geo-crawlers, geo-llmstxt, geo-brand-mentions.

---

### geo-platform-analysis

**File:** `agents/geo-platform-analysis.md`

**Role:** Platform optimization specialist.

**Dispatched when:** Phase 2 of `/geo audit` begins (concurrent with other agents).

**What it does:** Evaluates readiness for each of the five AI search platforms — Google AI Overviews, ChatGPT Web Search, Perplexity AI, Google Gemini, and Bing Copilot — using platform-specific scoring rubrics and signal checks.

**Returns:** Per-platform scores (0–100 each) and a Platform Readiness Average; cross-platform synergy actions.

**Sub-skill used:** geo-platform-optimizer.

---

### geo-technical

**File:** `agents/geo-technical.md`

**Role:** Technical SEO specialist.

**Dispatched when:** Phase 2 of `/geo audit` begins (concurrent with other agents).

**What it does:** Fetches raw HTML and response headers; audits SSR vs. CSR rendering (the highest-weight check), crawlability, meta tags, security headers, Core Web Vitals risk indicators, mobile optimization, and URL structure.

**Returns:** Technical Score (0–100) with per-category breakdown; SSR severity rating (Critical / High / Medium / Low).

**Sub-skill used:** geo-technical.

---

### geo-content

**File:** `agents/geo-content.md`

**Role:** Content quality specialist.

**Dispatched when:** Phase 2 of `/geo audit` begins (concurrent with other agents).

**What it does:** Evaluates E-E-A-T across all four dimensions (25 points each), measures word count, readability (Flesch), heading structure, and internal linking, detects AI content quality signals, assesses topical authority and content freshness.

**Returns:** Content Score (0–100); E-E-A-T breakdown; AI content assessment label.

**Sub-skill used:** geo-content.

---

### geo-schema

**File:** `agents/geo-schema.md`

**Role:** Schema markup specialist.

**Dispatched when:** Phase 2 of `/geo audit` begins (concurrent with other agents).

**What it does:** Uses `fetch_page.py` to retrieve raw HTML, detects all JSON-LD / Microdata / RDFa blocks, validates each against Schema.org specifications, audits `sameAs` entity links, flags deprecated or JS-injected schemas, and generates ready-to-paste JSON-LD templates for missing schemas.

**Returns:** Schema Score (0–100); validated schema inventory; generated JSON-LD code blocks.

**Sub-skill used:** geo-schema.

---

## Python Scripts

| Script | Purpose | Used by |
|--------|---------|---------|
| `scripts/fetch_page.py` | Fetches a URL and returns structured data including raw HTML, meta tags, heading structure, word count, and parsed JSON-LD blocks. Bypasses the markdown conversion that WebFetch applies, preserving `<head>` content. | geo-schema (skill + agent), geo-technical |
| `scripts/citability_scorer.py` | Scores individual text passages for AI citation readiness using five weighted dimensions (answer quality, self-containment, structure, statistical density, uniqueness). Provides `score_passage()` as a callable function. | geo-citability |
| `scripts/brand_scanner.py` | Checks brand presence across AI-cited platforms (YouTube, Reddit, Wikipedia, LinkedIn). Provides per-platform check functions and instructions for WebFetch-based verification. Requires `requests` and `beautifulsoup4`. | geo-brand-mentions |
| `scripts/llmstxt_generator.py` | Validates an existing `llms.txt` against the spec (H1 title, blockquote description, H2 sections, absolute URLs, descriptions) and generates a new file from site crawl data. | geo-llmstxt |
| `scripts/generate_pdf_report.py` | Generates a multi-page PDF from a JSON audit data file using ReportLab. Renders score gauges, bar charts, color-coded tables, and an action plan. Accepts the JSON file path as a CLI argument or via stdin. Requires `reportlab`. | geo-report-pdf |
| `scripts/crm_dashboard.py` | Renders a rich terminal dashboard for the prospect CRM. Reads `~/.geo-prospects/prospects.json` and displays pipeline stages, MRR, and prospect detail views. Requires `rich`. | geo-prospect |

---

## Schema Templates

These JSON-LD files in `schema/` serve as generation references when `geo-schema` or `geo-report` need to produce ready-to-paste structured data. All placeholders follow the pattern `YOUR_FIELD_NAME` or `REPLACE_WITH_VALUE`.

| Template | When to use |
|----------|-------------|
| `schema/organization.json` | Any business site; provides the full Organization type with `sameAs` links to Wikipedia, Wikidata, LinkedIn, YouTube, GitHub, and Crunchbase, plus `knowsAbout` for entity topic signals. |
| `schema/local-business.json` | Businesses with a physical location; extends Organization with address, `geo` coordinates, opening hours, service area, aggregate rating, and an offer catalog. |
| `schema/article-author.json` | Publisher and blog pages; Article type with a fully populated Person author (credentials, `sameAs`, `alumniOf`, `knowsAbout`) and a `speakable` specification for AI assistant readability. |
| `schema/product-ecommerce.json` | E-commerce product pages; Product type with Offer (including shipping details and return policy), AggregateRating, and individual Review entries. |
| `schema/software-saas.json` | SaaS product pages; SoftwareApplication type with tiered AggregateOffer pricing, `featureList`, screenshot, and `sameAs` links to G2, Capterra, ProductHunt, and GitHub. |
| `schema/website-searchaction.json` | Every site's homepage; WebSite type with a SearchAction `potentialAction` to enable sitelinks search box and provide AI systems with the site's search endpoint. |

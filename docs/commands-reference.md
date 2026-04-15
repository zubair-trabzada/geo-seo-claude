# Commands Reference

This file documents every command in the `geo-seo-claude` skill bundle. Commands are invoked inside Claude Code using the `/geo` prefix. The main skill at `geo/SKILL.md` acts as a router: it reads the first argument after `/geo` and delegates to the matching sub-skill under `skills/`. All commands accept a URL as their primary argument; CRM commands operate on domain names or prospect IDs instead. Every command that produces a score references the weighting model described in [scoring-methodology.md](scoring-methodology.md). The parallel subagent architecture used by `/geo audit` is described in [architecture.md](architecture.md).

---

## Command categories

**Audit** — full-site and focused analysis

| Command | Description |
|---------|-------------|
| `/geo audit <url>` | Full GEO + SEO audit with parallel subagents |
| `/geo quick <url>` | 60-second GEO visibility snapshot |
| `/geo citability <url>` | Score a single page for AI citation readiness |
| `/geo crawlers <url>` | Check AI crawler access via robots.txt and meta tags |
| `/geo llmstxt <url>` | Analyze an existing llms.txt or generate one from scratch |
| `/geo brands <url>` | Scan brand mentions across AI-cited platforms |
| `/geo platforms <url>` | Platform-specific readiness scores (AIO, ChatGPT, Perplexity, Gemini, Copilot) |

**Diagnostics** — targeted technical and content checks

| Command | Description |
|---------|-------------|
| `/geo schema <url>` | Detect, validate, and generate Schema.org structured data |
| `/geo technical <url>` | Technical SEO audit with GEO-specific checks |
| `/geo content <url>` | Content quality and E-E-A-T assessment |

**Reports** — client-ready deliverables

| Command | Description |
|---------|-------------|
| `/geo report <url>` | Generate a client-ready GEO report in Markdown |
| `/geo report-pdf <url>` | Generate a professional PDF report with charts and visualizations |

**CRM** — prospect and client pipeline management

| Command | Description |
|---------|-------------|
| `/geo prospect <cmd>` | Manage prospects through the sales pipeline |
| `/geo proposal <domain>` | Auto-generate a client proposal from audit data |
| `/geo compare <domain>` | Monthly delta report showing score improvements |

---

## /geo audit

Performs a comprehensive GEO + SEO audit of a website using five parallel subagents.

**Usage**

```
/geo audit https://example.com
```

**What it does**

- Phase 1 (sequential): fetches the homepage, detects business type (SaaS, Local, E-commerce, Publisher, Agency), and crawls up to 50 pages from the sitemap or internal links.
- Phase 2 (parallel): delegates to five specialized subagents simultaneously — AI visibility, platform analysis, technical SEO, content E-E-A-T, and schema markup. See [architecture.md](architecture.md) for the subagent flow.
- Phase 3 (sequential): aggregates subagent scores into a weighted composite GEO Score (0–100). See [scoring-methodology.md](scoring-methodology.md) for the weighting formula.
- Classifies every issue by severity: Critical, High, Medium, or Low.
- Produces a 30-day action plan with weekly themes.

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<url>` | Yes | Homepage URL of the site to audit |

**Output**

Writes `GEO-AUDIT-REPORT.md` to the working directory. Contains: executive summary, score breakdown table, per-category deep dives, issue list by severity, quick wins, and a week-by-week 30-day action plan. Inline summary is also printed to the terminal.

**When to use it**

Run this first for any new client or site; it is the entry point for all other analysis.

---

## /geo quick

Delivers a 60-second GEO visibility snapshot without writing any output file.

**Usage**

```
/geo quick https://example.com
```

**What it does**

- Fetches the homepage and a small sample of key pages.
- Runs a lightweight pass across the main GEO signals: AI crawler access, llms.txt presence, schema on the homepage, and a rough citability read on the hero content.
- Produces an approximate GEO score and a short list of the highest-impact gaps.
- Feeds directly into `/geo prospect audit` when called from the CRM workflow.

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<url>` | Yes | URL to snapshot |

**Output**

Inline terminal summary only — no file is written. Score is stored in the prospect record when invoked via `/geo prospect audit`.

**When to use it**

Use this for a fast qualification check before committing to a full audit, or when the `/geo prospect audit` subcommand calls it automatically.

---

## /geo citability

Scores a single page for AI citation readiness using a five-dimension rubric.

**Usage**

```
/geo citability https://example.com/blog/my-article
```

**What it does**

- Fetches the page and segments content into blocks at each H2/H3 boundary.
- Scores each block across: answer block quality (30%), passage self-containment (25%), structural readability (20%), statistical density (15%), and uniqueness/original data (10%).
- Identifies the top three strongest and the three weakest blocks.
- Generates specific rewrite suggestions — including a suggested opening sentence — for every block scoring below 60. See [scoring-methodology.md](scoring-methodology.md) for the rubric detail.

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<url>` | Yes | URL of the specific page to score |

**Output**

Writes `GEO-CITABILITY-SCORE.md`. Contains: overall citability score, weighted score table, strongest/weakest block analysis with quoted excerpts, rewrite suggestions, and a per-section score table.

**When to use it**

Use this on any content page before publishing, or to prioritize which existing pages to rewrite for AI citation.

---

## /geo crawlers

Analyzes which AI crawlers can access the site and provides a recommended robots.txt configuration.

**Usage**

```
/geo crawlers https://example.com
```

**What it does**

- Fetches and parses `robots.txt`, mapping every User-agent directive to the 14 known AI crawlers.
- Checks a sample of key pages for `<meta name="robots">` overrides and `X-Robots-Tag` HTTP headers.
- Checks for the presence of `/llms.txt` and `/.well-known/ai-plugin.json`.
- Assesses whether key content requires JavaScript rendering (AI crawlers do not execute JS).
- Scores crawler access in three tiers: Tier 1 (ChatGPT, Claude, Perplexity — critical for AI search), Tier 2 (Gemini, Copilot, Apple Intelligence, Meta AI), and Tier 3 (training-only crawlers).

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<url>` | Yes | Domain root URL |

**Output**

Writes `GEO-CRAWLER-ACCESS.md`. Contains: access summary table per crawler, an AI visibility score (0–100), critical issues list, and a complete ready-to-paste robots.txt block configured for maximum AI visibility.

**When to use it**

Use this as a quick standalone check when a client reports they are not appearing in AI search results, or to verify a robots.txt change before deploying.

---

## /geo llmstxt

Analyzes an existing `llms.txt` file for quality, or generates a new one from scratch if none exists.

**Usage**

```
/geo llmstxt https://example.com
```

**What it does**

- Fetches `https://example.com/llms.txt` and `llms-full.txt` and checks HTTP status.
- **Analysis mode** (file exists): validates format (H1 title, blockquote description, H2 sections, absolute URLs, entry descriptions, Key Facts, Contact section); scores completeness (40%), accuracy (35%), and usefulness (25%); identifies important pages missing from the file.
- **Generation mode** (file absent): crawls the sitemap and homepage, prioritizes pages by type, writes 10-30 word descriptions for each selected page, gathers key business facts, and assembles a complete `llms.txt` ready to deploy.

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<url>` | Yes | Domain root URL |

**Output**

- Analysis mode: writes `GEO-LLMSTXT-ANALYSIS.md` with validation results, missing pages, and a suggested updated file.
- Generation mode: writes the ready-to-deploy `llms.txt` file and a brief `GEO-LLMSTXT-GENERATION.md` summarizing prioritization decisions.

**When to use it**

Use this on any site to either validate an existing `llms.txt` or produce a new one. Fewer than 5% of sites had an `llms.txt` as of early 2026, making it an accessible quick win.

---

## /geo brands

Scans brand mentions across the platforms AI systems rely on for entity recognition and citation decisions.

**Usage**

```
/geo brands https://example.com
```

**What it does**

- Checks brand presence on YouTube (channel existence, subscriber count, third-party video mentions), Reddit (thread volume, sentiment, official presence, subreddit), Wikipedia/Wikidata (article existence, Wikidata Q-number, quality class), and LinkedIn (company page, follower count, post frequency).
- Uses the Wikipedia API directly (`en.wikipedia.org/w/api.php`) to avoid false negatives from web search.
- Also scans supplementary platforms: Quora, Stack Overflow, GitHub, Hacker News, and press/news.
- Calculates a composite Brand Authority Score: YouTube 25%, Reddit 25%, Wikipedia/Wikidata 20%, LinkedIn 15%, other platforms 15%. See [scoring-methodology.md](scoring-methodology.md).

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<url>` | Yes | Domain URL (brand name is inferred from the site) |

**Output**

Writes `GEO-BRAND-MENTIONS.md`. Contains: Brand Authority Score (0–100), per-platform breakdown tables, sentiment assessment, competitive context table (if competitors are identified), and prioritized recommendations grouped by time horizon (week 1–2, month 1–3, month 3–12).

**When to use it**

Use this when a site has technically sound content but is not appearing in AI-generated recommendations, or as part of an entity-building strategy.

---

## /geo platforms

Audits readiness for each major AI search platform individually and produces per-platform scores.

**Usage**

```
/geo platforms https://example.com
```

**What it does**

- Runs a separate checklist and scoring rubric for each of five platforms: Google AI Overviews, ChatGPT Web Search, Perplexity AI, Google Gemini, and Bing Copilot.
- Google AIO checklist covers: top-10 organic ranking, question-based headings, direct answer structure, tables, FAQ sections, statistics with attribution, author bylines, and publication dates.
- ChatGPT checklist covers: Wikipedia/Wikidata entity, Bing index coverage, Reddit mentions, YouTube presence, entity consistency, and content comprehensiveness.
- Perplexity checklist covers: Reddit presence, forum mentions, content freshness, original research, quotable paragraphs, and multi-source claim validation.
- Gemini checklist covers: Google Knowledge Panel, Google Business Profile, YouTube strategy, Schema.org markup, and Google ecosystem presence.
- Copilot checklist covers: Bing Webmaster Tools, IndexNow implementation, LinkedIn page, meta descriptions, and page load speed.

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<url>` | Yes | Homepage URL of the site |

**Output**

Writes `GEO-PLATFORM-OPTIMIZATION.md`. Contains: an overall combined score, per-platform score table, per-platform gap analysis with specific actions, and a prioritized action plan (quick wins, medium-term, strategic). See [scoring-methodology.md](scoring-methodology.md) for platform weight in the composite score.

**When to use it**

Use this when you need to know which specific AI platforms a site is underperforming on, or to build a platform-targeted optimization roadmap.

---

## /geo schema

Detects all structured data on a site, validates it against Schema.org specifications, and generates ready-to-paste JSON-LD blocks for missing or incomplete schemas.

**Usage**

```
/geo schema https://example.com
```

**What it does**

- Fetches raw HTML using `fetch_page.py` (not WebFetch, which strips `<head>` content) to extract all JSON-LD, Microdata, and RDFa blocks.
- Validates each schema: JSON syntax, valid `@type`, required properties, recommended properties, `sameAs` links, URL validity, nesting, and whether the schema is server-rendered or JS-injected.
- Checks for GEO-critical schema types: Organization, LocalBusiness, Article with Author, Product, FAQPage, SoftwareApplication, WebSite with SearchAction, and BreadcrumbList.
- Audits the `sameAs` property against a priority list of 14 platforms (Wikipedia, Wikidata, LinkedIn, YouTube, Twitter/X, GitHub, Crunchbase, etc.).
- Generates complete JSON-LD code blocks using the `@graph` pattern for any missing or incomplete schemas. See [scoring-methodology.md](scoring-methodology.md) for how schema score feeds the composite GEO Score.

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<url>` | Yes | URL of the page or domain to audit |

**Output**

Writes `GEO-SCHEMA-REPORT.md`. Contains: schema score (0–100), detected schemas table, per-property validation results, missing schema list, sameAs audit table, and ready-to-paste JSON-LD code blocks with implementation notes.

**When to use it**

Use this to give a developer team a self-contained implementation ticket, or to verify schema quality after a CMS migration.

---

## /geo technical

Performs a technical SEO audit across eight categories with special emphasis on server-side rendering and AI crawler access.

**Usage**

```
/geo technical https://example.com
```

**What it does**

- Crawlability (15 pts): robots.txt validity, AI crawler access for 11 named bots, XML sitemap presence and validity, crawl depth, noindex directives.
- Indexability (12 pts): canonical tags, duplicate content (www/HTTP/trailing-slash), pagination, hreflang.
- Security (10 pts): HTTPS enforcement, HSTS, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, CSP.
- URL structure (8 pts): clean readable URLs, logical hierarchy, redirect chains, parameter handling.
- Mobile optimization (10 pts): viewport meta tag, responsive layout, tap target sizing, font legibility.
- Core Web Vitals (15 pts): LCP < 2.5s, INP < 200ms, CLS < 0.1 using 2026 thresholds.
- Server-side rendering (15 pts): compares `curl` output to rendered DOM; flags client-rendered content that AI crawlers cannot read.
- Page speed and server performance (15 pts): TTFB, page weight, image optimization, JS bundle size, compression, caching, CDN. See [scoring-methodology.md](scoring-methodology.md) for how the technical score feeds the composite.

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<url>` | Yes | Domain root URL |

**Output**

Writes `GEO-TECHNICAL-AUDIT.md`. Contains: technical score (0–100), per-category score table with Pass/Warn/Fail status, AI crawler access table, critical issues list, warnings, and recommendations.

**When to use it**

Use this when a site's content is strong but AI visibility is poor, or to produce a developer-facing remediation checklist.

---

## /geo content

Evaluates content quality through the E-E-A-T framework (Experience, Expertise, Authoritativeness, Trustworthiness) and assesses AI citability and topical authority.

**Usage**

```
/geo content https://example.com
```

**What it does**

- Scores each of the four E-E-A-T dimensions on a 25-point scale: Experience (first-person accounts, original data, case studies), Expertise (author credentials, technical depth, methodology, data-backed claims), Authoritativeness (inbound citations, press mentions, awards, Wikipedia presence), Trustworthiness (contact info, privacy policy, HTTPS, editorial standards, accurate claims).
- Applies a topical authority modifier: +10 for 20+ pages with strong clustering, down to −5 for fewer than 5 pages on the topic.
- Assesses content freshness for each page (< 3 months through no-date/24+ months).
- Flags low-quality AI-generated content patterns (generic phrasing, no original insight, hedging overload) and identifies high-quality signals.
- Checks word count benchmarks per page type and paragraph structure for AI extraction. See [scoring-methodology.md](scoring-methodology.md) for how content score feeds the composite.

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<url>` | Yes | Domain root URL (analyzes homepage plus key content pages) |

**Output**

Writes `GEO-CONTENT-ANALYSIS.md`. Contains: content score (0–100), E-E-A-T breakdown table, pages-analyzed table, detailed findings per dimension, content quality issues with rewrite suggestions, AI content concerns, freshness assessment, most and least citable passages, content gap recommendations, and E-E-A-T improvement steps.

**When to use it**

Use this when a site has good technical fundamentals but is not being cited by AI systems, indicating a content quality problem.

---

## /geo report

Aggregates outputs from all audit skills into a single professional, client-facing Markdown report.

**Usage**

```
/geo report https://example.com
```

**What it does**

- Reads existing `GEO-*.md` audit files from the working directory; runs missing audits automatically if needed.
- Calculates a composite GEO Readiness Score: AI Platform Readiness 25%, Content E-E-A-T 25%, Technical Foundation 20%, Schema 15%, Brand Authority 15%. See [scoring-methodology.md](scoring-methodology.md).
- Translates all technical findings into business-impact language aimed at owners and marketing leaders, not developers.
- Produces 12 structured sections: executive summary, score dashboard, AI visibility dashboard (per platform), AI crawler access table, brand authority analysis, citability analysis (top 5 / bottom 5 pages), technical health summary, schema status, llms.txt status, prioritized action plan (quick wins / medium / strategic), competitor comparison (if competitors were analyzed), and glossary appendix.
- Includes conservative traffic and revenue impact estimates tied to score improvements.

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<url>` | Yes | Domain URL; existing audit files in the working directory are consumed automatically |

**Output**

Writes `GEO-CLIENT-REPORT.md`. The report is 3,000–6,000 words, self-contained, and ready to deliver without further editing.

**When to use it**

Use this to produce the final deliverable after running the full audit suite, or at the end of each monthly engagement cycle.

---

## /geo report-pdf

Converts GEO audit data into a professionally formatted PDF with charts, score gauges, and color-coded tables.

**Usage**

```
/geo report-pdf https://example.com
```

**What it does**

- Checks the working directory for existing `GEO-CLIENT-REPORT.md` or `GEO-AUDIT-REPORT.md`; if none are found, runs a full audit first.
- Parses the Markdown report to extract scores, platform readiness numbers, crawler status, findings, and action items.
- Assembles the data into the JSON schema expected by the PDF generation script.
- Calls `python3 ~/.claude/skills/geo/scripts/generate_pdf_report.py` (requires `pip install reportlab`).
- The PDF uses US Letter size with a navy/blue/coral color palette; score gauges use traffic-light colors (green 80+, blue 60–79, yellow 40–59, red below 40).

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<url>` | Yes | Domain URL; used to locate or generate audit data |

**Output**

Writes `GEO-REPORT-<brand>.pdf` to the working directory. The PDF contains: cover page with score gauge, executive summary, score breakdown bar chart, AI platform readiness horizontal bar chart, crawler access color-coded table, key findings by severity, prioritized action plan, and a methodology/glossary appendix. File path and size are reported on completion.

**When to use it**

Use this when the deliverable needs to be emailed directly to a client who expects a polished document rather than a Markdown file.

---

## /geo prospect

A CRM-lite pipeline manager for tracking prospects and clients from initial discovery through contract.

**Usage**

```
/geo prospect new <domain>
/geo prospect list [<status>]
/geo prospect show <id-or-domain>
/geo prospect audit <id-or-domain>
/geo prospect note <id-or-domain> "<text>"
/geo prospect status <id-or-domain> <new-status>
/geo prospect won <id-or-domain> <monthly-value>
/geo prospect lost <id-or-domain> "<reason>"
/geo prospect pipeline
```

**What it does**

- Stores all prospect data in `~/.geo-prospects/prospects.json` as persistent JSON records containing ID, company, domain, status, GEO score, audit file path, proposal file path, monthly contract value, and timestamped notes.
- Tracks five pipeline stages: `lead`, `qualified`, `proposal`, `won`, `lost`.
- `prospect audit` calls `/geo quick` and saves the resulting score to the prospect record.
- `prospect pipeline` prints a revenue-focused summary showing committed MRR, pipeline value, and suggested next actions per record.
- All subcommands print a confirmation and the current prospect status to the terminal; no external files are written except audit snapshots and proposals.

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<cmd>` | Yes | Subcommand: `new`, `list`, `show`, `audit`, `note`, `status`, `won`, `lost`, `pipeline` |
| `<id-or-domain>` | Contextual | Prospect ID (e.g., `PRO-001`) or domain name |
| `<status>` | For `status`, `list` | Pipeline stage: `lead`, `qualified`, `proposal`, `won`, `lost` |
| `<monthly-value>` | For `won` | Numeric monthly contract value |
| `"<text>"` | For `note`, `lost` | Free-text note or lost reason |

**Output**

Updates `~/.geo-prospects/prospects.json`. Audit snapshots saved to `~/.geo-prospects/audits/`. Terminal output for all subcommands.

**When to use it**

Use this to manage an ongoing GEO agency sales pipeline and track client history across sessions.

---

## /geo proposal

Auto-generates a fully customized, client-ready GEO service proposal from audit data.

**Usage**

```
/geo proposal <domain>
/geo proposal <domain> --tier basic|standard|premium --client-name "Name" --monthly EUR
```

**Examples**

```
/geo proposal example.com
/geo proposal example.com --tier standard --client-name "Acme Corp"
/geo proposal ~/.geo-prospects/audits/example.com-2026-03-12.md
```

**What it does**

- Loads the most recent audit file from `~/.geo-prospects/audits/<domain>*.md` (or runs `/geo quick` if none exists).
- Selects a recommended service tier based on GEO score: 0–40 → Premium, 41–60 → Standard, 61–75 → Basic.
- Populates a 12-section proposal template: executive summary, market context tables, audit findings, three-tier service packages with pricing (Basic €2,500/mo, Standard €5,000/mo, Premium €9,500/mo), ROI projection table, six-month engagement timeline, investment summary, and terms.
- Updates the prospect record status to `proposal` and saves the proposal file path.

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<domain>` | Yes | Domain name or path to an audit file |
| `--tier` | No | Force a specific tier instead of using score-based recommendation |
| `--client-name` | No | Override the auto-detected company name |
| `--monthly` | No | Override the estimated monthly contract value |

**Output**

Writes `~/.geo-prospects/proposals/<domain>-proposal-<date>.md`. Prints confirmation with the recommended package and price. The proposal is ready to send without editing.

**When to use it**

Use this immediately after a prospect audit when the GEO score indicates a clear sales opportunity (score below 75).

---

## /geo compare

Generates a monthly delta report comparing a baseline audit to a current audit, showing score improvements to the client.

**Usage**

```
/geo compare <domain>
/geo compare <baseline-file> <current-file>
/geo compare <domain> --month march-2026
```

**What it does**

- Locates audit files in `~/.geo-prospects/audits/` matching the domain; uses the oldest as baseline and the newest as current. If only one file exists, runs a fresh quick audit as the current snapshot.
- Extracts overall GEO score, all six category scores, all five platform scores, and AI crawler status from both files.
- Calculates deltas and assigns trend symbols (▲▲ strong improvement, ▲ improvement, ── unchanged, ▼ decline, ▼▼ significant decline).
- Tracks completion status of quick wins, medium-term, and strategic action items.
- Includes a six-month trajectory table and a conservative business impact estimate (AI citation likelihood change, crawler coverage, estimated traffic value).

**Inputs**

| Argument | Required | Description |
|----------|----------|-------------|
| `<domain>` | Yes (or two file paths) | Domain name, or explicit paths to baseline and current audit files |
| `--month` | No | Month label for the report filename |

**Output**

Writes `~/.geo-prospects/reports/<domain>-monthly-<YYYY-MM>.md`. Prints a summary to the terminal showing score change, quick wins completion rate, new issues found, and whether the six-month target is on track.

**When to use it**

Run this on the first of each month for every active client to generate the progress report that justifies the retainer.

---

## Discrepancies

The following discrepancies were found between `geo/SKILL.md` and the `skills/` directory:

- **`/geo quick`**: Listed in `geo/SKILL.md` and referenced throughout the codebase (by `geo-prospect` and `geo-compare`), but there is no `skills/geo-quick/SKILL.md`. The quick-scan behavior is documented only through the orchestration instructions in `geo/SKILL.md` and the `geo-prospect` skill. This command is documented above based on those references.
- **`/geo page`**: Listed in `geo/SKILL.md`'s quick reference table (as `/geo page <url>` — deep single-page GEO analysis) and in the output files table (produces `GEO-PAGE-ANALYSIS.md`), but there is no `skills/geo-page/SKILL.md`. No implementation exists. This command is **not documented** in the reference above because there is no skill file to draw from.
- **`/geo quick` in original `docs/commands-reference.md`**: The old table listed `/geo quick` but `geo/SKILL.md` does not list it in the sub-skills table (only in the quick reference table). It is referenced as a real behavior in the prospect and compare skills, so it is retained above.

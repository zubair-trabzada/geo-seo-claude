---
name: geo-citation-pipeline
description: >
  End-to-end AI crawler discovery → citation pipeline. Stitches geo-crawlers,
  geo-citability, geo-schema, and geo-llmstxt into a single 5-stage closed loop:
  (1) AI crawler robots audit, (2) AI-friendly internal-link wiring,
  (3) AI-training authority backlink check, (4) on-page GEO element compliance,
  (5) rapid-indexing channels (IndexNow / Google URL Inspection / Bing Webmaster
  / sitemap lastmod), and (6) preferred-answer verification across 6 AI engines.
  Use when user says "pipeline", "citation pipeline", "spider pipeline", "AI
  crawl loop", "preferred answer", "/geo pipeline", or asks to wire a page so
  AI engines actually cite it as the first answer.
version: 1.0.0
author: geo-seo-claude-plus
tags: [geo, pipeline, crawlers, citability, indexing, preferred-answer]
allowed-tools: Read, Grep, Glob, Bash, WebFetch, Write
---

# GEO Citation Pipeline Skill

## Core Insight

GEO step 3 — "guiding the AI spider to a preferred-answer outcome" — is not a single action. It is a closed loop of five sequential gates: **discovery → in-site navigation → off-site authority → on-page extractability → rapid indexing**, followed by a verification step that confirms the AI engine actually picked the page as its preferred citation. If any of the five gates fails, the entire chain breaks: a crawl-blocked page is invisible no matter how citable it is; an isolated orphan page with no internal links may be crawled but never resurfaced; a perfectly cited page with no IndexNow ping may take 4–6 weeks to appear in a Perplexity answer instead of 24 hours.

A 2025 Originality.ai longitudinal study tracking 1,200 newly published B2B pages across six AI engines found that pages with all five gates green appeared in AI citations within a median of **7 days**, while pages missing any single gate had a median of **53 days** — a 7.5× slowdown for each missing gate. The takeaway: you don't optimize one stage at a time; you wire all five and treat any single failure as a pipeline outage.

This skill is an **orchestrator**, not a re-implementer. Stages 1, 4, and parts of 5 inherit data from existing skills (`geo-crawlers`, `geo-citability`, `geo-schema`, `geo-llmstxt`). Stages 2 and 3 are new checks introduced by this skill. Stage 6 is the verification snapshot that closes the loop.

---

## How to Use This Skill

1. Take a URL as input (typically a P0 piece scheduled by `geo-intent-matrix`).
2. Run the 7-step workflow below.
3. Roll up the 5 stage gates into a single `PIPELINE_READY / PIPELINE_DEGRADED / BLOCKED` verdict.
4. Emit `~/.geo-prospects/pipelines/<domain>-<slug>-<YYYY-MM-DD>.md` with a remediation plan.

---

## Pipeline Architecture (5 Stages)

```
       Discovery        Navigation        Off-site authority      On-page extract    Rapid indexing       Verify
   ┌──────────────┐  ┌───────────────┐  ┌───────────────────┐  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐
   │ Stage 1      │  │ Stage 2       │  │ Stage 3           │  │ Stage 4      │  │ Stage 5        │  │ Stage 6      │
   │ AI crawler   │→ │ Internal-link │→ │ AI-training       │→ │ GEO on-page  │→ │ IndexNow /     │→ │ Preferred-   │
   │ robots audit │  │ wiring        │  │ authority         │  │ compliance   │  │ URL Inspection │  │ answer       │
   │              │  │               │  │ backlinks         │  │              │  │ / Bing / sitm. │  │ snapshot     │
   └──────────────┘  └───────────────┘  └───────────────────┘  └──────────────┘  └────────────────┘  └──────────────┘
   inherits          new check          new check              inherits          new check          new check
   geo-crawlers                                                geo-citability                       (6 AI engines)
                                                               + geo-schema
```

Any single FAIL drops the pipeline to **PIPELINE_DEGRADED**. Two or more FAILs (or any Stage 1 / Stage 4 FAIL) drops it to **BLOCKED**.

### Stage 1: AI Crawler Robots Audit

**Purpose:** Confirm AI engines are even allowed to reach the URL.

**Inherits from:** `geo-crawlers` (full crawler reference table is maintained there; do not duplicate).

**Pipeline-specific checks:**

| Check | PASS | FAIL |
|---|---|---|
| Per-URL robots check (not just root) | URL is allowed for all 5 critical crawlers (GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, Google-Extended) | Any critical crawler is blocked at the URL path |
| `noindex` meta + `X-Robots-Tag` header | Both absent or set to `index, follow` | Either declares `noindex` |
| Server response | `200 OK` on first hit, no redirect chain > 1 hop | 4xx / 5xx, or > 1 redirect hop |
| Render mode | Server-rendered or pre-rendered (key content visible in raw HTML response) | Content only appears after JS execution (most AI crawlers do not execute JS) |

### Stage 2: AI-Friendly Internal-Link Wiring

**Purpose:** Make sure once the crawler arrives, it can find the page from authoritative entry points and the anchor text tells the engine what the page is about.

**This is a new check.** No existing skill audits internal-link semantics from the GEO-extraction angle.

| Check | PASS | FAIL |
|---|---|---|
| Click depth from homepage | ≤ 3 clicks | > 3 clicks |
| Inbound internal links | ≥ 3 distinct internal pages link to this URL | 0–2 inbound internal links |
| Anchor-text intent triggers | ≥ 50 % of inbound anchors contain an intent trigger word matching the page's `intent:` value (e.g., for a Procedural page, anchors like "how to …", "tutorial", "guide", "steps to …") | < 50 % anchors contain intent triggers; or anchors are generic ("click here", "read more", brand name only) |
| Topical-cluster hub link | At least one inbound link comes from a recognized hub page (the topic-level pillar or sitemap-listed category page) | Page is orphaned from any hub |
| Canonical | `<link rel="canonical">` points to itself (not to a parent page) | Canonical missing, or points elsewhere |

**Intent trigger lookup:** see `geo-intent-matrix` Intent → Content-Form table for the canonical vocabulary per intent.

### Stage 3: AI-Training Authority Backlink Check

**Purpose:** Off-site backlinks matter for AI citation, but **only from domains that are known to appear in AI training corpora or RAG retrieval indexes**. A backlink from a random DR-30 blog has near-zero impact on AI citation; a single unlinked mention on Wikipedia or a high-engagement Reddit thread has measurable impact.

**This is a new check.** `geo-brand-mentions` covers brand presence broadly; this stage narrows to backlinks (linked + unlinked references) at the URL level, scoped to AI-training source domains.

**AI-training source domain whitelist (Tier A and Tier B):**

| Tier | Domains | Why they matter |
|---|---|---|
| Tier A — Confirmed in major AI training sets | `en.wikipedia.org`, `reddit.com`, `stackoverflow.com`, `github.com`, `quora.com`, `medium.com`, `wikidata.org`, `youtube.com` (transcripts) | Documented in published Common Crawl analyses; high retrieval frequency by Perplexity, Gemini, ChatGPT |
| Tier B — High retrieval frequency in RAG / live search | `news.ycombinator.com`, `substack.com`, major industry trade press (e.g., `techcrunch.com`, `theverge.com`, `arstechnica.com`, `36kr.com`, `huxiu.com` for CN), `g2.com`, `capterra.com`, `trustpilot.com`, `linkedin.com` (posts and articles) | Frequently surfaced by Perplexity and ChatGPT live search; high authority for Gemini |

**Pipeline checks:**

| Check | PASS | FAIL |
|---|---|---|
| Tier A backlinks or mentions | ≥ 1 mention (linked or unlinked) of the URL or its core entity on any Tier A domain | 0 Tier A mentions |
| Tier B backlinks or mentions | ≥ 3 mentions across Tier B domains | < 3 Tier B mentions |
| Recency | At least one Tier A or Tier B mention within the last 12 months | All mentions older than 12 months |
| Anchor / context relevance | At least one mention contains the page's primary topic phrase verbatim or as a clear paraphrase | All mentions are tangential brand drops with no topical context |

### Stage 4: On-Page GEO Element Compliance

**Purpose:** Once the engine fetches the page, can it actually extract a 134–167 word self-contained answer block? Are structured-data signals in place?

**Inherits from:** `geo-citability` (citability rubric) and `geo-schema` (schema validation). This skill does not re-implement scoring; it consumes the existing per-page scores and applies pipeline thresholds.

| Check | PASS | FAIL |
|---|---|---|
| `geo-citability` page-level Citability Score | ≥ 70 | < 70 |
| Top answer block length | At least one passage in the 134–167 word optimal window with a definition / answer-first opening | No qualifying passage |
| Required schema present | Schema types match the page intent: Definitional → `DefinedTerm` or `Article`; Comparative → `Table` + `Article`; Procedural → `HowTo`; Causal → `Article` + `Claim` / `CreativeWork` with named author. Plus always: `Organization` or `Person` author with `sameAs` | Required schema for intent absent or malformed |
| `geo-schema` validation result | All schema blocks validate without errors | Any schema block has errors |
| Form-binding compliance | Page form matches the intent → form contract from `geo-intent-matrix` (Comparative has a table, Procedural has ordered list, etc.) | Form mismatch |

### Stage 5: Rapid-Indexing Channels

**Purpose:** Push the URL through every available expedited-discovery channel so AI engines (which retrieve from search indexes more than they re-crawl directly) see it within hours, not weeks.

**This is a new check** (orchestrated, not previously checked end-to-end).

| Channel | Check | PASS | FAIL |
|---|---|---|---|
| **IndexNow** | API ping issued for the URL within 24 h of publish | Recent successful ping recorded; valid `<host>-<key>.txt` file at site root | No ping issued; or key file missing / 404 |
| **Google URL Inspection / Indexing API** | URL submitted via Search Console URL Inspection (manual) or Indexing API (for `JobPosting` / `BroadcastEvent` only — otherwise note manual submission required) | Submission timestamp ≤ 7 days old; URL marked Indexed in Search Console | Not submitted or status `Discovered – currently not indexed` / `Crawled – currently not indexed` |
| **Bing Webmaster Tools** | URL submitted via Bing's URL submission API | Submission timestamp ≤ 7 days old | Not submitted |
| **Sitemap `lastmod`** | `sitemap.xml` entry exists for the URL with `<lastmod>` ≥ publish date and ≤ 24 h drift | Entry present, `lastmod` recent and accurate | Entry missing, or `lastmod` stale (> 7 days drift from actual change) |
| **llms.txt freshness** | URL appears in `/llms.txt` if it is a P0 piece | URL listed under the appropriate section | URL missing from `llms.txt` (P0 only — P1/P2 are warning, not FAIL) |

Stage 5 PASS requires **4 of 5 channels PASS** (the Google Indexing API is optional for most content types and a manual URL Inspection submission counts as PASS).

### Stage 6: Preferred-Answer Verification (6 AI Engines)

**Purpose:** Close the loop. Did the engines actually cite this page when asked the question this page was written to answer?

**This is a new check.** Distinct from `geo-competitor-citation` (which is a comparative gap analysis); this is a single-URL pickup check.

**Probe construction:**

1. Take the page's `intent:` and primary question (recorded by `geo-intent-matrix` at planning time).
2. Issue that exact question to each of the 6 engines:
   - ChatGPT (search mode)
   - Claude (with web search)
   - Perplexity
   - Gemini
   - Microsoft Copilot
   - Google AI Overviews (run the question as a Google search and inspect the AI Overview block)
3. For each engine, record: cited (Y/N), citation position (1 = first cited source), and presence-of-page-as-the-primary-anchor (Y/N — is the answer paraphrasing the page or merely linking to it).

**Stage 6 rubric:**

| Verdict | Criteria |
|---|---|
| **PREFERRED** | Page cited by ≥ 4 of 6 engines AND average citation position ≤ 2 |
| **CITED** | Page cited by 2–3 engines, any position |
| **MENTIONED** | Page cited by 1 engine, OR domain (not URL) cited by ≥ 2 engines |
| **INVISIBLE** | No citation across any engine |

Stage 6 PASS = verdict is `PREFERRED` or `CITED`. **Note:** Stage 6 is run **14 days post-publication**, not at publish time — engines need indexing lag. At publish time, Stage 6 is marked `PENDING` and the file is regenerated on day 14.

---

## Pipeline State Machine (PIPELINE_READY / PIPELINE_DEGRADED / BLOCKED)

| State | Criteria |
|---|---|
| **PIPELINE_READY** | All 5 stages PASS at publish time (Stage 6 PENDING is acceptable for the initial run); on the day-14 regeneration, Stage 6 = PREFERRED or CITED |
| **PIPELINE_DEGRADED** | Exactly one stage FAIL, and it is not Stage 1 or Stage 4 |
| **BLOCKED** | Stage 1 FAIL, OR Stage 4 FAIL, OR ≥ 2 stages FAIL |

A `PIPELINE_DEGRADED` page is publishable but a remediation ticket is generated. A `BLOCKED` page must not be promoted via `geo-distribution-plan` until remediated — the upstream Stage 1/4 problems guarantee distribution effort would be wasted.

---

## Workflow

### Step 1: Inherit AI Crawler Status from geo-crawlers

1. If a recent `geo-crawlers` report exists in the current directory or `~/.geo-prospects/audits/`, parse the per-crawler status table.
2. If no report exists, run `/geo crawlers <domain>` and inherit the output.
3. Apply the four Stage 1 pipeline-specific checks above against the URL path.
4. Record Stage 1 verdict.

### Step 2: Audit Internal-Link Anchors and Depth

1. Fetch the page's HTML via WebFetch.
2. Fetch the homepage and walk the sitemap to map the click-depth graph (cap at 5 levels deep; abort if no sitemap and crawl > 200 internal pages would be required).
3. For each inbound internal link to the target URL, extract the anchor text.
4. Look up the page's `intent:` value (from front-matter, from the matrix record, or by classifying the page using the disambiguation rules in `geo-intent-matrix`).
5. Score anchors against the intent trigger vocabulary; mark PASS / FAIL on each Stage 2 sub-check.

### Step 3: Score Authority Backlinks from AI-Training Source Domains

1. For Tier A check Wikipedia first via API (see the procedure in `agents/geo-ai-visibility.md` Step 5 — do not duplicate). Then Reddit, GitHub, Stack Overflow, etc. via WebFetch `site:` search patterns.
2. For Tier B check via WebFetch `site:<domain> "<core-topic>"` queries.
3. Record mention counts, recency, and topical relevance.
4. Compute Stage 3 verdict.

### Step 4: Inherit On-Page Compliance from geo-citability and geo-schema

1. If recent `GEO-CITABILITY-SCORE.md` and `GEO-SCHEMA-REPORT.md` files exist for this URL, parse them.
2. If not, run `/geo citability <url>` and `/geo schema <url>` to generate them.
3. Apply the Stage 4 threshold table.
4. Validate the form-binding contract by looking up the page in the latest `~/.geo-prospects/matrices/<domain>-<topic>-*.md` and confirming the actual page form matches the planned form.

### Step 5: Build Rapid-Indexing Submission Checklist

1. **IndexNow:** Check for `<host>-<api-key>.txt` at site root. Check for IndexNow ping log (most CMS plugins log this; if not, instruct user to issue a manual ping with the curl snippet below).
2. **Google URL Inspection:** Mark as `manual submission required` and emit instructions; if Search Console MCP / API is wired up, attempt programmatic check.
3. **Bing Webmaster:** Same as Google — mark manual unless API is wired up.
4. **Sitemap `lastmod`:** Fetch `/sitemap.xml`, locate the URL entry, parse `<lastmod>`, compare to publish date.
5. **llms.txt:** Inherit `geo-llmstxt` output if available; otherwise fetch `/llms.txt` and grep for the URL.

**Manual IndexNow ping snippet (emit verbatim in the output):**

```
curl -X POST 'https://api.indexnow.org/IndexNow' \
  -H 'Content-Type: application/json' \
  -d '{
    "host": "<domain>",
    "key": "<api-key>",
    "keyLocation": "https://<domain>/<api-key>.txt",
    "urlList": ["<url>"]
  }'
```

### Step 6: Capture Preferred-Answer Snapshot Across 6 Engines

1. If invoked at publish time, set Stage 6 = `PENDING` and emit a 14-day callback note. Skip to Step 7.
2. If invoked 14+ days post-publish (or the user passes `--verify`), build the probe question from the page's `intent:` and `question:` metadata.
3. Use WebFetch to query each engine where a public web interface exists (Perplexity, Gemini, Google AI Overviews via google.com search). For ChatGPT, Claude, and Copilot, instruct the user to capture the response manually and paste into a stub block — these engines do not have stable public-URL query endpoints.
4. Record cited Y/N, position, and primary-anchor status per engine.
5. Apply the Stage 6 rubric.

### Step 7: Roll Up to Pipeline State and Emit Remediation Plan

1. Apply the pipeline state machine.
2. For each FAIL, generate a remediation item with concrete action, owner ("content" / "dev" / "marketing"), and effort estimate.
3. Emit the output file at `~/.geo-prospects/pipelines/<domain>-<slug>-<YYYY-MM-DD>.md`.

---

## Upstream Skill Hooks

| Stage | Upstream skill | What it consumes |
|---|---|---|
| 1 | `geo-crawlers` | Per-crawler status table; sitemap reference |
| 2 | `geo-intent-matrix` | Intent trigger vocabulary; planned page intent |
| 4 | `geo-citability` | Page-level citability score and per-block scores |
| 4 | `geo-schema` | Schema validation result and per-type presence |
| 4 | `geo-intent-matrix` | Form-binding contract |
| 5 | `geo-llmstxt` | URL-in-llms.txt status |

## Downstream Skill Hooks

| Downstream skill | What this pipeline feeds it |
|---|---|
| `geo-distribution-plan` | Pipeline verdict gates distribution: BLOCKED pages do not enter the cadence calendar |
| `geo-competitor-citation` | Stage 6 snapshot becomes a baseline that competitor analysis builds on (avoiding duplicated probe runs) |
| `geo-compare` | The pipeline state is one of the per-page metrics tracked month-over-month |

---

## Output Format

Generate `~/.geo-prospects/pipelines/<domain>-<slug>-<YYYY-MM-DD>.md`:

```markdown
# GEO Citation Pipeline: <Page Title>

**URL:** <url>
**Run date:** <YYYY-MM-DD>
**Intent:** <Definitional / Comparative / Procedural / Causal>
**Planned question:** <question from matrix>

**Pipeline state:** [PIPELINE_READY / PIPELINE_DEGRADED / BLOCKED]

---

## Stage Summary

| # | Stage | Verdict | Notes |
|---|---|---|---|
| 1 | AI Crawler Robots Audit | [PASS / FAIL] | <one-line> |
| 2 | Internal-Link Wiring | [PASS / FAIL] | <one-line> |
| 3 | AI-Training Authority Backlinks | [PASS / FAIL] | <one-line> |
| 4 | On-Page GEO Compliance | [PASS / FAIL] | <one-line> |
| 5 | Rapid-Indexing Channels | [PASS / FAIL] | <one-line, channel pass count: X/5> |
| 6 | Preferred-Answer Verification | [PREFERRED / CITED / MENTIONED / INVISIBLE / PENDING] | <day-N post-publish> |

---

## Stage 1 — AI Crawler Robots Audit

| Check | Verdict | Detail |
|---|---|---|
| Per-URL robots for 5 critical crawlers | [PASS/FAIL] | <list crawlers + status> |
| noindex meta + X-Robots-Tag | [PASS/FAIL] | <observed value> |
| Server response | [PASS/FAIL] | <status code + redirect hops> |
| Render mode | [PASS/FAIL] | [SSR / pre-rendered / CSR-only] |

## Stage 2 — Internal-Link Wiring

| Check | Verdict | Detail |
|---|---|---|
| Click depth from homepage | [PASS/FAIL] | <N clicks> |
| Inbound internal links | [PASS/FAIL] | <N inbound links from M pages> |
| Anchor-text intent triggers | [PASS/FAIL] | <X% of anchors contain intent triggers> |
| Topical-cluster hub link | [PASS/FAIL] | <hub page URL or "no hub"> |
| Canonical | [PASS/FAIL] | <canonical URL> |

## Stage 3 — AI-Training Authority Backlinks

**Tier A mentions:** <list with URL + linked/unlinked + date>
**Tier B mentions:** <list>

| Check | Verdict | Detail |
|---|---|---|
| Tier A mentions ≥ 1 | [PASS/FAIL] | <N> |
| Tier B mentions ≥ 3 | [PASS/FAIL] | <N> |
| Recency ≤ 12 mo | [PASS/FAIL] | <most recent date> |
| Topical context | [PASS/FAIL] | <count of contextually relevant> |

## Stage 4 — On-Page GEO Compliance

| Check | Verdict | Detail |
|---|---|---|
| Citability score ≥ 70 | [PASS/FAIL] | <score>/100 |
| Top answer block in 134–167 window | [PASS/FAIL] | <best passage word count> |
| Required schema present | [PASS/FAIL] | <intent → required → present> |
| Schema validation | [PASS/FAIL] | <error count> |
| Form-binding match | [PASS/FAIL] | <planned form / actual form> |

## Stage 5 — Rapid-Indexing Channels

| Channel | Verdict | Detail |
|---|---|---|
| IndexNow | [PASS/FAIL] | <last ping timestamp or "not pinged"> |
| Google URL Inspection | [PASS/FAIL] | <Search Console status or "manual required"> |
| Bing Webmaster | [PASS/FAIL] | <last submission> |
| Sitemap lastmod | [PASS/FAIL] | <lastmod value, drift from publish> |
| llms.txt freshness | [PASS/FAIL] | <listed Y/N> |

**Channel PASS count: X/5**

### IndexNow ping snippet (manual fallback)

```
curl -X POST 'https://api.indexnow.org/IndexNow' \
  -H 'Content-Type: application/json' \
  -d '{
    "host": "<domain>",
    "key": "<api-key>",
    "keyLocation": "https://<domain>/<api-key>.txt",
    "urlList": ["<url>"]
  }'
```

## Stage 6 — Preferred-Answer Verification

**Probe question:** "<question>"
**Verification date:** <YYYY-MM-DD> (day <N> post-publish)

| Engine | Cited (Y/N) | Position | Primary anchor (Y/N) |
|---|---|---|---|
| ChatGPT (search) | | | |
| Claude (web search) | | | |
| Perplexity | | | |
| Gemini | | | |
| Microsoft Copilot | | | |
| Google AI Overviews | | | |

**Stage 6 verdict:** [PREFERRED / CITED / MENTIONED / INVISIBLE / PENDING]

---

## Remediation Plan

| Priority | Stage | Action | Owner | Effort |
|---|---|---|---|---|
| <P0/P1/P2> | <stage #> | <concrete action> | <content/dev/marketing> | <S/M/L> |

---

## Re-verification Schedule

- **Day 14 post-publish:** re-run with `--verify` to populate Stage 6
- **Day 30 post-publish:** if Stage 6 = INVISIBLE or MENTIONED, escalate to `/geo compete` for full gap analysis
```

---

## Quality Gates

- **Stage 1 and Stage 4 are non-negotiable.** A FAIL on either drops the pipeline to BLOCKED regardless of how many other stages pass.
- **Stage 6 cannot be run at publish time.** AI engines need indexing lag (median 7 days, P95 14 days). Always mark `PENDING` at publish and schedule a day-14 re-run.
- **Stage 3 mention counts are noisy.** Wikipedia is authoritative (API check); other Tier A/B domains are best-effort via WebFetch and may under-report. Always note "minimum N found" rather than "exactly N exist."
- **Inheritance freshness:** Inherited reports (`geo-crawlers`, `geo-citability`, `geo-schema`) older than 30 days must be re-run before being trusted. Mark stale inherited data with a `(stale, regenerated)` suffix.
- **Distribution gate:** Never trigger `/geo distribute` for a URL whose pipeline state is BLOCKED. Distribution amplifies whatever the AI engine sees on the destination — if the destination is broken, distribution multiplies the waste.
- **Rate limit:** Stage 6 probe runs should be spaced ≥ 5 seconds between engines and respect each engine's terms of service. Captured snapshots are point-in-time and may not be reproducible.

---

## Important Notes

- This skill is the **GEO step-3 implementation** in the four-step GEO workflow (angles → publish → guide → measure). The other three steps map to `geo-intent-matrix` (angles), `geo-distribution-plan` (publish), and `geo-competitor-citation` (measure).
- Do not run this pipeline on every URL — it is expensive (WebFetch + multiple inherited skills). Run it on P0 pieces planned by `geo-intent-matrix` and on any URL that scores < 60 in a prior `geo-audit`.
- The "preferred answer" verdict in Stage 6 is the only metric that proves the loop closed. All five upstream gates can be green and the engine can still ignore the page — usually because the engine has already locked onto a competitor's answer. When that happens, the remediation is not pipeline-level; it is competitive (run `/geo compete` and target the specific competitor citations).
- If the site uses heavy client-side rendering (React/Vue SPA without SSR), Stage 1 will almost always FAIL. The remediation is structural (add SSR or pre-rendering) and outside the scope of this skill — flag it loudly in the remediation plan.

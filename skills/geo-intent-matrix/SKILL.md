---
name: geo-intent-matrix
description: >
  Query-intent angle matrix for systematic GEO content coverage. Given a core
  topic, generates a 4-quadrant intent matrix (Definitional / Comparative /
  Procedural / Causal), scores each candidate question by search volume × AI
  citation propensity × difficulty, binds each intent to a required content
  form, and emits a 12-week rolling editorial schedule with downstream hooks
  into geo-citation-pipeline, geo-distribution-plan, and geo-competitor-citation.
  Use when user says "matrix", "intent matrix", "content angles", "intent angles",
  "topic plan", "/geo matrix", or asks how to systematically cover a topic for
  AI search.
version: 1.0.0
author: geo-seo-claude-plus
tags: [geo, intent, content-strategy, planning, matrix, coverage]
allowed-tools: Read, Grep, Glob, Bash, WebFetch, Write
---

# GEO Intent-Angle Matrix Skill

## Core Insight

AI search engines do not cite "the best article" — they cite the article that best matches the **shape of the user's question**. Every query the user types into ChatGPT, Perplexity, Claude, Gemini, Copilot, or Google AI Overviews falls into one of four intent shapes: *what is this*, *which of these*, *how do I do this*, or *why does this happen*. Each shape rewards a structurally different content form. A site that publishes only "What is X" definitional content will be invisible whenever the user asks "X vs Y," "How to X," or "Why X" — no matter how high-quality the existing pages are.

A 2025 Profound study analyzing 40,000 AI search citations across the five major engines found that **Definitional** content drives 31 % of citations, **Comparative** 27 %, **Procedural** 24 %, and **Causal** 18 %. A site covering only one quadrant therefore caps its addressable AI-citation surface at roughly a quarter of the maximum. Coverage breadth across all four intents matters more than depth in any single one.

This skill turns one core topic into a 12-week rolling editorial plan that systematically populates all four quadrants, scores each candidate question by ROI, binds each intent to its required content form (so downstream `geo-content` can produce the right structure), and wires each planned piece into the rest of the GEO loop.

---

## How to Use This Skill

1. Collect a single **core topic** (1–4 words, the central entity the site wants to be cited for).
2. Collect the **target domain** so the coverage heat-map can be built from the live sitemap and prior `geo-brand-mentions` data.
3. (Optional) Collect a list of 3–10 **seed entities** the topic should co-occur with (related products, methods, audiences).
4. Run the 6-step workflow below.
5. Emit `~/.geo-prospects/matrices/<domain>-<topic>-<YYYY-MM-DD>.md`.

---

## The Four Intent Angles (Taxonomy)

Every candidate question must be classified into exactly one of these four buckets. If a question fits two, split it into two questions.

### Definitional (What is X)

**Trigger when:** the user is encountering a concept, product, technology, or term for the first time and needs a clean mental model.

**Surface patterns:**
- "What is `<term>`?"
- "`<term>` meaning / definition / explained"
- "What does `<term>` mean in `<context>`?"
- "`<term>` overview / introduction"
- "What is `<term>` used for?"

**Why AI engines cite it:** Definitional passages are the highest-value training-and-retrieval blocks because they let an LLM produce a confident opening sentence. Engines preferentially extract a single 134-167 word self-contained paragraph that opens with "X is …" or "X refers to …".

**Required content form:** see [Intent → Content-Form Binding](#intent--content-form-binding).

### Comparative (X vs Y)

**Trigger when:** the user is in active selection mode and needs to choose between options.

**Surface patterns:**
- "`<X>` vs `<Y>`"
- "Best `<category>` (2026)"
- "Top N `<category>` for `<use-case>`"
- "Which is better, `<X>` or `<Y>`?"
- "`<X>` alternatives"
- "`<X>` vs `<Y>` vs `<Z>` comparison"

**Why AI engines cite it:** Comparative queries trigger high-confidence table extraction. Engines prefer pages that present 3+ options in a side-by-side table with consistent columns (price, feature, audience) — they can then re-render the table directly in the answer.

### Procedural (How to X)

**Trigger when:** the user has decided and is now executing a task.

**Surface patterns:**
- "How to `<verb>` `<object>`"
- "Steps to `<verb>` `<object>`"
- "`<verb>` `<object>` tutorial"
- "Guide to `<verb>` `<object>`"
- "How do I `<verb>` `<object>` in `<context>`?"

**Why AI engines cite it:** Procedural queries trigger ordered-list extraction. Engines reward pages with explicit numbered steps, each step self-contained, with imperative verbs in step 1 of each item.

### Causal (Why X)

**Trigger when:** the user has hit a surprise and is asking for mechanism, root cause, or principle.

**Surface patterns:**
- "Why does `<phenomenon>` happen?"
- "Why is `<X>` `<adjective>`?"
- "How does `<X>` work?"
- "What causes `<X>`?"
- "Reason for `<X>`"

**Why AI engines cite it:** Causal queries are the deepest funnel stage and the lowest-volume but highest-trust quadrant. Engines reward cause-and-effect chains supported by data, named studies, or first-party experiments. Causal content is the strongest E-E-A-T signal because it requires demonstrated expertise rather than aggregation.

### Disambiguation rules

If a candidate question fits two quadrants, apply these tie-breakers in order:

1. If a number ("top 5", "best 3") is present → **Comparative**.
2. If an imperative verb ("install", "set up", "configure", "run") is the head → **Procedural**.
3. If "why" is the head wh-word → **Causal**.
4. If "what" is the head wh-word and no list/verb is present → **Definitional**.
5. If still ambiguous, split the question into two single-intent versions.

---

## Intent → Content-Form Binding

This table is the contract consumed by `geo-content`. When `geo-content` is invoked on a page that the matrix planned, it must validate the page against the form for its intent.

| Intent | Required Form | Minimum Structural Elements | Length Target | Reject If |
|---|---|---|---|---|
| Definitional | Standalone definition block 134–167 words at the top, then expansion | Opening "`<X>` is …" sentence; one named source within first 3 sentences; one numeric fact within first 6 sentences | 800–1500 words total | Opening sentence is narrative or hedged; no numeric fact in opening block |
| Comparative | HTML table with ≥ 3 rows and ≥ 4 consistent columns | Header row; one row per option; columns include price-or-equivalent, primary feature, audience, verdict | 1200–2500 words total | Table absent; table has < 3 rows; columns inconsistent across rows |
| Procedural | Ordered list with 5–15 numbered steps | Each step opens with imperative verb; each step is self-contained (no "as above"); a one-screenshot-or-code-block ratio per step is recommended | 1000–2000 words total | Steps are unnumbered prose; step 1 does not begin with imperative verb |
| Causal | Cause → effect chain with named mechanisms and ≥ 2 cited studies | Explicit "because" connectors; named study/dataset citations; at least one data table OR diagram description | 1500–3000 words total | No named source; no mechanism named; ends in opinion without data |

Each planned piece must declare its intent in the front-matter `intent:` field so downstream skills can validate the form binding.

---

## Angle Expansion Templates

Given a core topic, mechanically expand candidate questions per quadrant. Aim for ≥ 5 candidates per intent (matrix minimum is 20 questions total).

### Definitional expansion

For core topic `T`:

1. What is `T`?
2. What is `T` used for?
3. `T` vs related-but-distinct concept `R` (definitional, not comparative — clarifying boundary, not picking a winner)
4. What is `T` in `<industry>` / for `<persona>`?
5. History of `T` / where did `T` come from?
6. `T` explained for `<expertise-level>` (beginners / engineers / executives)

### Comparative expansion

For core topic `T`:

1. Best `T` solutions in `<year>`
2. `T` vs `<top-alternative-1>`
3. `T` vs `<top-alternative-2>`
4. Top N `T` for `<use-case>`
5. `T` alternatives
6. `<vendor-A>` vs `<vendor-B>` in the `T` category

### Procedural expansion

For core topic `T`:

1. How to start with `T`
2. How to set up / configure / install `T`
3. How to migrate from `<predecessor>` to `T`
4. How to integrate `T` with `<adjacent-system>`
5. How to debug / troubleshoot `T`
6. How to scale / harden `T` for `<context>`

### Causal expansion

For core topic `T`:

1. Why does `T` matter?
2. Why is `T` `<surprising-property>`?
3. How does `T` actually work under the hood?
4. What causes `T` to fail / break / underperform?
5. Why did `<industry>` move from `<predecessor>` to `T`?
6. Why is `T` better / worse than `<alternative>` for `<criterion>` (mechanism, not verdict)

---

## Priority Scoring (Search Volume × AI Citation Propensity × Difficulty)

Each candidate question gets a P-score on three factors, then the product is bucketed into P0/P1/P2.

### Factor 1: Search Volume (SV)

Estimate monthly search volume for the question. Use Bash + WebFetch to pull from Google Suggest, People Also Ask, or any available keyword tool the user has wired up. If no tool is available, infer from query head/torso/tail length:

| SV Bucket | Volume Range | Score |
|---|---|---|
| Head | 10k+/mo | 5 |
| Upper torso | 1k–10k/mo | 4 |
| Torso | 100–1k/mo | 3 |
| Tail | 10–100/mo | 2 |
| Long tail | < 10/mo | 1 |

### Factor 2: AI Citation Propensity (AICP)

How likely is this question to be answered by an AI engine rather than a traditional SERP. Use the 2025 Profound distribution as the prior:

| Intent | Base AICP | Adjustments |
|---|---|---|
| Definitional | 4 | +1 if topic is < 5 years old (engines preferred for fresh terms) |
| Comparative | 5 | +0, –1 if traditional review sites dominate the SERP |
| Procedural | 4 | +1 if topic is technical / developer-oriented; –1 if topic is regulated (legal/medical) |
| Causal | 3 | +1 if topic requires synthesizing multiple sources |

Floor at 1, cap at 5.

### Factor 3: Difficulty (D)

Inverted — higher difficulty subtracts from P-score. Estimate from existing competitor coverage observed during `geo-competitor-citation` runs, or fall back to a default of 3.

| D Bucket | Description | Score (inverted) |
|---|---|---|
| Open | No strong incumbent answer | 5 |
| Contested | Several incumbents but no consensus citation | 4 |
| Crowded | Multiple high-authority answers | 3 |
| Locked | Wikipedia + 2+ top-DR sites dominate every engine | 2 |
| Saturated | Brand has zero realistic shot of displacing incumbents | 1 |

### P-score and Bucketing

`P = SV × AICP × D` (range 1–125)

| Bucket | Range | Meaning |
|---|---|---|
| **P0** | ≥ 60 | Must-publish this quarter |
| **P1** | 30–59 | Publish next quarter |
| **P2** | < 30 | Backlog; revisit annually |

---

## Coverage Heat-Map Self-Check

Before emitting the 12-week schedule, render the current state of the site against the 4 quadrants.

### Inputs

1. **Sitemap scan** — fetch `/sitemap.xml`, list every URL whose title or H1 contains the core topic or a seed entity.
2. **Existing entity coverage** — read the latest `~/.geo-prospects/audits/<domain>-*.md` if present and extract any brand-mention entities already inventoried.
3. **For each candidate question** in the expanded matrix, mark it as `COVERED`, `PARTIAL`, or `MISSING` based on URL-title fuzzy match against the sitemap.

### Heat-Map Output (always render)

```
                COVERAGE BY INTENT QUADRANT

                Definitional   Comparative   Procedural    Causal
P0 (must-do)    [█ COVERED]    [░ MISSING]   [▒ PARTIAL]   [░ MISSING]
P1 (next Q)     [▒ PARTIAL]    [░ MISSING]   [░ MISSING]   [░ MISSING]
P2 (backlog)    [▒ PARTIAL]    [░ MISSING]   [░ MISSING]   [░ MISSING]

Coverage score: 18 % (3 of 16 cells covered or partial)
Critical gaps: P0 Comparative, P0 Causal
```

Coverage score = (`COVERED` cells × 1.0 + `PARTIAL` cells × 0.5) / total cells.

---

## Workflow

### Step 1: Resolve Core Topic and Seed Entities

1. Capture the core topic from the user invocation.
2. If the user did not provide seed entities, infer 3–10 from the homepage of the target domain via WebFetch (look for navigation items, product names, repeated noun phrases).
3. Confirm topic and seeds before proceeding.

### Step 2: Expand Candidate Questions per Quadrant

1. Apply the four expansion templates above to the core topic.
2. Generate **at least 5** candidates per quadrant. Aim for 6 to leave room for filtering. Final matrix size: 20–24 questions.
3. For each candidate, classify via the disambiguation rules. If a question lands in the wrong quadrant after generation, move or split it.

### Step 3: Score and Triage (P0 / P1 / P2)

1. Compute SV, AICP, D for every candidate.
2. Multiply for P-score; bucket into P0/P1/P2.
3. Discard any candidate scoring < 8 (`SV=1 × AICP=2 × D=4` or worse) — these are not worth the production cost.

### Step 4: Bind Each Item to a Content Form

1. Look up the required form in the [Intent → Content-Form Binding](#intent--content-form-binding) table.
2. Add the form spec to each item's plan record. This becomes the contract for `geo-content` later.
3. Flag any item where the user has indicated a preference for a non-default form (e.g., they want a Causal piece presented as a video) — note the deviation but warn that citation propensity may drop.

### Step 5: Build Coverage Heat-Map from Sitemap + Brand-Mentions Inventory

1. Fetch the site's sitemap.
2. For each candidate, fuzzy-match against existing URLs (title + slug match at ≥ 60 % similarity).
3. Mark COVERED / PARTIAL / MISSING.
4. Render the heat-map block in the output.

### Step 6: Emit 12-Week Rolling Schedule with Downstream Hooks

1. Order all P0 items first, then P1, then P2.
2. Spread items across 12 weeks (typically 1–2 items/week).
3. For each scheduled item, emit a row with the following columns:

```
Week | Intent | Question | Form | P-score | Downstream actions
```

Where Downstream actions is a comma-separated list selected from:

- `→ geo-citation-pipeline` (run after publication)
- `→ geo-distribution-plan` (run on publication day)
- `→ geo-competitor-citation` (run 14 days post-publication to confirm engine pickup)

Every P0 item gets all three downstream hooks. P1 items get `geo-citation-pipeline` + `geo-distribution-plan`. P2 items get `geo-citation-pipeline` only.

---

## Downstream Skill Hooks

This matrix is the upstream contract for three downstream skills. The hooks are:

| Downstream Skill | What the matrix feeds it |
|---|---|
| `geo-content` | Per-piece `intent:` value and required form spec — used to validate the draft before publication |
| `geo-citation-pipeline` | The URL of each published piece, with its intent — pipeline tunes its on-page checks per intent (Comparative pages get table-extraction checks; Procedural pages get step-list checks) |
| `geo-distribution-plan` | The full matrix as input topic universe — distribution plan picks tier targets per intent (Comparative content syndicates well to Reddit; Procedural to dev platforms; Causal to long-form like Substack/Medium) |
| `geo-competitor-citation` | The same 20-question matrix is reused as the competitor probe set (avoiding duplicated taxonomy work) |

---

## Output Format

Generate `~/.geo-prospects/matrices/<domain>-<topic>-<YYYY-MM-DD>.md` with the following structure:

```markdown
# GEO Intent Matrix: <Core Topic>

**Domain:** <domain>
**Generated:** <YYYY-MM-DD>
**Core topic:** <topic>
**Seed entities:** <entity-1>, <entity-2>, …

**Matrix status:** [MATRIX_COMPLETE / MATRIX_PARTIAL / BLOCKED]

---

## Coverage Heat-Map

```
<heat-map block from Step 5>
```

**Coverage score:** <X>%
**Critical gaps:** <list of P0 MISSING quadrants>

---

## Quadrant 1 — Definitional

| # | Question | SV | AICP | D | P-score | Bucket | Status | Form |
|---|---|---|---|---|---|---|---|---|
| 1 | <question> | 4 | 5 | 4 | 80 | P0 | MISSING | Standalone definition block |
| … | | | | | | | | |

## Quadrant 2 — Comparative

| # | Question | SV | AICP | D | P-score | Bucket | Status | Form |
|---|---|---|---|---|---|---|---|---|
| … | | | | | | | | |

## Quadrant 3 — Procedural

| # | Question | SV | AICP | D | P-score | Bucket | Status | Form |
|---|---|---|---|---|---|---|---|---|
| … | | | | | | | | |

## Quadrant 4 — Causal

| # | Question | SV | AICP | D | P-score | Bucket | Status | Form |
|---|---|---|---|---|---|---|---|---|
| … | | | | | | | | |

---

## 12-Week Rolling Schedule

| Week | Intent | Question | Form | P-score | Downstream actions |
|---|---|---|---|---|---|
| 1 | Definitional | What is <topic>? | Standalone definition block | 100 | → geo-citation-pipeline, → geo-distribution-plan, → geo-competitor-citation |
| 1 | Comparative | <topic> vs <alt> | HTML comparison table | 80 | → geo-citation-pipeline, → geo-distribution-plan, → geo-competitor-citation |
| 2 | Procedural | How to <verb> <topic> | Ordered list 5–15 steps | 72 | → geo-citation-pipeline, → geo-distribution-plan, → geo-competitor-citation |
| … | | | | | |

---

## Downstream Wire-Up

For each P0 item published this quarter:

1. Run `/geo pipeline <url>` to confirm the 5-stage citation pipeline is healthy.
2. Run `/geo distribute <topic>` to generate the 14-day cadence calendar.
3. Run `/geo compete <domain> <competitor1,competitor2,...>` 14 days post-publication to confirm engine pickup.

---

## Quality Gates

- Matrix is **MATRIX_COMPLETE** iff every quadrant has ≥ 5 candidates and ≥ 1 P0.
- Matrix is **MATRIX_PARTIAL** iff one or more quadrants has zero P0 candidates — the schedule will still emit but the gap section will flag the missing quadrant.
- Matrix is **BLOCKED** iff the sitemap cannot be fetched or the core topic could not be resolved against the site.
```

---

## Quality Gates

- **Quadrant minimum:** Every quadrant must have ≥ 5 candidate questions after Step 2.
- **P0 minimum per quadrant:** A quadrant with zero P0 items downgrades the matrix to MATRIX_PARTIAL and is flagged in the heat-map.
- **Schedule cap:** Maximum 2 P0 items per week to avoid production bottlenecks. Items beyond the cap roll into the next available week.
- **Duplicate guard:** If two candidates collapse to the same fuzzy question (≥ 80 % similarity), keep only the higher-scoring one.
- **Sitemap fetch timeout:** 30 seconds. If the sitemap is unreachable, set status BLOCKED and abort emission.
- **Intent purity:** No candidate may carry two intents. If disambiguation rules cannot resolve, split into two questions.

---

## Important Notes

- This skill **plans** content. It does not write it. Page bodies are produced downstream by `geo-content`.
- The 4-quadrant taxonomy is the canonical intent vocabulary for the entire fork. `geo-competitor-citation` reuses it verbatim. Do not introduce a fifth intent here without updating both downstream skills.
- Search volume estimates are unreliable without a keyword tool wired up. When falling back to head/torso/tail heuristics, mark the SV cell with a `~` prefix in the output table to signal the estimate is rough.
- The 2025 Profound citation distribution (31/27/24/18) is a population prior, not a per-topic guarantee. A site selling B2B compliance software will skew Causal-heavy; a site selling consumer electronics will skew Comparative-heavy. Treat the priors as defaults, not targets.
- The matrix output file should be regenerated quarterly, not monthly. The 12-week schedule horizon matches one publishing quarter and a longer regeneration cycle would invalidate downstream pipeline runs.

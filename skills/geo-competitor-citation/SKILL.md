---
name: geo-competitor-citation
description: >
  Cross-engine competitor GEO gap analysis. Runs a representative question
  set against 6 AI engines (ChatGPT, Claude, Perplexity, Gemini, Copilot,
  Google AI Overviews) for the brand and N competitors, normalizes citations,
  and builds a 3-D gap matrix (brand × engine × intent type) showing citation
  count, average position, and contextual sentiment. Emits LEADING / PARITY /
  LAGGING / CRITICAL_GAP verdict per quadrant plus a top-3 remediation plan
  mapped back to geo-content, geo-distribution-plan, and geo-citation-pipeline.
  Use when user says "compete", "competitor", "gap analysis", "citation gap",
  "/geo compete", or asks how your AI visibility compares against named rivals.
version: 1.0.0
author: geo-seo-claude-plus
tags: [geo, competitor, gap-analysis, citation, ai-engines, benchmarking]
allowed-tools: Read, Grep, Glob, Bash, WebFetch, Write
---

# GEO Competitor Citation Gap Skill

## Core Insight

`geo-compare` answers "*am I improving against myself month over month?*". This skill answers a different question: "*for the questions my audience actually asks AI engines, who is being cited — me, or someone else?*"

Self-comparison is necessary but insufficient. A brand can climb its own GEO score from 40 to 65 over a quarter and still be invisible in AI answers because two competitors moved from 75 to 85 in the same period. AI citation is a positional game: engines cite a small set of sources per answer (Perplexity 4–8, ChatGPT 2–4, Gemini 3–5, Google AI Overviews 2–4, Claude 1–3, Copilot 2–3) and the question is not "did I get better" but "did I get into the cited set."

A 2025 Ahrefs / Profound cross-engine analysis of 18,000 commercial queries found that the same brand was cited in different positions across engines for 73 % of queries — meaning a brand can rank #1 in Perplexity, be missing from ChatGPT, and rank #3 in Gemini for the same question. Position varies by engine because each engine's training mix and retrieval logic is different. A single-engine view of competitive positioning is misleading.

This skill therefore probes all 6 major engines, with 3 runs per probe for denoising, across a 20-question matrix balanced over the 4 intent types from `geo-intent-matrix`. The output is a 3-D matrix (brand × engine × intent) that surfaces both topical and engine-specific gaps, and a top-3 remediation plan that maps each gap to the right upstream skill.

---

## How to Use This Skill

1. Take **my-domain** and a comma-separated **competitor list** (1–4 competitors).
2. (Optional) Take a topic scope — if omitted, the latest `~/.geo-prospects/matrices/<domain>-*.md` is used to source the 20 probe questions.
3. Run the 8-step workflow below.
4. Emit `~/.geo-prospects/competitor/<my-domain>-<YYYY-MM-DD>.md`.

**Cost note:** This skill runs 20 questions × 6 engines × 3 runs = **360 probes per execution**. Several engines do not have stable public-URL query endpoints; for those, the skill stops at the planned probe and asks the user to capture the response manually. Plan on 60–90 minutes of human time for a full run unless a programmatic SDK is wired up.

---

## Question Set Construction (4 intents × 5 questions = 20)

The probe set is **balanced across the four intents** so the gap matrix can attribute gaps to a specific intent shape (e.g., "we are LEADING on Definitional but CRITICAL_GAP on Comparative").

### Sourcing the questions

**Preferred:** Pull from the latest `~/.geo-prospects/matrices/<domain>-<topic>-*.md`. Take the top-5 P-scored questions from each quadrant.

**Fallback (no matrix exists):** Generate 5 questions per quadrant using the angle expansion templates from `geo-intent-matrix`. Note this in the output file as a "matrix-less probe set" — results are still valid but less aligned with the brand's stated content strategy.

### Question quality gates

Each of the 20 questions must:

- Be phrased exactly as a real user would type into an AI engine (lowercase, no over-formatting).
- Be answerable by content in the brand's space (do not probe questions where the brand has no plausible authority).
- Not name any competitor explicitly (those probes are meta-questions handled separately in the optional `--meta` flag).
- Be in the language of the target market (if `region: cn`, questions are in Chinese).

---

## Cross-Engine Execution Protocol (6 engines × 3 runs for denoising)

| # | Engine | Surface | Programmatic? | Probe handling |
|---|---|---|---|---|
| 1 | **ChatGPT (search mode)** | chatgpt.com with search toggle on | No stable public-URL query API | Manual capture via the user pasting response text into a stub block |
| 2 | **Claude (web search)** | claude.ai with web search | No stable public-URL query API | Manual capture |
| 3 | **Perplexity** | perplexity.ai | Yes — `https://www.perplexity.ai/search?q=<encoded>` is fetchable but rate-limited; use WebFetch |
| 4 | **Gemini** | gemini.google.com | No stable public-URL query API | Manual capture |
| 5 | **Microsoft Copilot** | copilot.microsoft.com or Bing chat | No stable public-URL query API | Manual capture |
| 6 | **Google AI Overviews** | google.com SERP (AI Overview block) | Yes — fetch `https://www.google.com/search?q=<encoded>&udm=14` (web tab) or vanilla SERP and look for the AI Overview block; respect rate limits | WebFetch |

### Denoising via 3 runs

For each probe, run the question **3 times** with 90 s gap between runs:

- **Citation set =** the union of cited sources across the 3 runs.
- **Stable position =** the median position across runs where the source is cited (if cited in < 2 runs, mark `unstable`).
- **Citation rate =** the fraction of runs in which the source is cited (used as a confidence weight in the matrix).

### Capture format per probe

For each probe-engine pair, capture:

```yaml
probe: "<question>"
engine: <engine>
runs:
  - run: 1
    cited_sources:
      - position: 1
        url: <url>
        domain: <domain>
        anchor_text: <…>
        context_excerpt: <≤ 280 char snippet showing how the source was used>
      - position: 2
        url: <url>
        domain: <domain>
        anchor_text: <…>
        context_excerpt: <…>
  - run: 2
    cited_sources: [...]
  - run: 3
    cited_sources: [...]
```

Store raw captures under `~/.geo-prospects/competitor/_runs/<my-domain>-<YYYY-MM-DD>/<engine>-<probe-id>.yaml` so a later re-analysis can recompute the matrix without re-probing.

---

## Citation Normalization Rules

Raw citation lists are noisy. Normalize before populating the matrix.

### Brand alias merging

For each tracked brand (my-domain + competitors), maintain an alias list:

```yaml
brand: <competitor-1>
canonical_domain: <competitor-1-domain.com>
aliases:
  - <brand spelled differently>
  - <legal entity name>
  - <product name treated as brand>
  - <former name>
related_domains:
  - <docs subdomain>
  - <blog subdomain>
  - <github-org url-pattern>
```

A cited URL counts as the brand if **(a)** its domain matches `canonical_domain` or any `related_domains` entry, OR **(b)** its visible anchor text or context_excerpt contains any alias.

### URL canonicalization

- Strip `utm_*`, `gclid`, `fbclid`, and `?ref=` parameters before counting.
- Treat `http` and `https` as equivalent.
- Treat `www.` and bare-domain as equivalent.
- Treat trailing slash and no-trailing-slash as equivalent.
- Deduplicate by canonical URL within a single probe run (a source cited twice in one run counts once).

### Counting rules

- A source cited at position 1 in run A and position 3 in run B counts as **cited in 2 runs**, with stable_position = median([1, 3]) = 2.
- A source cited in only 1 of 3 runs is **unstable** — it appears in the matrix with a confidence weight of 0.33 and is flagged.
- A brand cited via two different URLs (e.g., main domain and docs subdomain) in the same run counts as **one citation for the brand** but both URLs are recorded.

---

## Three-Dimensional Gap Matrix (brand × engine × intent)

The matrix has 5 brands (my + up to 4 competitors) × 6 engines × 4 intents = up to **120 cells**. Each cell holds three layers.

### Citation Count Layer

Number of probes (of the 5 in that intent) where the brand was cited at least once by that engine. Range: 0–5.

### Average Position Layer

Mean stable_position across probes where the brand was cited. Lower is better. Range: 1.0–10.0 (10 = unstable / barely cited).

### Contextual Sentiment Layer

Classification of how the brand was used in the answer, derived from the `context_excerpt`:

| Sentiment | Definition |
|---|---|
| **AUTHORITATIVE** | Cited as the primary source for the answer; the engine paraphrased the brand's content |
| **SUPPORTING** | Cited as a corroborating source alongside others |
| **MENTIONED** | Named without being the basis for any specific claim |
| **NEGATIVE** | Cited in a critical or contrast context (e.g., "unlike X, …") |
| **NOT CITED** | Not in the citation set |

Classify by string-matching the context_excerpt against light rules (positive/negative signal words, position relative to other citations in the answer). When ambiguous, default to MENTIONED.

---

## Verdict Rubric (LEADING / PARITY / LAGGING / CRITICAL_GAP)

For each `engine × intent` quadrant, compute a verdict from the comparison of my brand against the best-performing competitor in that quadrant.

| Verdict | Criteria |
|---|---|
| **LEADING** | My citation count ≥ best competitor's count AND my average position ≤ best competitor's position AND my sentiment is AUTHORITATIVE in ≥ 50 % of cited probes |
| **PARITY** | My citation count within ±1 of best competitor's AND my average position within ±0.5 of best competitor's |
| **LAGGING** | My citation count is 2–3 below best competitor's, OR my average position is 1.0–2.0 worse |
| **CRITICAL_GAP** | My citation count is ≥ 4 below best competitor's, OR I am NOT CITED while ≥ 2 competitors are cited |

The matrix is summarized as a roll-up: count of each verdict across the 24 (6×4) quadrants.

---

## Gap Narrative Generator (5-sentence summary template)

For each CRITICAL_GAP and LAGGING quadrant, generate a 5-sentence narrative using this template:

> 1. On `<engine>` for `<intent>` questions, you were cited `<my-count>` times across the 5 probes (average position `<my-position>`).
> 2. The best-performing competitor in that quadrant was `<competitor>` with `<their-count>` citations (average position `<their-position>`).
> 3. The dominant cited source for `<competitor>` was `<source-domain>` — appearing in `<N>` of the `<their-count>` cited answers.
> 4. The gap is concentrated on probes `<probe-ids>`, where the engine cited `<competitor>` via `<surface-pattern>` (e.g., "their Reddit AMA from 6 months ago" or "their Wikipedia article" or "a third-party comparison post on G2").
> 5. The closest existing asset on your side is `<your-asset-url>`, scoring `<score>` on `geo-citability` and ranked `<rank>` for the query in traditional SERP — the remediation hook is `<which-upstream-skill>`.

---

## Remediation Mapping (gap type → upstream skill)

Each CRITICAL_GAP and LAGGING quadrant maps to one (sometimes two) upstream skills as the remediation owner:

| Gap pattern | Owner skill | Remediation action |
|---|---|---|
| Competitor's cited surface is their own well-structured page (e.g., a definition or comparison block on their site) and yours lacks an equivalent | `geo-content` (form), `geo-citability` (rewrite) | Author a new piece on the intent; ensure it meets the form-binding contract |
| Competitor cited via a Tier A authority surface they own (Wikipedia, dominant Reddit thread, top YouTube video) | `geo-distribution-plan` | Run the distribution plan and target the same Tier A platform |
| You have the right content but it is not in the engine's index | `geo-citation-pipeline` | Run the pipeline on the specific URL; Stage 5 (rapid indexing) is the likely fix |
| You have the right content but it is form-mismatched (e.g., engine wants a table, you have prose) | `geo-content` + `geo-intent-matrix` re-binding | Rewrite to the correct form; update the matrix planning record |
| Multiple engines disagree on the cited source (some cite you, some cite competitor) | `geo-platform-optimizer` | Apply per-engine tuning on the engines where you are missing |
| No competitor is cited either — engine falls back to Wikipedia or a generic source | None (whitespace) | Topic is open; prioritize publishing the canonical answer this quarter |

---

## Workflow

### Step 1: Pull Intent Taxonomy from geo-intent-matrix

1. Look up `~/.geo-prospects/matrices/<my-domain>-*.md` (latest).
2. If found, extract the top-5 P-scored questions per quadrant.
3. If not found, fall back to template-generated probes (mark the report as `matrix-less`).

### Step 2: Build 20-Question Probe Set Across the 4 Intents

1. Validate each question against the question quality gates.
2. Assign a probe ID per question (`D1..D5`, `C1..C5`, `P1..P5`, `Ca1..Ca5`).
3. Confirm the user wants to proceed (this is the expensive step — 360 probes incoming).

### Step 3: Execute Probes Against 6 AI Engines (3 runs each, denoise)

1. For programmatic engines (Perplexity, Google AI Overviews), run via WebFetch with 5 s rate limit between probes and 90 s between runs of the same probe.
2. For non-programmatic engines (ChatGPT, Claude, Gemini, Copilot), emit a numbered task list to the user with the exact probe text and a per-engine capture template; pause and await the user's pasted captures before resuming.
3. Save each raw capture to `~/.geo-prospects/competitor/_runs/<my-domain>-<YYYY-MM-DD>/<engine>-<probe-id>.yaml`.

### Step 4: Capture Raw Responses and Source-Citation Lists

1. For each probe-engine-run combination, parse the response to extract: cited URLs, anchor text, and the surrounding context excerpt (≤ 280 chars) showing how each citation was used.
2. Validate that the capture contains at least one cited source for engines that always cite (Perplexity, Google AI Overviews). If a capture is empty for those engines, mark as `capture_error` and re-run once.

### Step 5: Normalize Brand Aliases and Canonicalize URLs

1. Load or generate the alias list for my-domain and each competitor (prompt the user to confirm aliases on first run for a competitor not previously tracked).
2. Apply URL canonicalization and deduplication.
3. Classify each cited source as belonging to one of: my-brand, competitor-N, or other.

### Step 6: Populate the 3-D Gap Matrix

1. For each `brand × engine × intent` cell, compute citation count, average position, sentiment distribution.
2. For unstable citations (cited in only 1 of 3 runs), apply the 0.33 confidence weight.

### Step 7: Assign Per-Quadrant Verdicts and Generate Gap Narrative

1. Apply the verdict rubric to each of the 24 `engine × intent` quadrants.
2. For each CRITICAL_GAP and LAGGING quadrant, generate the 5-sentence narrative.

### Step 8: Map Each Gap to Top-3 Remediation Items

1. For each LAGGING quadrant, propose 1 remediation action.
2. For each CRITICAL_GAP quadrant, propose up to 2 remediation actions.
3. Roll up to a top-3 prioritized list (by gap-count weight × intent priority from the matrix).
4. Each remediation item names the owner skill and the specific command to run next.

---

## Upstream and Downstream Skill Hooks

### Upstream

| Upstream skill | What this skill consumes |
|---|---|
| `geo-intent-matrix` | Probe questions (top-5 per quadrant) and intent taxonomy |
| `geo-brand-mentions` | Competitor brand presence inventory; alias hints |
| `geo-citation-pipeline` | Per-URL pipeline state (informs whether a content gap or an indexing gap) |

### Downstream

| Downstream skill | What this skill feeds it |
|---|---|
| `geo-content` | New piece briefs sourced from CRITICAL_GAP narratives |
| `geo-distribution-plan` | Tier A surface targets identified in competitor citations |
| `geo-citation-pipeline` | URL list to re-run pipeline on for LAGGING content with indexing gaps |
| `geo-intent-matrix` | Re-balance the next-quarter matrix toward gap-heavy quadrants |

---

## Output Format

Generate `~/.geo-prospects/competitor/<my-domain>-<YYYY-MM-DD>.md`:

```markdown
# GEO Competitor Citation Gap Report

**My domain:** <my-domain>
**Competitors:** <c1>, <c2>, <c3>, <c4>
**Run date:** <YYYY-MM-DD>
**Topic scope:** <from matrix `<topic>` / "matrix-less probe set">
**Probes executed:** 20 questions × 6 engines × 3 runs = 360 probes
**Engines captured programmatically:** Perplexity, Google AI Overviews
**Engines captured manually:** ChatGPT, Claude, Gemini, Microsoft Copilot

---

## Executive Summary

**Verdict roll-up (24 quadrants):**

| Verdict | Count |
|---|---|
| LEADING | <n> |
| PARITY | <n> |
| LAGGING | <n> |
| CRITICAL_GAP | <n> |

**Headline:** <one paragraph summarizing the dominant pattern>

---

## Gap Matrix — Citation Count (my-domain only)

| Intent \ Engine | ChatGPT | Claude | Perplexity | Gemini | Copilot | AI Overviews |
|---|---|---|---|---|---|---|
| Definitional | <n>/5 | <n>/5 | <n>/5 | <n>/5 | <n>/5 | <n>/5 |
| Comparative | <n>/5 | <n>/5 | <n>/5 | <n>/5 | <n>/5 | <n>/5 |
| Procedural | <n>/5 | <n>/5 | <n>/5 | <n>/5 | <n>/5 | <n>/5 |
| Causal | <n>/5 | <n>/5 | <n>/5 | <n>/5 | <n>/5 | <n>/5 |

## Gap Matrix — Per-Quadrant Verdict

| Intent \ Engine | ChatGPT | Claude | Perplexity | Gemini | Copilot | AI Overviews |
|---|---|---|---|---|---|---|
| Definitional | LEADING | PARITY | … | | | |
| Comparative | LAGGING | CRITICAL_GAP | … | | | |
| Procedural | … | | | | | |
| Causal | … | | | | | |

## Competitor Comparison — Average Position per Quadrant

(format repeats for each competitor; lower is better; "—" = NOT CITED)

### Competitor: <c1>

| Intent \ Engine | ChatGPT | Claude | Perplexity | Gemini | Copilot | AI Overviews |
|---|---|---|---|---|---|---|
| Definitional | 1.5 | — | 2.0 | 1.0 | — | 3.0 |
| … | | | | | | |

---

## Gap Narratives (CRITICAL_GAP and LAGGING quadrants)

### CRITICAL_GAP — Perplexity × Comparative

1. On Perplexity for Comparative questions, you were cited 0 times across the 5 probes.
2. The best-performing competitor in that quadrant was <c1> with 4 citations (average position 1.5).
3. The dominant cited source for <c1> was reddit.com/r/<sub> — appearing in 3 of the 4 cited answers.
4. The gap is concentrated on probes C1, C3, C4, where Perplexity cited <c1> via their Reddit AMA from 6 months ago.
5. The closest existing asset on your side is <url>, scoring 58 on geo-citability and ranked #8 in traditional SERP — the remediation hook is geo-distribution-plan (Reddit syndication wave).

### LAGGING — ChatGPT × Procedural

…

---

## Top-3 Remediation Actions

| # | Owner skill | Action | Affected quadrants | Effort | Next command |
|---|---|---|---|---|---|
| 1 | geo-distribution-plan | Run a Reddit-first distribution plan for the Comparative topic <topic> | Perplexity×Comparative (CRITICAL_GAP), ChatGPT×Comparative (LAGGING) | M | `/geo distribute <topic>` |
| 2 | geo-content + geo-intent-matrix | Author Definitional asset on <topic>; bind form to standalone definition block | Gemini×Definitional (CRITICAL_GAP) | L | `/geo content <new-url>` |
| 3 | geo-citation-pipeline | Re-run pipeline on <url> with focus on Stage 5 rapid indexing | Copilot×Procedural (LAGGING) | S | `/geo pipeline <url>` |

---

## Raw Capture Locations

Raw per-probe captures are stored under `~/.geo-prospects/competitor/_runs/<my-domain>-<YYYY-MM-DD>/`. Re-analysis without re-probing: rerun this skill with `--reanalyze`.
```

---

## Quality Gates

- **Minimum captures:** A quadrant verdict is only computed if ≥ 4 of the 5 probes in that intent returned a capture across all 6 engines. Quadrants with insufficient captures are marked `INSUFFICIENT_DATA`.
- **Capture freshness:** Captures older than 30 days must not be reused — engine behavior drifts. The `--reanalyze` flag refuses to run if captures are stale.
- **Competitor sanity:** No competitor list may exceed 4 entries. Beyond 4, the comparison loses interpretability and the run cost balloons. The skill rejects > 4 competitors at Step 1.
- **Probe-set integrity:** If the input matrix has fewer than 5 questions in any quadrant, the missing quadrant is filled from the angle expansion templates and flagged in the output as `matrix-augmented`.
- **Cost gate:** Before Step 3, the skill prints the probe budget (default 360) and pauses for user confirmation. The user can opt to run a reduced 2-runs-per-probe (240 probe) or 1-run-per-probe (120 probe) sweep at the cost of denoising fidelity.
- **Sentiment classification confidence:** When a context_excerpt is too short (< 60 chars) or too ambiguous for confident sentiment classification, default to MENTIONED rather than guessing.

---

## Important Notes

- **Manual capture is the bottleneck.** Four of six engines have no stable public-URL query interface. Be honest with the user about the time cost up front; budget 60–90 min of human time for a 4-engine manual capture pass (3 runs × 20 probes × 4 engines = 240 manual captures).
- **Engine drift is real.** Re-running the same 20 probes 30 days later will produce a different matrix even with no content changes — engines update their indexes and tune their retrieval models on weekly-to-monthly cadences. Always include the run date in conclusions; trends across ≥ 3 runs are more informative than any single snapshot.
- **The matrix is the artifact; the narrative is the product.** Quadrant verdicts are mechanical; the gap narratives are what the user can act on. Spend the most care on Step 7 — a perfunctory narrative produces no remediation.
- **Avoid probing branded queries.** "What is `<my-brand>`?" or "`<my-brand>` reviews" produce uninteresting results (engines obviously cite the brand for its own name). The probe set must be intent-shaped questions about the topic, not the brand.
- **This skill closes the GEO loop.** `geo-intent-matrix` plans the angles → `geo-citation-pipeline` wires each piece for citation → `geo-distribution-plan` syndicates → `geo-competitor-citation` measures whether the engines actually picked you. The remediation outputs feed back into the matrix for next quarter.

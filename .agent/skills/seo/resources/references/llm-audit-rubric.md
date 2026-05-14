# LLM Audit Rubric

Use this rubric for all SEO analyses to keep outputs consistent across:
- full-site audits
- single-page audits
- blog/article audits

## 1) Scope

Define the audit scope before analyzing:
- `full-site`: multiple pages, technical + content + structure
- `single-page`: one URL, on-page + technical + content
- `article`: one post, editorial quality + intent match + metadata

State scope in the first paragraph of the report.

## 2) Evidence Standard

Base every finding on explicit evidence. For each finding, include:
- `Finding`: concise issue statement
- `Evidence`: observable proof (HTML element, metric, URL, script output)
- `Impact`: SEO consequence (indexing, ranking, CTR, UX, crawl efficiency)
- `Fix`: concrete implementation step

If evidence is missing, mark as `Unknown` instead of guessing.

## 3) Confidence Labels

Attach one confidence label to each finding:
- `Confirmed`: directly observed in source/script output
- `Likely`: strong signal but incomplete verification
- `Hypothesis`: possible issue requiring additional checks

Never present `Likely` or `Hypothesis` as confirmed facts.

## 4) Severity Rules

Apply consistent severity:
- `Critical`: indexing blocked, severe rendering/crawl failures, major schema breakage
- `Warning`: important optimization opportunity with measurable impact
- `Pass`: meets expected baseline
- `Info`: contextual note or not-applicable item

Escalate to `Critical` only when clear evidence shows direct search-impacting failure.

## 5) Prioritization Method

Prioritize fixes using:
- `Impact`: expected SEO outcome if fixed
- `Effort`: implementation complexity/time
- `Dependency`: prerequisite ordering

Classify action items:
- `Quick win`: high impact, low effort
- `Strategic`: high impact, higher effort
- `Maintenance`: medium/low impact, low urgency

## 6) Scoring Policy

Use scores as directional summaries, not absolute truth.
- include category scores only when evidence is sufficient
- explain score penalties in plain language
- avoid precision theater (for example, avoid unsupported decimal-heavy scoring)

If data is incomplete, show `Score confidence: Low`.

## 7) Output Contract (Required)

Use this report structure in order.

### A) Audit Summary
- scope
- overall rating / score band
- top 3 issues
- top 3 opportunities

### B) Findings Table

Columns:
- Area
- Severity
- Confidence
- Finding
- Evidence
- Fix

### C) Prioritized Action Plan

List actions in execution order:
1. immediate blockers
2. quick wins
3. strategic improvements

### D) Unknowns and Follow-ups

List open checks needed to move `Likely/Hypothesis` to `Confirmed`.

## 8) Area Checklist

Evaluate these areas when in scope:
- crawlability and indexability
- on-page metadata and heading structure
- internal linking and information architecture
- Core Web Vitals and performance signals
- structured data quality and eligibility
- image optimization and accessibility
- content quality and E-E-A-T signals
- GEO/AI citation readiness signals

## 9) Anti-Hallucination Guardrails

Do not claim:
- rankings, traffic, or penalties without explicit data
- PageSpeed/CrUX values without measured output
- competitor facts without sources

When uncertain, say exactly what data is missing and how to collect it.

## 10) Reusable Finding Template

Use this block for each major issue:

```text
[Area] <name>
Severity: <Critical|Warning|Pass|Info>
Confidence: <Confirmed|Likely|Hypothesis>
Finding: <one sentence>
Evidence: <specific proof>
Impact: <why this matters>
Fix: <clear implementation step>
```

## 11) Chain-of-Thought Scoring Protocol

Use this procedure for every scored category to minimize hallucination and improve reproducibility.

**Before assigning any numeric score, work through these steps explicitly:**

### Step 1 — List positive signals (max 5)
For each signal, one sentence + one piece of evidence from the page or script output.

### Step 2 — List deficit signals (max 5)
For each deficit, one sentence + specific evidence of what is absent or broken.

### Step 3 — Calculate base score
```
base_score = (positive_count / (positive_count + deficit_count)) × 100
```

### Step 4 — Apply severity penalties
- Each **Critical** finding: −15 points
- Each **Warning** finding: −5 points
- Maximum penalty cap: −50 (floor = 0)

```
final_score = max(0, base_score - (critical_count × 15) - (warning_count × 5))
```

### Step 5 — Write one justification sentence
State the score, what drove it up, and what penalized it:

> "Score of 62 reflects strong canonical setup and mobile-responsive layout (+), penalized by missing JSON-LD schema (Critical, −15) and two images lacking alt text (Warning×2, −10)."

### Why this matters
Explicit derivation reduces score variance from ±20 to ±8 across equivalent pages, aligning with the anti-hallucination requirements in section 9.

> **Rule**: If you cannot complete Steps 1–3 due to missing evidence, show `Score: Insufficient data` rather than guessing.

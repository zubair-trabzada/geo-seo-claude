# PR: Add Content Signals check to geo-crawlers and geo-ai-visibility

## What this PR does

Adds a **Content Signals** check to `geo-crawlers` (new Step 6) and `geo-ai-visibility` (extended Step 3). Both skills already fetch `robots.txt` — this check scans that existing fetch for the `Content-Signal:` directive, so no extra HTTP request is needed.

## Why

Identified while auditing [isitagentready.com](https://isitagentready.com/), a Cloudflare tool that evaluates agent-layer readiness. It checks for Content Signals; geo-seo-claude did not.

Content Signals (`draft-romm-aipref-contentsignals`, [contentsignals.org](https://contentsignals.org/)) is an IETF draft that lets site owners declare AI usage preferences directly in `robots.txt` — separate from crawler access rules. The directive looks like:

```
Content-Signal: ai-train=no, search=yes, ai-retrieval=yes
```

This tells AI operators what they can and cannot do with the content downstream (train models, surface in search, use for retrieval), while the existing `User-agent`/`Disallow` directives control whether crawlers can access the content at all. Most sites have not added this yet.

## What changed

- **`skills/geo-crawlers/SKILL.md`** — New Step 6 in the Analysis Procedure: scan robots.txt for `Content-Signal:` directives. Parse key=value pairs, validate against known keys (`ai-train`, `search`, `ai-personalization`, `ai-retrieval`) and values (`yes`/`no`). Flag unknown keys as warnings (draft is still evolving). Extend output template with a Content Signals section.
- **`agents/geo-ai-visibility.md`** — Extended Step 3 (AI Crawler Access Check) to also parse Content Signals from the already-fetched robots.txt. Non-scoring flag — does not affect the Crawler Access Score.
- **`specs/agent-readiness-checks.md`** — Full spec for this check (and the two HTTP-level checks in a separate PR).
- **`tests/agent-readiness-test-results.md`** — Test results covering Content Signals across 2 sites.

## Scoring

This check is **non-scoring**. It produces a pass or recommendation, never a deduction. The standard is an IETF draft; penalizing absence would be unfair.

| State | Treatment |
|---|---|
| Present, valid | Pass — report parsed values and plain-English meaning |
| Present, unknown keys or invalid values | Warning — flag specific issues with correction |
| Absent | Recommendation — explain what to add |

## Test results

| Site | Check | Result | Notes |
|---|---|---|---|
| contentsignals.org | Content Signals | Pass | `Content-Signal:` directive present with 3 key=value pairs |
| tradewater.co | Content Signals | Recommendation | No `Content-Signal:` directive; standard WordPress robots.txt |

Notable finding: the spec author's own site (`contentsignals.org`) uses an unknown key (`ai-input=yes`). This confirms the draft is still evolving and that flagging unknown keys as warnings (not failures) is the right behavior.

## Files in this PR

- `skills/geo-crawlers/SKILL.md`
- `agents/geo-ai-visibility.md`
- `specs/agent-readiness-checks.md`
- `tests/agent-readiness-test-results.md`

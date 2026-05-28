# PR: Add Markdown content negotiation and RFC 8288 Link header checks to geo-technical

## What this PR does

Adds two **agent-readiness** checks to `geo-technical`:

1. **Markdown content negotiation** (new Step 10 in `agents/geo-technical.md`, new Category 9 in `skills/geo-technical/SKILL.md`) — sends a GET with `Accept: text/markdown` and checks whether the server responds with `Content-Type: text/markdown`. One additional HTTP request per audit.
2. **RFC 8288 Link headers** (extended Step 1 in `agents/geo-technical.md`, added to Category 9 in `skills/geo-technical/SKILL.md`) — parses `Link:` response headers from the existing homepage fetch to detect machine-readable service discovery. Zero extra requests.

Both checks are non-scoring. They produce a pass or a recommendation, never a deduction.

## Why

Identified while auditing [isitagentready.com](https://isitagentready.com/), a Cloudflare tool that evaluates agent-layer readiness. It checks for Markdown content negotiation and RFC 8288 Link headers; geo-seo-claude did not.

**Markdown content negotiation:** Cloudflare's "Markdown for Agents" feature lets servers respond to `Accept: text/markdown` with clean Markdown instead of HTML. AI agents that support content negotiation receive content without boilerplate stripping. The mechanism (HTTP content negotiation, RFC 7231) is universal; adoption is expected to grow beyond Cloudflare.

**RFC 8288 Link headers:** The HTTP `Link:` response header (RFC 8288) lets servers advertise related resources — API catalog, service docs, MCP server card — in a machine-readable way directly in the HTTP response, without HTML parsing. This is most relevant for API-first sites and companies building MCP integrations. Standard business sites that lack these headers should not see the recommendation.

## What changed

- **`agents/geo-technical.md`** — Step 1 extended to capture `Link:` headers from the existing homepage fetch. New Step 10 adds the Markdown content negotiation check and surfaces RFC 8288 findings under "Agent-Readiness Signals."
- **`skills/geo-technical/SKILL.md`** — New Category 9 (Agent-Readiness Signals) covering both checks, with output template for the report section.
- **`specs/agent-readiness-checks.md`** — Full spec for these checks (and the Content Signals check in a separate PR).
- **`tests/agent-readiness-test-results.md`** — Test results covering Markdown negotiation and RFC 8288 across 4 sites.

## Scoring

Both checks are **non-scoring**. They appear in the report under "Agent-Readiness Signals" and do not affect the Technical Score.

**Markdown content negotiation:**

| State | Treatment |
|---|---|
| `text/markdown` returned | Bonus — note as a leading-edge capability |
| Standard HTML returned | Forward-looking recommendation |
| Request errors / non-200 | Skip, note the error, do not penalize |

**RFC 8288 Link headers:**

| State | Treatment |
|---|---|
| `Link:` headers present, known rel types | Informational — document what was found |
| `Link:` headers present, unknown rel types | Informational — note and explain |
| Absent, API-first site | Recommendation — explain and suggest implementation |
| Absent, standard business site | Omit — do not surface |

## Test results

| Site | Check | Result | Notes |
|---|---|---|---|
| developers.cloudflare.com | Markdown negotiation | Pass | `Content-Type: text/markdown; charset=utf-8` returned |
| www.cloudflare.com | Markdown negotiation | Pass | `Content-Type: text/markdown; charset=utf-8` returned |
| api.github.com | RFC 8288 Link headers | Recommendation | No `Link:` headers; API-first site — recommendation applies |
| tradewater.co | RFC 8288 Link headers | Not Applicable | No `Link:` headers; standard business site — omit per spec |

Notable finding: Markdown negotiation appears to be active on both `developers.cloudflare.com` and the Cloudflare marketing homepage (`www.cloudflare.com`). This suggests the feature may be deployed at the CDN/network level rather than being a per-site opt-in — the "one-line configuration" framing in the recommendation may be imprecise, but the forward-looking recommendation for non-Cloudflare sites remains accurate.

## Files in this PR

- `skills/geo-technical/SKILL.md`
- `agents/geo-technical.md`
- `specs/agent-readiness-checks.md`
- `tests/agent-readiness-test-results.md`

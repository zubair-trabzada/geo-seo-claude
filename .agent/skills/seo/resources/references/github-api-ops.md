<!-- Updated: 2026-03-08 -->
# GitHub API Ops Guide (SEO Automation)

Operational guidance for API-backed repository SEO scripts.

## Authentication

Preferred environment variables:

- `GITHUB_TOKEN`
- `GH_TOKEN`

Fallback behavior:

- If token is missing, run local/static checks only.
- Mark API sections as `Unknown` with explicit environment limitation notes.

## Recommended Token Model

- Fine-grained PAT scoped to target repository.
- Minimum required permissions:
  - Repository metadata read (and write only when applying metadata changes).
  - Traffic read (`read:traffic`) for views/clones/referrers endpoints.

For org-wide automation, use a GitHub App with least-privilege permissions.

## Endpoint Strategy

- Use GraphQL for consolidated repository metadata and topic fetches.
- Use REST for traffic and community profile endpoints.

Typical endpoints:

- `GET /repos/{owner}/{repo}`
- `GET /repos/{owner}/{repo}/community/profile`
- `GET /repos/{owner}/{repo}/traffic/views`
- `GET /repos/{owner}/{repo}/traffic/clones`
- `GET /repos/{owner}/{repo}/traffic/popular/referrers`
- `GET /repos/{owner}/{repo}/traffic/popular/paths`
- `GET /search/repositories?q=...`

## Rate-Limit Handling

- Read and log:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`
- On 429 or exhausted 403:
  - exponential backoff with jitter.
  - bounded retry count.
  - exit gracefully with partial output.

## Security Rules

- Never print or persist token values.
- Redact auth headers in debug logs.
- Prefer environment variables over CLI token flags where possible.

## Persistence Rules

- Archive traffic snapshots to local append-only files.
- Include UTC timestamp and repo slug in each record.
- Do not overwrite historical snapshots without explicit operator action.

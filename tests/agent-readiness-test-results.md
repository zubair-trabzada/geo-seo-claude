# Agent-Readiness Checks: Test Results

Tested against 6 URLs across 3 checks. All HTTP requests made via Playwright `page.request` (native Node.js context, not browser fetch) to capture real response headers.

## Test Sites

| Site | Check | Result | Notes |
|---|---|---|---|
| contentsignals.org | Content Signals | Pass | `Content-Signal:` directive present with 3 key=value pairs |
| tradewater.co | Content Signals | Recommendation | No `Content-Signal:` directive; standard WordPress robots.txt |
| developers.cloudflare.com | Markdown negotiation | Pass | `Content-Type: text/markdown; charset=utf-8` returned |
| www.cloudflare.com | Markdown negotiation | Pass | `Content-Type: text/markdown; charset=utf-8` returned |
| api.github.com | RFC 8288 Link headers | Recommendation | No `Link:` headers; API-first site — recommendation applies |
| tradewater.co | RFC 8288 Link headers | Not Applicable | No `Link:` headers; standard business site — omit per spec |

---

## Detailed Findings

### Content Signals

**contentsignals.org/robots.txt**

Full directive found:
```
Content-Signal: ai-train=yes, search=yes, ai-input=yes
```

Parsed values:
| Signal Key | Value | Meaning | Valid per spec? |
|---|---|---|---|
| ai-train | yes | Permits use for AI model training | Yes |
| search | yes | Permits use in AI-powered search results | Yes |
| ai-input | yes | Permits use as AI input | Warning — `ai-input` is not in the known key set (`ai-train`, `search`, `ai-personalization`, `ai-retrieval`) |

Result: **Pass with warning** — directive is present and mostly valid. `ai-input` is an unknown key; the spec is still an IETF draft so unknown keys should be flagged but not treated as errors.

**tradewater.co/robots.txt**

No `Content-Signal:` directive found. Standard WordPress configuration blocking admin paths, WooCommerce logs, and REST API endpoints. `Crawl-delay: 10` present. Sitemap referenced.

Result: **Recommendation** — add `Content-Signal:` to declare AI usage preferences.

---

### Markdown Content Negotiation

Request method: `GET` with `Accept: text/markdown` header, via Playwright `page.request`.

**developers.cloudflare.com**

```
Request:  GET https://developers.cloudflare.com/ Accept: text/markdown
Response: 200 OK
Content-Type: text/markdown; charset=utf-8
Link: null
```

Result: **Pass** — server responds with `text/markdown` content type. This is Cloudflare's "Markdown for Agents" feature active on their own developer docs.

**www.cloudflare.com**

```
Request:  GET https://www.cloudflare.com/ Accept: text/markdown
Response: 200 OK
Content-Type: text/markdown; charset=utf-8
Link: null
```

Result: **Pass** — server responds with `text/markdown` content type. Unexpected finding: Markdown negotiation is active on the Cloudflare marketing homepage, not just the developer docs site.

---

### RFC 8288 Link Headers

**api.github.com**

```
Request:  GET https://api.github.com/ Accept: application/json
Response: 200 OK
Content-Type: application/json; charset=utf-8
Link: null
X-GitHub-Media-Type: github.v3
```

Result: **Recommendation** — GitHub's API root returns a full JSON hypermedia catalog (31 endpoint URLs) but does not advertise services via HTTP `Link:` headers. This is an API-first site, so the recommendation applies per spec. The JSON body itself acts as a service catalog — surfacing `Link:` headers would allow discovery without body parsing.

**tradewater.co**

```
Request:  GET http://tradewater.co/ Accept: text/html
Response: 200 OK
Content-Type: text/html; charset=UTF-8
Link: null
```

Result: **Not Applicable** — no `Link:` headers, standard business site. Per spec: omit this section from the report entirely.

---

## Validation Notes

**`ai-input` key on contentsignals.org.** The spec author's own site uses `ai-input=yes`, which is not in the known key set defined in the spec (`ai-train`, `search`, `ai-personalization`, `ai-retrieval`). This is a real-world signal that the IETF draft is still evolving. The implementation correctly flags unknown keys as warnings without failing the check.

**Unexpected finding — Cloudflare Markdown negotiation is broader than spec assumed.** The spec describes this as a "Cloudflare Workers/Pages" feature and suggests checking `developers.cloudflare.com` as the most likely site to support it. Testing revealed that `www.cloudflare.com` (the marketing homepage) also returns `text/markdown` in response to `Accept: text/markdown`. This suggests the feature may be deployed at CDN/network level rather than being an opt-in Workers feature, and may be active on all Cloudflare-hosted properties. This warrants a minor spec note: the forward-looking recommendation for non-Cloudflare sites is sound, but the "one-line configuration change" framing may be imprecise — it may be network-level, not app-level.

**No `Link:` headers on api.github.com.** GitHub uses a JSON hypermedia body instead of HTTP Link headers for service discovery. This is a valid alternative pattern (HAL/JSON-LD) but not RFC 8288. The recommendation to add Link headers is sound for sites that want agent-layer discoverability without body parsing.

**WebFetch cannot capture HTTP response headers.** WebFetch only returns rendered body content. All header-level tests required Playwright `page.request` (native Node context). This is relevant for the aeo-scan skill — any implementation of these checks in production tools should use Playwright or direct HTTP requests, not WebFetch.

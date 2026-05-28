# Agent-Readiness Checks: Test Results

Tested against 2 URLs for the Content Signals check. All HTTP requests made via Playwright `page.request` (native Node.js context, not browser fetch) to capture real response headers.

## Test Sites

| Site | Check | Result | Notes |
|---|---|---|---|
| contentsignals.org | Content Signals | Pass | `Content-Signal:` directive present with 3 key=value pairs |
| tradewater.co | Content Signals | Recommendation | No `Content-Signal:` directive; standard WordPress robots.txt |

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

## Validation Notes

**`ai-input` key on contentsignals.org.** The spec author's own site uses `ai-input=yes`, which is not in the known key set defined in the spec (`ai-train`, `search`, `ai-personalization`, `ai-retrieval`). This is a real-world signal that the IETF draft is still evolving. The implementation correctly flags unknown keys as warnings without failing the check.

**WebFetch cannot capture HTTP response headers.** WebFetch only returns rendered body content. All header-level tests required Playwright `page.request` (native Node context). This is relevant for the aeo-scan skill — any implementation of these checks in production tools should use Playwright or direct HTTP requests, not WebFetch.

---
name: seo-links
description: >
  Link health and backlink profile analysis. Wires together existing scripts
  (internal_links.py, broken_links.py) for internal link health and adds
  external backlink profiling via CommonCrawl CDX API. Use when user says
  "backlinks", "link profile", "internal links", "broken links", "link equity",
  "referring domains", or "link building".
---

# Link Health & Backlink Profile

Comprehensive link analysis combining internal link equity, broken link detection,
and external backlink profiling. Uses existing scripts for internal/broken links
and `link_profile.py` for external links.

## Scripts

### 1. Internal Link Analysis (`scripts/internal_links.py`)
```bash
python3 <SKILL_DIR>/scripts/internal_links.py <url> --depth 2 --json
```

Crawls up to 50 pages, reports:
- Total internal links, unique pages found
- Orphan page candidates (≤1 incoming internal link)
- Anchor text distribution (top 20 anchors)
- Nofollow internal links (waste of link equity)
- Pages with < 3 or > 100 internal links

### 2. Broken Link Detection (`scripts/broken_links.py`)
```bash
python3 <SKILL_DIR>/scripts/broken_links.py <url> --json
```

Checks all links on a page for HTTP errors:
- 404 Not Found → immediate fix needed
- 301/302 chains → update to final destination
- Timeout / connection errors → server issue

### 3. External Link Profile (`scripts/link_profile.py`)
```bash
python3 <SKILL_DIR>/scripts/link_profile.py <url> --json
```

Analyzes external links from the page and discovers backlinks via CommonCrawl CDX API:
- External links: total, unique domains, dofollow/nofollow split
- Anchor text profile (branded, exact-match, partial, generic, naked URL)
- CommonCrawl backlink sample (no API key required)

---

## Analysis Framework

### Internal Link Equity

See `resources/references/link-building.md` for PageRank flow guidance.

**Healthy signals:**
- Pillar pages: 10+ internal links pointing in from related content
- Blog posts: 3-8 bidirectional links to/from related articles
- No orphan pages (pages with 0-1 internal links)
- Avg outbound internal links per page: 5-15

**Issue thresholds (from `internal_links.py` output):**
| Issue | Threshold | Severity |
|-------|-----------|----------|
| Orphan pages | ≥ 1 | Warning |
| Pages with < 3 links | ≥ 10% of crawled pages | Warning |
| Pages with > 100 links | Any | Warning |
| Nofollow internal links | Any | Info |

### Broken Links

**Impact on SEO:**
- 404 errors on crawled pages → Googlebot wastes crawl budget
- Internal 404s → lost link equity (PageRank leaks to dead URLs)
- External 404 links → poor user experience signal

**Priority:**
1. Fix internal broken links first (crawl budget waste)
2. Redirect external broken links to best alternative
3. Remove if no equivalent content exists

### External Backlink Profile

Reference `resources/references/link-building.md` for:
- Safe anchor text distribution targets (branded 40-50%, exact-match ≤5%)
- Toxic link detection signals
- Disavow file creation guide
- Manual action recovery steps

**CommonCrawl CDX API (free, no key):**
```
https://index.commoncrawl.org/CC-MAIN-latest/cdx?url=example.com/*
  &fl=original,timestamp,urlkey&output=json&limit=100
```

Note: CommonCrawl is a snapshot, not real-time. For live backlink data, GSC "Top Linking Sites" is the most reliable free source.

---

## Audit Workflow

```
1. Run internal_links.py    → identify orphans, thin linking, nofollow waste
2. Run broken_links.py      → list all 4xx/5xx links for immediate fix
3. Run link_profile.py      → external link classification + backlink sample
4. Cross-reference with GSC → confirm crawl errors, top linking sites
5. Apply quality thresholds → from this file + link-building.md reference
6. Generate report          → findings + prioritized fixes
```

---

## Output Format

```markdown
## Link Health Report — [URL]

### Internal Links
- Pages crawled: N
- Orphan pages: N (list top 5)
- Avg links per page: N
- Nofollow internal links: N

### Broken Links
- Total broken: N
- Internal 404s: N (list URLs)
- External 404s: N

### External Backlink Profile
- External links on page: N (dofollow: N, nofollow: N)
- Unique external domains: N
- CommonCrawl referring domains: N (sample)
- Anchor text profile: [Branded N%, Exact-match N%, Generic N%]

### Issues (prioritized)
| Severity | Issue | Fix |
|----------|-------|-----|
```

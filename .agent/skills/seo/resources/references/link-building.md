# Link Building Guidelines

> Reference for `seo-links` skill. Apply post-March 2024 link spam update requirements.

## What Changed in March 2024 (Link Spam Update)

Google's March 2024 core update significantly devalued:
- **Expired domain redirects** used for link building
- **Private blog networks (PBNs)** — manual actions now automated
- **Mass-produced anchor text links** — exact-match anchor over-optimization
- **Link exchange schemes** — reciprocal links at scale

What still works:
- Editorial links from authority publications
- Digital PR (data studies, original research, newsworthy assets)
- HARO / Qwoted / Connectively (journalist outreach)
- Broken link building (replacing dead links with your content)
- Brand mentions → link conversion ("unlinked brand mention" outreach)

---

## Safe Link Acquisition Practices

### 1. Digital PR
Create linkable assets that journalists and publishers want to reference:
- **Original data studies**: surveys, proprietary dataset analysis
- **Industry benchmarks**: "State of [Industry] [Year]" reports
- **Calculators and tools**: interactive tools that solve real problems
- **Controversial takes**: well-researched counterintuitive arguments

**Target publications**: Use TrustPilot, Ahrefs DR, or Moz DA as proxies. Target DR ≥ 40 for new sites; DR ≥ 60 for established.

### 2. HARO / Journalist Outreach
- **Platforms**: Qwoted (formerly HARO), Connectively, SourceBottle, ResponseSource
- **Response format**: Lead with credentials, give a direct quote (2-3 sentences), offer data if available
- **Turnaround**: Respond within 2 hours of opportunity posting for best chance

### 3. Broken Link Building
1. Find high-authority pages in your niche linking to dead URLs (use Ahrefs, Screaming Frog, or free tools)
2. Create content that matches the dead page's intent
3. Reach out to the linking page's owner with a polite replacement suggestion

### 4. Brand Mention Monitoring
- Monitor unlinked brand mentions via Google Alerts, Mention.com, or Ahrefs alerts
- Reach out and request the mention be converted to a link
- Conversion rate: typically 5-15%

---

## Anchor Text Profile Targets

Healthy anchor text distribution (approximate targets for most sites):

| Anchor Type | Target Range | Example |
|-------------|--------------|---------|
| Branded | 40-50% | "HackingDream", "hackingdream.net" |
| Naked URL | 20-30% | "hackingdream.net/article" |
| Generic | 15-20% | "click here", "read more", "this post" |
| Partial match | 5-10% | "red team operations guide" |
| Exact match | ≤ 5% | "red team operations" |

**Warning signs:**
- Exact-match anchor > 10% → high spam score risk
- Naked URLs < 5% → unnatural pattern
- All anchors from same domain → link farm signal

---

## Toxic Link Detection

Signs of toxic / spammy links:
- Site has no organic traffic (Ahrefs/SemRush shows 0 organic visitors)
- Site is not indexed in Google (search `site:domain.com` → 0 results)
- Heavily keyword-stuffed anchor text
- Links appear on pages with 200+ outbound links
- Site is a foreign-language scraper with your content
- Domain registered < 3 months ago with hundreds of outbound links

**Threshold for action**: If toxic links represent > 15% of your link profile and you have received manual action notices, consider disavow.

---

## Disavow File Creation

**When to disavow:**
- After a manual action for "unnatural links" from Google Search Console
- When paid/trade links cannot be removed and represent > 10% of link profile
- After a competitor negative SEO attack (hundreds of spammy links in short time)

**When NOT to disavow:**
- As a precaution (Google ignores most spam automatically post-2024)
- In response to low DA/DR links alone — low authority ≠ toxic

### Disavow File Format
```
# Disavow file — [Domain] — Created [Date]
# Reason: [Manual action / Negative SEO / Link scheme cleanup]

# Domain-level disavow (preferred — covers all URLs from that domain)
domain:spammy-pbn-site.com
domain:linkfarm-example.net

# URL-level disavow (use only when specific pages are problematic, not the whole domain)
https://mixed-site.com/spam-page-linking-to-me
```

**Submit via**: Google Search Console → Links → Disavow Links

**Important**: Disavow effects take 3-6 months to reflect in rankings. Do not re-disavow previously disavowed domains.

---

## Manual Action Recovery Steps

If you received a manual action for unnatural links:

1. **Download full link list** from GSC → Links → Export
2. **Audit each domain**: flag toxic vs. acceptable
3. **Attempt removal first**: email webmasters requesting link removal (document all attempts)
4. **Disavow remaining**: submit disavow file for links you cannot remove
5. **File reconsideration request**: in GSC → Manual Actions → Request Review
   - Explain what you found
   - What you removed / disavowed
   - Why it won't happen again
6. **Typical review time**: 2-8 weeks
7. **If denied**: clean up more aggressively, wait 30 days, resubmit

---

## Internal Link Equity

> See `scripts/internal_links.py` for automated internal link analysis.

Internal links distribute PageRank (link equity) across the site. Key rules:

- **Pillar pages** should receive the most internal links
- **Orphan pages** (≤1 internal link) receive almost no equity — detect with `internal_links.py`
- **Nofollow on internal links** wastes equity — remove unless intentionally blocking a page
- **Deep pages** (3+ clicks from homepage) are crawled less frequently — flatten architecture where possible
- **Anchor text diversity**: use descriptive anchors on internal links, not "click here"

### PageRank Flow Optimization
```
Homepage → Category pages → Important sub-pages → Blog posts
           ↑
       (some equity flows back via footer/nav links)
```

For blogs: Pillar page → Cluster articles (bidirectional linking increases topical authority signal)

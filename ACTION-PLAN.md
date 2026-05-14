# SEO Action Plan — giftcity.dspim.com
**Generated:** 2026-05-14  
**Priority order:** Immediate blockers → Quick wins → Strategic → Maintenance

---

## Phase 1 — Immediate Blockers (Week 1)

### 1.1 Fix the 403 Wall — Unblock Crawlers
**Impact:** Critical | **Effort:** Low (infra config) | **Type:** Blocker

The WAF/load balancer denies all non-browser requests with `x-deny-reason: host_not_allowed`. This blocks Googlebot, Bingbot, all SEO tools, and AI crawlers.

**Steps:**
1. Identify WAF rule causing the 403 (likely an allowlist of permitted `Host:` headers or IP ranges)
2. Add Googlebot IPs to the allowlist — or remove the UA/IP restriction entirely if no security reason exists
3. Ensure `/robots.txt` and `/sitemap.xml` are publicly accessible with no authentication
4. Verify with Google Search Console > URL Inspection > "Test Live URL" — must return 200
5. Submit sitemap to GSC after confirming crawl access

**Verification:** `curl -A "Googlebot/2.1" https://giftcity.dspim.com/` must return 200.

---

### 1.2 Verify Index Status in Google Search Console
**Impact:** Critical | **Effort:** Low | **Type:** Blocker

- Run `site:giftcity.dspim.com` in Google Search to see how many pages are indexed
- Check GSC Coverage report for Crawl Anomalies or Excluded pages
- If pages are Discovered but not Crawled, the 403 is confirmed as the cause

---

## Phase 2 — Quick Wins (Weeks 2–3)

### 2.1 Fix Keyword Cannibalization on Customer Care / Contact Queries
**Impact:** High | **Effort:** Low | **Type:** Quick Win

"dsp mutual fund toll free number" and "dsp mutual fund customer care" are splitting rankings across /, /product, /faq, /mandatory-disclosures. Google is confused about the authoritative page.

**Steps:**
1. Choose `/mandatory-disclosures` or `/faq` as the canonical page for customer support info
2. Add `<link rel="canonical" href="https://giftcity.dspim.com/faq">` to all other pages that contain this content
3. Remove duplicate customer care content from /product and the homepage
4. Add a clear H2 "Contact Us / Customer Care" section on the chosen page

---

### 2.2 Optimise /empanelment Page — Defend Position 2
**Impact:** High | **Effort:** Low | **Type:** Quick Win

"dsp mutual fund empanelment online" ranks position 2 with only 140 sv but high commercial intent (CPC ₹1.25). This page is working — protect and expand it.

**Steps:**
1. Audit title tag: should be ~55 chars, include "DSP Mutual Fund Empanelment Online | GIFT City"
2. Add meta description (150–160 chars) with a clear CTA: "Register as DSP Mutual Fund distributor online via GIFT City IFSC. Quick empanelment process."
3. Add H1 matching the keyword: "DSP Mutual Fund Empanelment Online"
4. Add BreadcrumbList + Organization JSON-LD schema
5. Add internal links from the homepage and /product to /empanelment

---

### 2.3 Add Security Headers
**Impact:** Medium (trust signal) | **Effort:** Low | **Type:** Quick Win

All 6 security headers are missing. Financial services sites are particularly scrutinised for security.

Add to server/CDN config:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

---

### 2.4 Add llms.txt for AI Search Visibility
**Impact:** Medium (growing channel) | **Effort:** Low | **Type:** Quick Win

No AI crawler declarations exist. Financial queries increasingly appear in ChatGPT, Perplexity, and Google AI Overviews.

Create `https://giftcity.dspim.com/llms.txt`:
```
# DSP Investment Managers — GIFT City
> DSP IM's GIFT City IFSC platform for offshore global equity mutual funds for accredited investors.

## Products
- /product: DSP GIFT City Global Equity Funds and offshore investment products

## Key Pages
- /empanelment: Distributor empanelment and registration
- /faq: Frequently asked questions about GIFT City investing
- /mandatory-disclosures: Regulatory disclosures

## Allowed Crawlers
GPTBot, ClaudeBot, PerplexityBot, Applebot-Extended, Google-Extended
```

Also add to robots.txt:
```
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /
```

---

## Phase 3 — Strategic Improvements (Months 1–2)

### 3.1 Fix /product Page — Topical Dilution
**Impact:** High | **Effort:** Medium | **Type:** Strategic

/product currently ranks for irrelevant queries: "250000 usd into inr", "ppm to ppt", "pragya securities", "indmoney", "aed 450 in indian rupees". These signals confuse Google about the page's purpose and waste crawl budget.

**Steps:**
1. Audit /product HTML — identify which copy elements are triggering these accidental rankings (likely footer text, disclaimers, or unrelated boilerplate)
2. Remove or rewrite content that introduces irrelevant entities
3. Tighten title tag to: "DSP GIFT City Global Equity Funds | Offshore Investments for Accredited Investors"
4. Add H1: "Global Equity Funds — DSP GIFT City IFSC"
5. Create individual sub-pages per fund if multiple products exist (e.g., `/product/global-equity-fund`, `/product/feeder-fund`)
6. Add FinancialProduct or InvestmentOrPortfolioContent schema (use WebPage + FinancialService)

---

### 3.2 Build Informational Content Hub — GIFT City Topics
**Impact:** High | **Effort:** High | **Type:** Strategic

Multiple informational GIFT City queries are ranking between positions 46–89 with zero traffic. These keywords are trending upward (12-month trend 0.02 → 1.00 for "gift city mutual fund"). A content hub would:
- Capture informational traffic
- Build topical authority for GIFT City / IFSC
- Feed users into product and empanelment pages

**Create these pages:**

| Target Page | Primary Keyword | SV | Current Pos |
|-------------|-----------------|-----|-------------|
| /learn/what-is-gift-city | what is gift city | 1,900 | 85–89 |
| /learn/gift-city-mutual-fund | gift city mutual fund | 720 | 23 |
| /learn/ifsc-gift-city | ifsc gift city | 1,300 | 52 |
| /learn/accredited-investor-india | accredited investor india | 110 | 69–90 |
| /learn/lrs-gifting | lrs document | 110 | 67 |

Each page: 800–1,200 words, unique content, internal links to /product and /empanelment, Article schema.

---

### 3.3 Link Building — GIFT City Financial Authority
**Impact:** Critical | **Effort:** High | **Type:** Strategic

With only 9 referring domains, the subdomain cannot compete in financial SERPs. Target 20+ quality RDs within 3 months.

**Priority targets:**
1. **Internal links from dspim.com** — the root domain ranks #8,199 overall and has 9,548 organic keywords. A prominent link from `dspim.com` homepage or navigation to `giftcity.dspim.com` would pass significant equity. Verify this link exists.
2. **GIFT City IFSC authority sites** — giftcitybiz.in, ifsca.gov.in mentions/citations
3. **Financial media** — Moneycontrol, Economic Times, Mint, Value Research — via press releases or product announcements
4. **SEBI / AMFI context** — If DSP has any AMFI registration pages, ensure they link to the GIFT City subdomain
5. **Distributor/IFA platforms** — Mfuindia.com, NSE mutual fund platforms

---

### 3.4 Implement Schema Markup Across All Pages
**Impact:** Medium | **Effort:** Medium | **Type:** Strategic

No structured data detected. Financial services benefit from Organization, BreadcrumbList, and WebPage schema.

**Homepage (`/`):**
```json
{
  "@context": "https://schema.org",
  "@type": "FinancialService",
  "name": "DSP Investment Managers — GIFT City",
  "url": "https://giftcity.dspim.com",
  "description": "DSP IM's GIFT City IFSC platform for offshore global equity mutual funds",
  "parentOrganization": {
    "@type": "Organization",
    "name": "DSP Investment Managers",
    "url": "https://www.dspim.com"
  },
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "GIFT City",
    "addressRegion": "Gujarat",
    "addressCountry": "IN"
  }
}
```

**All pages:** Add BreadcrumbList schema.

**Product pages:** Add WebPage with `about` pointing to the fund description.

---

## Phase 4 — Maintenance (Ongoing)

### 4.1 Monthly Semrush Subdomain Rank Tracking
- Track positions for: "gift city mutual fund", "global equity fund", "dsp mutual fund empanelment online", "what is gift city", "ifsc gift city"
- Flag any new irrelevant keyword rankings on /product early

### 4.2 Google Search Console Weekly Review
- Monitor Coverage for new crawl errors
- Monitor Core Web Vitals for regressions after any site updates
- Watch for manual actions (financial sites are closely scrutinised)

### 4.3 Backlink Monitoring
- Monthly: `backlinks_refdomains` report to track new/lost referring domains
- Alert if any referring domain is a known link farm (cross-reference Trust Score)

---

## Summary Scorecard

| Action | Impact | Effort | Timeline |
|--------|--------|--------|----------|
| Fix 403 crawler block | 🔴 Critical | Low | Week 1 |
| Verify GSC index status | 🔴 Critical | Low | Week 1 |
| Fix keyword cannibalization | ⚠️ High | Low | Week 2 |
| Optimise /empanelment page | ⚠️ High | Low | Week 2 |
| Add security headers | Medium | Low | Week 2 |
| Add llms.txt | Medium | Low | Week 2–3 |
| Fix /product topical dilution | 🔴 High | Medium | Month 1 |
| Create informational content hub | ⚠️ High | High | Month 1–2 |
| Link building campaign | 🔴 Critical | High | Month 1–3 |
| Implement schema markup | Medium | Medium | Month 1 |

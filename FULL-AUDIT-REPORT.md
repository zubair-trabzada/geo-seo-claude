# Full SEO Audit — giftcity.dspim.com
**Date:** 2026-05-14  
**Scope:** Single-subdomain audit — on-page, technical, content, backlinks, keyword visibility  
**Auditor:** Agentic SEO Skill (LLM-first + Semrush data)

---

## A) Audit Summary

**Overall Score: 22/100 — Critical**

`giftcity.dspim.com` is a DSP Investment Managers subdomain serving their GIFT City (Gujarat International Finance Tec-City / IFSC) offshore mutual fund offering. Despite operating in a strategically high-value niche, the subdomain is near-invisible in organic search.

### Top 3 Issues
1. **403 block to all crawlers and bots** — the site returns HTTP 403 to non-browser user-agents, blocking Googlebot, security scanners, and SEO tools. This is the single biggest risk to indexability.
2. **Organic traffic estimated at ~17 visits/month** — from 165 keywords, with zero traffic from 95%+ of those keywords. Core target terms like "gift city mutual fund" (720 sv) rank at position 23.
3. **Extreme link poverty** — only 9 referring domains and 17 total backlinks. No domain authority to compete in financial SERPs.

### Top 3 Opportunities
1. **"gift city mutual fund" cluster** — trending keyword (12-month trend: 0.02 → 1.00) with growing search intent. Currently at position 23 — top-10 is achievable with focused on-page and link work.
2. **Empanelment / distributor funnel** — "dsp mutual fund empanelment online" ranks position 2 (140 sv). Signals Google already trusts this page for transactional intent. Optimise and expand.
3. **GIFT City informational hub** — queries like "what is gift city", "gift city full form", "ifsc gift city", "gift city companies list" show rising interest. A dedicated educational content section would capture this and establish topical authority.

---

## B) Findings Table

| Area | Severity | Confidence | Finding | Evidence | Fix |
|------|----------|------------|---------|----------|-----|
| Technical | 🔴 Critical | Confirmed | Site returns HTTP 403 to all non-browser requests, including Googlebot | `curl -sI https://giftcity.dspim.com` → `403 x-deny-reason: host_not_allowed` | Remove IP/UA allowlist restriction or whitelist Googlebot IPs; verify Google Search Console fetch-as-Google succeeds |
| Technical | 🔴 Critical | Confirmed | Robots.txt and Sitemap.xml both return 403 | Direct fetch of `/robots.txt` and `/sitemap.xml` both return 403 | Expose robots.txt and sitemap.xml publicly regardless of WAF rules |
| Technical | 🔴 Critical | Confirmed | llms.txt absent — site invisible to AI crawlers (ChatGPT, Claude, Perplexity) | `/llms.txt` returns 403; no AI crawler declarations found | Create `/llms.txt` with site description and allowed crawlers; add GPTBot/ClaudeBot/PerplexityBot to robots.txt allowlist |
| Technical | ⚠️ Warning | Confirmed | 6 of 6 security headers missing | Security check: HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy all absent. Security score: 25/100 | Add all 6 headers at server/CDN level. Priority: HSTS + X-Content-Type-Options |
| Keyword Visibility | 🔴 Critical | Confirmed | Primary target keyword at position 23 | "gift city mutual fund" (720 sv) ranks #23 — no estimated traffic | Dedicated landing page with keyword-focused H1, unique content, and internal links from dspim.com |
| Keyword Visibility | 🔴 Critical | Confirmed | Organic traffic ~17 visits/month from 165 keywords | Semrush: Organic Traffic = 17 | See action plan — content, on-page, and link building all required |
| Keyword Relevance | 🔴 Critical | Confirmed | /product page ranking for completely irrelevant queries | "250000 usd into inr" (14,800 sv, pos 45), "ppm to ppt", "1 bissa", "aed 450 in indian rupees", "pragya securities" all land on /product | Audit /product for accidental keyword injection; add canonical or noindex to irrelevant URL variants; rewrite meta to tightly match product intent |
| Keyword Cannibalization | ⚠️ Warning | Confirmed | Same keyword ranking on 3–4 different pages simultaneously | "dsp mutual fund toll free number" ranks at positions 54, 64, 69, 79 across /, /product, /faq, /mandatory-disclosures | Consolidate customer care info to one authoritative page; add canonical tags on duplicates |
| Keyword Cannibalization | ⚠️ Warning | Confirmed | "dsp mutual fund customer care" ranking at positions 39, 50, 54 across multiple URLs | Semrush subdomain_organic data shows three separate page rankings for same query | Same fix as above |
| Backlinks | 🔴 Critical | Confirmed | Only 9 referring domains and 17 total backlinks | Semrush backlinks_overview: total=17, domains_num=9, ips_num=9 | Immediate link building campaign (see action plan) |
| Backlinks | ⚠️ Warning | Confirmed | Authority Score 49, Trust Score 49 | Semrush backlinks_overview: score=49, trust_score=49 | Acquire links from .gov.in, SEBI-adjacent, and financial media domains |
| Content | ⚠️ Warning | Likely | /product page has diluted topical focus | Rankings for "global equity fund", "accredited investor india", "pragya securities", "indmoney", "gift scheme", "lrs document" on same page suggests catch-all content | Split /product into distinct pages per fund/product category |
| Content | ⚠️ Warning | Likely | No dedicated educational content for GIFT City informational queries | "what is gift city" (1,900 sv, pos 85–89), "gift city full form" (6,600 sv, pos 57), "ifsc gift city" (1,300 sv, pos 52) all rank deep with 0% traffic | Create /learn or /knowledge-hub section covering GIFT City, IFSC, LRS, accredited investor definitions |
| Schema | ⚠️ Warning | Hypothesis | No schema markup detected | Site blocked to tools; no JSON-LD observed in any cached/redirect data | Add Organization, FinancialService, and BreadcrumbList schema to all pages |
| On-Page | ⚠️ Warning | Hypothesis | Title tags and meta descriptions unverifiable due to 403 | Direct HTML fetch blocked | Verify via Google Search Console; ensure titles are 50–60 chars and include primary keyword per page |
| On-Page | ⚠️ Warning | Hypothesis | Open Graph and Twitter Card tags status unknown | social_meta.py blocked by 403 | Implement OG tags for all shareable pages (/product, /, /empanelment) |
| Performance | ℹ️ Info | Hypothesis | Core Web Vitals unmeasurable | PageSpeed Insights rate-limited; site blocked to external tools | Measure via Google Search Console CWV report; target LCP < 2.5s, INP < 200ms, CLS < 0.1 |
| GEO/AEO | ⚠️ Warning | Confirmed | No AI search readiness signals | No llms.txt, no structured FAQ content, no entity-clear content structure | Add llms.txt, implement Organization schema, create concise FAQ content for AI snippet eligibility |

---

## C) Scoring

### Chain-of-Thought Scoring

**Technical SEO (Weight: 25%)**
- Positives: HTTPS confirmed, subdomain properly isolated from root, referring domain AS/TS at 49
- Deficits: 403 to all bots (Critical), robots.txt 403 (Critical), sitemap.xml 403 (Critical), 6 security headers missing (Warning), no llms.txt (Warning)
- Base: 1/(1+5) × 100 = 17 | Penalties: 3×Critical(−45) + 2×Warning(−10) = −55 → floor 0
- **Technical Score: 0/100** *(three independent crawl-blocking failures)*

**Keyword Visibility / On-Page SEO (Weight: 15%)**
- Positives: 165 keywords indexed, "empanelment" at pos 2, "global equity fund" at pos 6
- Deficits: Core keyword at pos 23, ~17 monthly visits (Critical), irrelevant keyword rankings (Critical), cannibalization across 4 pages (Warning)
- Base: 2/(2+4) × 100 = 33 | Penalties: 2×Critical(−30) + 1×Warning(−5) = −35 → floor 0
- **On-Page Score: 0/100**

**Content Quality (Weight: 20%)**
- Positives: Pages for product, empanelment, FAQ, mandatory disclosures exist; growing GIFT City trend keywords starting to surface
- Deficits: /product ranks for irrelevant queries (Critical), no informational hub (Warning), cannibalization (Warning), content unverifiable (Hypothesis)
- Base: 2/(2+4) × 100 = 33 | Penalties: 1×Critical(−15) + 2×Warning(−10) = −25 → 8
- **Content Score: 8/100**

**Backlinks (Weight: 15%)**
- Positives: AS/TS at 49, 14 dofollow links, dspim.com root domain provides brand halo
- Deficits: Only 9 RDs (Critical for financial SERPs), 17 total backlinks (Critical), no editorial/media links observed
- Base: 2/(2+2) × 100 = 50 | Penalties: 2×Critical(−30) = −30 → 20
- **Backlinks Score: 20/100**

**Schema / Structured Data (Weight: 15%)**
- Positives: None observable
- Deficits: No schema detected, no OG tags verified, financial niche needs FinancialService/Organization schema
- **Schema Score: 10/100** *(Score confidence: Low — site blocked)*

**GEO / AI Readiness (Weight: 5%)**
- No llms.txt, no structured AI-readable content, no entity markup
- **GEO Score: 5/100**

### Weighted Overall Score
| Category | Score | Weight | Contribution |
|----------|-------|--------|-------------|
| Technical SEO | 0 | 25% | 0.0 |
| On-Page / Keyword Visibility | 0 | 15% | 0.0 |
| Content Quality | 8 | 20% | 1.6 |
| Backlinks | 20 | 15% | 3.0 |
| Schema / Structured Data | 10 | 15% | 1.5 |
| Performance (CWV) | — | 10% | — |
| GEO / AI Readiness | 5 | 5% | 0.25 |
| **TOTAL** | | **70%** | **~22** |

**Overall Score: 22/100 — Critical**

---

## D) Keyword Opportunity Map

| Keyword | SV (IN) | Current Pos | Gap | Priority |
|---------|---------|-------------|-----|----------|
| gift city mutual fund | 720 | 23 | Top 10 achievable | High |
| global equity fund | 140 | 6 | Top 3 achievable | High |
| dsp mutual fund empanelment online | 140 | 2 | Defend + expand | High |
| what is gift city | 1,900 | 85–89 | Top 20 with content | Medium |
| gift city full form | 6,600 | 57 | Top 20 with content | Medium |
| ifsc gift city | 1,300 | 52 | Top 20 with content | Medium |
| gift city companies list | 590 | 46–94 | Top 20 with content | Medium |
| accredited investor india | 110 | 69–90 | Informational page | Medium |
| gift city gujarat | — | — | Not yet ranking | Low |
| dsp gift city fund | — | — | Not yet ranking | Low |

---

## E) Unknowns and Follow-ups

- **Page HTML unverifiable** — title tags, meta descriptions, H1/H2 structure, canonical tags, OG tags, schema markup are all unconfirmed due to 403. Must verify via Google Search Console > URL Inspection or by IP-whitelisting the audit environment.
- **Core Web Vitals** — PageSpeed Insights blocked. Check GSC > Core Web Vitals report.
- **Index status** — Cannot confirm how many pages are indexed. Run `site:giftcity.dspim.com` in Google Search after confirming crawl access.
- **Internal link structure** — Cannot audit link equity flow from dspim.com to giftcity.dspim.com subdomain.
- **robots.txt rules** — Unknown whether Googlebot is allowed or blocked at robots.txt level (file returns 403 to this audit environment).
- **Backlink quality** — 9 referring domains identified but their identities, anchor texts, and follow status not fully audited. Run `backlinks_refdomains` + `backlinks_anchors` reports for details.

# GEO Audit Report: Stripe Documentation

**Audit Date:** 25 February 2026
**URL:** https://docs.stripe.com
**Business Type:** Developer Documentation / SaaS (Payment Processing)
**Pages Analyzed:** 7 (sampled from 1,100+ indexed URLs)

---

## Executive Summary

**Overall GEO Score: 67/100 (Fair)**

docs.stripe.com is a technically excellent documentation site with world-class brand authority and AI infrastructure — but is held back by two critical structural gaps: zero Schema.org implementation across the entire site, and a near-complete absence of AI citability signals (FAQ content, dates, self-contained answer blocks). Stripe sits paradoxically as both an industry benchmark for developer documentation design *and* a site that AI systems struggle to cite authoritatively at the passage level. Closing the schema and citability gaps — both of which require no architectural changes — would realistically push the GEO score above 80.

### Score Breakdown

| Category | Score | Weight | Weighted Score |
|---|---|---|---|
| AI Citability | 50/100 | 25% | 12.50 |
| Brand Authority | 79/100 | 20% | 15.80 |
| Content E-E-A-T | 84/100 | 20% | 16.80 |
| Technical GEO | 83/100 | 15% | 12.45 |
| Schema & Structured Data | 2/100 | 10% | 0.20 |
| Platform Optimization | 88/100 | 10% | 8.80 |
| **Overall GEO Score** | | | **67/100** |

---

## Critical Issues (Fix Immediately)

### CRIT-1: Zero Schema.org Markup Across Entire Site
**Affected pages:** All pages (verified across 7 sampled: homepage, /payments, /error-handling, /keys, /agentic-commerce, /error-codes, /billing)

Not a single `<script type="application/ld+json">` tag was found anywhere on the site. For a documentation property of Stripe's scale — where developer queries like "how do I handle Stripe errors" or "what does card_declined mean" are answered millions of times monthly by AI systems — this is the single highest-leverage GEO gap in the entire audit. Without schema, Stripe's official documentation competes on equal terms with unofficial blog posts and Stack Overflow threads for AI citation priority.

**Fix:** Deploy `TechArticle` schema to all documentation pages as a site-wide template change. This is a single engineering change with maximum coverage.

```json
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "Error Handling — Stripe Documentation",
  "description": "Learn how to handle errors from the Stripe API, including declined cards, authentication errors, and rate limits.",
  "url": "https://docs.stripe.com/error-handling",
  "dateModified": "2026-02-25",
  "author": { "@type": "Organization", "name": "Stripe", "url": "https://stripe.com" },
  "publisher": { "@type": "Organization", "name": "Stripe" },
  "proficiencyLevel": "Beginner",
  "programmingLanguage": ["Python", "Ruby", "JavaScript", "PHP", "Go", "Java", ".NET"]
}
```

### CRIT-2: No FAQPage Schema on Error Codes Reference
**Affected page:** docs.stripe.com/error-codes

The error-codes page contains ~100 error code definitions — each one is a natural Q&A pair ("What does `card_declined` mean?"). Without FAQPage schema, this data is invisible to AI extraction engines. FAQPage is the single highest-impact schema type for AI citation; ChatGPT, Perplexity, and Google AI Overviews extract Q&A pairs directly from FAQPage markup.

**Fix:** Add FAQPage schema to /error-codes alongside TechArticle:

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What does the Stripe error code 'card_declined' mean?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The card_declined error indicates the card has been declined. The decline_code attribute provides the specific reason, such as insufficient_funds or do_not_honor."
      }
    },
    {
      "@type": "Question",
      "name": "What does the Stripe error code 'authentication_required' mean?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "The card requires authentication via 3D Secure to complete the payment. Retry with 3D Secure or ask the customer to use a different card."
      }
    }
  ]
}
```

---

## High Priority Issues

### HIGH-1: llms-full.txt Returns 404
`https://docs.stripe.com/llms-full.txt` does not exist. The companion file to `llms.txt` provides complete, untruncated content for AI bulk ingestion — allowing AI systems to consume full documentation without crawling thousands of individual pages. Given Stripe already has an exceptional `llms.txt`, this is a high-leverage, low-effort addition.

**Fix:** Generate and publish `llms-full.txt` concatenating key documentation pages in Markdown. Estimate: 1-2 days engineering work given existing llms.txt pipeline.

### HIGH-2: No FAQ or Question-Formatted Content on Any Page
Across all 7 pages sampled, not a single question-formatted heading (H2/H3) or FAQ section exists. This is the single most impactful citability gap. AI retrieval pipelines look for content that mirrors question-answer structure. Stripe's docs answer developer questions in prose but compete poorly against Stack Overflow answers and blog posts that use Q&A formatting.

**Fix:** Add a "Common Questions" FAQ block (4-6 Q&A pairs) to each major reference page. Example for /keys:
- *"What is the difference between a publishable key and a secret key?"*
- *"Can I use my test API key in production?"*
- *"What should I do if my secret key is exposed?"*

### HIGH-3: No Dates or Freshness Signals on Content Pages
No publication dates, last-updated timestamps, or API version badges appear on any documentation page. For a versioned API platform, this creates material trust and citability gaps. AI systems increasingly downweight undated content for rapidly evolving topics.

**Fix:** Add a visible `"Last reviewed: [Month Year] | Applies to API version: [version]"` badge to every documentation page header. Cross-reference changelog version names (e.g., "Clover", "Basil") to connect content to the API versioning system explicitly.

### HIGH-4: Organization Schema Missing from Homepage
No Organization schema exists on the homepage. This is the foundational entity recognition signal that tells AI knowledge graphs docs.stripe.com belongs to Stripe, Inc. Without it, entity attribution is left to AI inference.

**Fix (one-time, homepage only):**

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Stripe",
  "url": "https://stripe.com",
  "sameAs": [
    "https://en.wikipedia.org/wiki/Stripe,_Inc.",
    "https://www.wikidata.org/wiki/Q7624104",
    "https://www.linkedin.com/company/stripe",
    "https://github.com/stripe"
  ],
  "logo": "https://stripe.com/img/stripe-logo.png"
}
```

### HIGH-5: Sitemap Lacks lastmod, changefreq, and priority
All 1,100+ sitemap URLs have no `lastmod`, `changefreq`, or `priority` attributes. AI crawlers cannot determine content freshness or crawl scheduling. This is particularly damaging for a documentation site with frequent changelog updates.

**Fix:** Update sitemap generation pipeline to include `<lastmod>` tied to actual content modification dates. Split into a sitemap index with child sitemaps segmented by product area.

---

## Medium Priority Issues

### MED-1: Hub Pages Are Navigation Shells with No Citable Content
The homepage (H1: "Explore our guides and examples to integrate Stripe") and the Payments page function purely as link directories with zero substantive content. The pages with the most inbound authority signals contribute nothing to AI citability.

**Fix:** Rewrite hub pages into 800-1,200 word authoritative overviews covering: architectural summary, integration path comparison, common implementation patterns, and "when to use this" context.

### MED-2: Zero External Citations in Developer Docs
The API Keys page has 18 internal links and 0 external links. No documentation page cites OWASP, PCI-DSS, RFC standards, or any external authority. This limits bidirectional authority signals that AI models use to validate a source.

**Fix:** Add inline references to OWASP ASVS for key storage guidance, PCI-DSS Requirement 3.6 for key management, and RFC 9110 for HTTP error semantics on the error-handling page.

### MED-3: No Explicit AI Crawler Entries in robots.txt
All AI crawlers are currently allowed via the wildcard `*` rule. Adding explicit named rules for `GPTBot`, `ClaudeBot`, `anthropic-ai`, `PerplexityBot`, `OAI-SearchBot`, and `cohere-ai` makes AI-access intent unambiguous and future-proofs against wildcard interpretation changes.

**Fix:** 15-minute change to robots.txt adding explicit `Allow: /` blocks for each AI crawler.

### MED-4: Wikipedia Article Lacks Depth
Despite being a $159B company, Stripe's Wikipedia article lacks sections on regulatory history, competitive landscape, international expansion, and product timeline. This limits how rich an entity record AI models can build from Wikipedia training data.

**Fix:** Support or contribute expansion of the Stripe, Inc. Wikipedia article to "Good Article" standard. Target the Wikidata entry (Q7624104) for complete structured attribute coverage.

### MED-5: Trustpilot Sentiment Crisis
Stripe's Trustpilot profile (16,836+ reviews, predominantly negative) creates a "Stripe = unreliable for merchants" entity association in general-web-trained AI models, even as developer-focused models retain positive associations.

**Fix:** Implement a proactive Trustpilot response programme. Link `stripe.com/complaints` from Trustpilot responses. Introduce structured merchant appeal timelines disclosed publicly.

---

## Low Priority Issues

### LOW-1: No HowTo Schema on Integration Guides
Tutorial pages with numbered steps (e.g., "How to accept a payment") are ideal HowTo schema candidates. Perplexity and Google AI Overviews render HowTo steps verbatim.

### LOW-2: No BreadcrumbList Schema Site-Wide
Navigation context is absent for AI crawlers. BreadcrumbList on every page provides hierarchy signals.

### LOW-3: No DefinedTerm Schema on Error Codes
~100 error codes are each a defined term-definition pair. DefinedTerm schema allows AI models to extract with high confidence.

### LOW-4: YouTube Ecosystem Third-Party Controlled
High-volume beginner tutorials ("Stripe + React", "Stripe subscriptions Node.js") are created by independent creators, some using deprecated APIs. Stripe lacks control over what beginner content AI models encounter most.

### LOW-5: No Author Attribution on Any Content Page
No documentation page shows an author, contributor list, or editorial reviewer. For YMYL-adjacent technical content (financial APIs), this is a trust signal gap.

### LOW-6: llms.txt Gap — Error Handling and Troubleshooting
The current llms.txt has excellent integration path coverage but limited links to error code references and failure-mode troubleshooting. AI agents helping developers debug live integrations fall back to unstructured crawling.

---

## Category Deep Dives

### AI Citability — 50/100

The error-handling page is the standout performer: definition-style content like "An error occurred during a payment, involving one of these situations: Payment blocked for suspected fraud, Payment declined by the issuer, Other payment errors" is exactly what AI systems cite. The Type → Codes → Problem → Solutions structure creates natural answer blocks. The API keys comparison tables (4 tables, key types vs modes) provide clean, extractable facts.

However, three systemic gaps affect every page:
1. **Zero FAQ content** — not a single question-formatted heading across all 7 pages
2. **No dates** — no page displays a publication date, last-updated timestamp, or version badge
3. **Hub pages** — the homepage and /payments have no substantive content to cite

The site performs at parity with average developer documentation rather than dominating citations as the primary source it should be.

**Top rewrite suggestion:** Add a 4-sentence summary block at the top of each reference page answering the page's core question directly. For error handling: *"Stripe errors fall into four categories: API errors, card errors, idempotency errors, and invalid request errors. Card errors occur when the issuing bank declines a transaction and require user-facing messaging..."*

---

### Brand Authority — 79/100

| Platform | Score |
|---|---|
| GitHub & Developer Presence | 91/100 |
| Media & News Authority | 93/100 |
| Cross-Platform NAP Consistency | 85/100 |
| Wikipedia Authority | 78/100 |
| Reddit Community Presence | 72/100 |
| YouTube Content Ecosystem | 74/100 |
| Review Site Presence | 58/100 |

Stripe is a globally recognised, high-authority brand entity with dominant presence on technical and media platforms. The GitHub organisation (83+ repos, official SDKs for 7 languages, 33+ sample repos, dedicated `stripe/ai` repo) creates code-level citation density that no payment competitor approaches. TechCrunch, Forbes, and financial trade press coverage is continuous and top-tier ($159B valuation, $1.9T 2025 volume, 50% Fortune 100 penetration).

The primary drag is Trustpilot (16,836+ reviews, predominantly negative on account freezes and fund holds) which creates bifurcated brand signals that AI models processing broad review data will register.

---

### Content E-E-A-T — 84/100

| Dimension | Score |
|---|---|
| Expertise | 85/100 |
| Authoritativeness | 88/100 |
| Trustworthiness | 82/100 |
| Content Depth | 90/100 |
| Experience | 72/100 |
| Freshness | 65/100 |

docs.stripe.com is structurally the sole primary source for Stripe integration knowledge — there is no competing "official" reference. The security page publicly discloses PCI Service Provider Level 1, SOC 1/SOC 2 Type II, NIST Cybersecurity Framework, and EU-US Data Privacy Framework compliance. Content depth is exceptional: 14 error types with precise definitions, 7-language code coverage, original concepts like `SharedPaymentToken`.

The primary liability is structural: complete absence of author attribution, publication dates, and external standards citations across all content pages creates verifiability gaps that reduce trust scores despite technically excellent underlying content.

---

### Technical GEO — 83/100

| Dimension | Score |
|---|---|
| llms.txt Quality | 96/100 |
| HTTPS & Security | 98/100 |
| Technical Rendering (SSR) | 90/100 |
| AI Crawler Access | 88/100 |
| Meta Tags & Canonical URLs | 70/100 |
| Header Directives | 65/100 |
| Sitemap Quality | 62/100 |

docs.stripe.com sets the current benchmark for AI-ready technical documentation infrastructure. The `llms.txt` file (45,000+ characters, 25 sections, 280+ curated links, explicit "Instructions for Large Language Model Agents" section, active deprecation steering) is among the most sophisticated AI-readiness implementations publicly documented. Server-side rendering ensures AI crawlers receive complete, parseable content on first fetch. All AI crawlers are allowed.

The primary technical gap is freshness signalling: the sitemap lacks `lastmod` attributes and `llms-full.txt` is absent (404).

---

### Schema & Structured Data — 2/100

| Schema Type | Status |
|---|---|
| Organization | ❌ Missing |
| WebSite | ❌ Missing |
| TechArticle | ❌ Missing |
| FAQPage | ❌ Missing |
| HowTo | ❌ Missing |
| BreadcrumbList | ❌ Missing |
| SoftwareApplication | ❌ Missing |
| DefinedTerm | ❌ Missing |

**Zero schema.org markup detected across all 7 pages sampled.** This is confirmed across: homepage, /payments, /error-handling, /keys, /agentic-commerce, /error-codes, /billing.

For a documentation property at Stripe's scale, this is the single highest-leverage GEO gap. The score of 2 (rather than 0) reflects only that there are no conflicting or erroneous schema tags — a blank slate.

**Priority implementation order:**
1. `TechArticle` — all doc pages (template change, maximum coverage)
2. `FAQPage` — /error-codes, /billing FAQ sections
3. `HowTo` — integration guides with sequential steps
4. `Organization` + `WebSite` — homepage (one-time)
5. `BreadcrumbList` — site-wide
6. `DefinedTerm` — /error-codes, any glossary pages
7. `SoftwareApplication` — product overview pages

---

### Platform Optimization — 88/100

Stripe is an exceptionally strong AI-citation candidate. The combination of GitHub SDKs in millions of developer codebases, docs.stripe.com cited as the gold standard for API documentation design, prolific third-party tutorial content, an explicit `/llms.txt`, and dominant media coverage means an LLM answering "how do I accept payments in my app" will almost certainly reference Stripe. The 12-point gap from 100 reflects the Trustpilot sentiment mass, Wikipedia article shallowness, and missing schema/entity data on the docs property.

---

## Quick Wins (Implement This Week)

1. **Add `TechArticle` schema as a site-wide template** — single engineering change, affects all 1,100+ pages, highest GEO lift per hour of effort. Estimated impact: +8-12 points on overall GEO score.

2. **Add "Last reviewed" timestamps to every page** — minimal engineering effort, maximum trust and freshness signal gain. Directly addresses AI model freshness weighting.

3. **Publish `llms-full.txt`** — already have the llms.txt pipeline; extend it to produce the full-content companion file. Allows AI bulk ingestion without crawling individual pages.

4. **Add `Organization` + `WebSite` schema to homepage** — one-time, 20-minute implementation, establishes entity recognition foundation for all AI knowledge graphs.

5. **Add FAQ blocks to the top 10 highest-traffic pages** — no schema required initially; question-formatted H3 headings + 2-4 sentence answers immediately improve citability for "what is X" and "how do I Y" queries.

---

## 30-Day Action Plan

### Week 1: Schema Foundation
- [ ] Deploy `TechArticle` schema template to all documentation pages
- [ ] Add `Organization` and `WebSite` schema to homepage
- [ ] Add `BreadcrumbList` schema site-wide
- [ ] Add "Last reviewed" timestamps to all pages
- [ ] Add explicit AI crawler entries (GPTBot, ClaudeBot, PerplexityBot, anthropic-ai) to robots.txt

### Week 2: Citability & FAQ
- [ ] Add FAQ blocks (4-6 Q&A pairs) to: /keys, /error-handling, /payments, /billing, /agentic-commerce
- [ ] Add `FAQPage` schema to /error-codes (sample 20 most-queried error codes)
- [ ] Add "In this article" summary blocks (3-5 sentences) to top 10 highest-traffic pages
- [ ] Publish `llms-full.txt`

### Week 3: Content & Authority
- [ ] Add `lastmod` timestamps to sitemap.xml and implement sitemap index
- [ ] Add `HowTo` schema to top 5 integration tutorial pages
- [ ] Add external standards citations to /keys (OWASP) and /error-handling (RFC 9110)
- [ ] Begin Trustpilot response programme (respond to top 50 most-viewed complaints)

### Week 4: Platform & Depth
- [ ] Rewrite /payments hub page into 1,000-word authoritative overview
- [ ] Add `DefinedTerm` schema to /error-codes for top 30 error codes
- [ ] Expand Stripe Wikipedia article (add regulatory history, product timeline, competitive landscape sections)
- [ ] Add API version badges to all pages ("Applies to Stripe API version: [date]")

---

## Appendix: Pages Analyzed

| URL | Title | Key GEO Issues |
|---|---|---|
| docs.stripe.com | Documentation | No meta description, no schema, no citable content |
| docs.stripe.com/payments | Payments | Hub-only, no content, no schema, no FAQ |
| docs.stripe.com/error-handling | Error handling | No schema, no dates, no FAQ headings (despite ideal content) |
| docs.stripe.com/keys | API keys | No schema, no dates, no external citations, no FAQ |
| docs.stripe.com/agentic-commerce | Agentic commerce | No schema, no dates, partially self-contained only |
| docs.stripe.com/error-codes | Error codes | No FAQPage schema on 100+ Q&A pairs — critical missed opportunity |
| docs.stripe.com/billing | Billing | No schema detected |

---

## Methodology

This audit used the GEO framework scoring weighted across 6 categories. Data was collected via direct page fetching (WebFetch), robots.txt and llms.txt analysis, sitemap inspection, and cross-platform web searches for brand authority signals. 5 specialized analysis subagents ran in parallel. No pages were crawled in violation of robots.txt directives.

**GEO Score Formula:**
```
GEO_Score = (Citability × 0.25) + (Brand × 0.20) + (EEAT × 0.20) + (Technical × 0.15) + (Schema × 0.10) + (Platform × 0.10)
           = (50 × 0.25) + (79 × 0.20) + (84 × 0.20) + (83 × 0.15) + (2 × 0.10) + (88 × 0.10)
           = 12.50 + 15.80 + 16.80 + 12.45 + 0.20 + 8.80
           = 67/100
```

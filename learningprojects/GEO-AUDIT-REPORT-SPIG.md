# GEO Audit Report — SPIG-GMAB
**Generated:** 2026-02-24
**URL:** https://www.spig-gmab.com
**Business Type:** B2B Industrial — Cooling towers, water conservation, air pollution control
**Language:** English (primary) + 7 additional (IT, ES, PT, ZH, AR, SV, DE)
**Platform:** WordPress + Astra v6.7.4 + All in One SEO v4.8.1.1
**Audited by:** GEO-SEO Claude Code Skill

---

## GEO Score: 39 / 100

> **Verdict:** SPIG-GMAB is a legitimate, nearly 90-year-old industrial company (founded 1936) with real global operations, verified trade association memberships, and notable M&A history — but its website dramatically underrepresents the company's capabilities. The content is thin, technically shallow, authored by a web agency rather than engineers, and lacks the structured data, hreflang implementation, and AI-ready content that modern search platforms require. The gap between the company's real-world industrial authority and its digital presence is the largest single opportunity.

---

## Score Breakdown

| Category | Weight | Score | Grade |
|---|---|---|---|
| AI Citability & Visibility | 25% | 42 / 100 | D+ |
| Brand Authority Signals | 20% | 58 / 100 | C- |
| Content Quality & E-E-A-T | 20% | 29 / 100 | F |
| Technical Foundations | 15% | 42 / 100 | D+ |
| Structured Data | 10% | 32 / 100 | F |
| Platform Optimization | 10% | 22 / 100 | F |
| **COMPOSITE GEO SCORE** | **100%** | **39 / 100** | **D+** |

---

## Platform Readiness Dashboard

| AI Platform | Score | Status |
|---|---|---|
| Google AI Overviews | 18 / 100 | 🔴 Not ready |
| ChatGPT | 25 / 100 | 🔴 Not ready |
| Perplexity | 20 / 100 | 🔴 Not ready |
| Bing Copilot | 25 / 100 | 🔴 Not ready |

---

## Company Overview

| Property | Value |
|---|---|
| Founded | 1936 (Italy) |
| Parent Company | AUCTUS Capital Partners AG (acquired Oct 2024, ~$40M from Babcock & Wilcox) |
| Headquarters | Via Borgomanero, 34, 28040 Paruzzaro NO, Italy |
| Sweden Office | Anders Carlssons gata 14, SE-417 55 Goteborg |
| Subsidiaries | SPIG Shanxi (China), Brazil presence |
| Products | Wet cooling towers, dry cooling systems, hybrid towers, air pollution control, flue gas treatment |
| Industries | Power generation, petrochemical, waste-to-energy, heavy industry |
| Trade Memberships | ESWET (European Suppliers of Waste-to-Energy Technology) |
| Platform | WordPress + Astra theme v6.7.4 |
| SEO Plugin | All in One SEO v4.8.1.1 |
| Languages | EN, IT, ES, PT, ZH, AR, SV, DE (8 languages) |

---

## AI Crawler Access

| Crawler | Status | Notes |
|---|---|---|
| GPTBot (OpenAI) | ✅ Allowed | Falls under `User-agent: *` — not blocked |
| ClaudeBot (Anthropic) | ✅ Allowed | Falls under `User-agent: *` — not blocked |
| PerplexityBot | ✅ Allowed | Falls under `User-agent: *` — not blocked |
| Googlebot-Extended | ✅ Allowed | Falls under `User-agent: *` — not blocked |
| llms.txt | ❌ Missing | Returns generic page, not implemented |

**robots.txt:** Minimal — only blocks `/wp-admin/`. No AI-specific crawler directives. Two sitemaps declared (XML + RSS).

---

## Critical Findings

### 🔴 CRITICAL — No Hreflang Tags on 8-Language Site
**Impact:** The single most damaging technical SEO issue. The site serves content in 8 languages via URL subdirectories (/it/, /es/, /de/, etc.) but has **zero hreflang tags** on any page. No `x-default` declaration. No `lang` attribute on the `<html>` element. The `inLanguage` property in JSON-LD is present but is not a substitute for hreflang. Google has no signals to associate language variants, treating them as potential duplicate content. Users in Italy may see the English page instead of the Italian version.

**Fix:** Implement hreflang tags via All in One SEO's multilingual settings or WPML/Polylang. Every page must declare all language alternates plus `x-default` pointing to English. Add `<html lang="en">` (or appropriate language code) to every page.

---

### 🔴 CRITICAL — Lorem Ipsum on SPIG Brand Page
**Impact:** The `/spig/` brand page contains Lorem ipsum placeholder text visible to AI crawlers and users. This severely damages credibility and signals an incomplete website.

**Fix:** Replace immediately with the SPIG 90-year history narrative, technical capabilities, and brand positioning.

---

### 🔴 CRITICAL — Blog Author is a Web Agency Email
**Impact:** All blog posts and their schema markup attribute content to `multimedia@studiokey.it` — a web design agency. The Person schema shows this email as the author name with a generic Gravatar. This provides zero E-E-A-T value and signals that no internal expert created the content. Perplexity, Google E-E-A-T, and ChatGPT all weight author expertise heavily.

**Fix:** Replace author attribution with named SPIG engineers or technical directors. Create proper author bio pages with credentials, job titles, and LinkedIn profiles.

---

### 🟠 HIGH — Zero Technical/Educational Content
**Impact:** The site contains no content that answers industry questions ("What is an evaporative cooling tower?", "wet vs dry cooling tower comparison", "cooling tower maintenance best practices"). Product pages have under 200 words of marketing copy each. The blog has ~10 posts total (many are translations of the same 3-4 articles). No comparison tables, no FAQ sections, no technical specifications, no performance data.

**Fix:** Create a technical knowledge hub with 15-20 pillar articles. Add FAQ sections with FAQPage schema to every product page. Build comparison tables (wet vs dry vs hybrid).

---

### 🟠 HIGH — No Service or Product Schema
**Impact:** The core service pages (`/wet-cooling-towers/`, `/dry-cooling-systems/`) have zero Service or Product schema. Only generic WebPage + Organization + BreadcrumbList boilerplate. For a B2B industrial company, this is the most impactful missing schema — AI and search engines cannot understand SPIG's offerings in structured form.

**Fix:** Deploy Service JSON-LD on all product/service pages with descriptions, serviceType, areaServed, and provider references.

---

### 🟠 HIGH — No LocalBusiness Schema Despite Multiple Offices
**Impact:** Confirmed offices in Italy (Paruzzaro), Sweden (Goteborg), and China — none have LocalBusiness schema. Zero eligibility for local pack results. Contact details (phone numbers, addresses with VAT IDs) exist on the contact page but are not structured.

**Fix:** Add LocalBusiness schema for each office location with address, phone, geo coordinates.

---

### 🟠 HIGH — Case Studies Are Stubs
**Impact:** The cooling tower installation case study references "one of the largest refineries in Europe" and a "21-day timeframe" but has no client name, no quantified outcomes, no performance data, no photographs. The case studies category page renders but shows no substantive content. For a B2B company, detailed case studies are the single most important content type for AI citation.

**Fix:** Rebuild case studies as 1,500-2,500 word project narratives with quantified challenges, technical solutions, installation methodology, measured outcomes, and client testimonials.

---

### 🟠 HIGH — No llms.txt File
**Impact:** No structured guidance for AI crawlers about site content, company identity, or citation preferences. The URL returns a generic page rather than an AI instruction file.

**Fix:** Create `/llms.txt` with company facts (founded 1936, global operations, product lines), key page URLs, and preferred citation format.

---

### 🟡 MEDIUM — astra-advanced-hook URLs in Sitemap
**Impact:** The sitemap includes 2 internal Astra theme hook URLs (`/astra-advanced-hook/433/`, `/astra-advanced-hook/470/`). These are internal customization artifacts that waste crawl budget and expose theme architecture.

**Fix:** Exclude `astra-advanced-hook` post type from the sitemap and set to noindex in AIOSEO settings.

---

### 🟡 MEDIUM — No SearchAction in WebSite Schema
**Impact:** The WebSite schema has no `potentialAction` with `SearchAction`, so no sitelinks search box eligibility in Google.

**Fix:** Add SearchAction to WebSite schema via AIOSEO configuration.

---

### 🟡 MEDIUM — No Wikipedia/Wikidata Entity
**Impact:** Despite a 90-year history, multiple corporate acquisitions (Ambienta SGR 2010, Babcock & Wilcox, AUCTUS 2024), and global operations in 50+ countries — SPIG has no Wikipedia article. Wikipedia is one of the most heavily weighted sources in LLM training data.

**Fix:** Pursue a Wikipedia article. The company has sufficient notability via SEC filings, Power Magazine coverage, ESWET membership, and M&A history. This is the single highest-impact long-term action for AI visibility.

---

### 🟡 MEDIUM — No Canonical Tags Detected
**Impact:** Canonical tags were not found on tested pages. Without them, search engines must infer the preferred URL, increasing duplicate content risk — especially critical with 8 language versions.

**Fix:** Verify AIOSEO canonical tag configuration. Every page should have a self-referencing canonical.

---

### 🟡 MEDIUM — No YouTube Presence
**Impact:** For a company that installs massive cooling towers, the absence of installation timelapses, technical explainers, or factory tours on YouTube is a major missed opportunity. YouTube transcripts feed directly into AI training data.

**Fix:** Create a dedicated YouTube channel. Start with installation timelapse videos and technical explainer content.

---

## What's Working Well

| Strength | Notes |
|---|---|
| ✅ SSR content delivery | WordPress/Astra renders content server-side — AI crawlers read HTML directly |
| ✅ HTTPS fully implemented | No mixed content issues detected |
| ✅ BreadcrumbList schema | Well-implemented across all pages |
| ✅ WebPage schema with dates | datePublished and dateModified on all pages |
| ✅ Permissive robots.txt | AI crawlers not blocked — no hostile stance |
| ✅ Real brand authority | 90-year history, M&A paper trail (SEC filings, BusinessWire), ESWET membership |
| ✅ Third-party mentions | Power Magazine, BusinessWire, ESWET, Ambienta SGR, IndiaMART, WME Expo 2026 |
| ✅ Physical offices verified | Italy (with P.IVA), Sweden (with VAT ID) — verifiable trust signals |
| ✅ Multilingual URL structure | Clean subdirectory pattern (/it/, /es/, /de/, etc.) |
| ✅ Trade show presence | WME Expo 2026 exhibitor — active industry participant |

---

## Prioritized Action Plan

### Immediate — P0 (Week 1-2)

| # | Action | Time | Impact |
|---|---|---|---|
| 1 | Remove Lorem ipsum from /spig/ brand page — replace with 90-year history | 2 hrs | 🔥 Critical |
| 2 | Implement hreflang tags across all 8 language versions + x-default | 4 hrs | 🔥 Critical |
| 3 | Add `<html lang="...">` attribute to every page template | 30 min | 🔥 Critical |
| 4 | Add `dir="rtl"` to Arabic version HTML element | 15 min | Critical |
| 5 | Fix author attribution — replace agency email with named engineers | 2 hrs | 🔥 Critical |
| 6 | Create llms.txt and deploy to root | 1 hr | High |
| 7 | Exclude astra-advanced-hook from sitemap + set noindex | 15 min | Medium |

### Short-term (Weeks 3-6)

| # | Action | Time | Impact |
|---|---|---|---|
| 8 | Add Service schema to all product/service pages (8 languages) | 4 hrs | High |
| 9 | Enhance Organization schema (contactPoint, location, sameAs, description) | 2 hrs | High |
| 10 | Add LocalBusiness schema for Italy and Sweden offices | 2 hrs | High |
| 11 | Register Bing Webmaster Tools + submit sitemap | 20 min | High |
| 12 | Add canonical tags to every page (verify AIOSEO config) | 1 hr | High |
| 13 | Expand product pages to 1,000+ words with technical specifications | 8 hrs | High |
| 14 | Add FAQ sections with FAQPage schema to product pages | 6 hrs | High |

### Medium-term (Month 2-3)

| # | Action | Time | Impact |
|---|---|---|---|
| 15 | Create 10 pillar technical articles answering core industry questions | 20 hrs | 🔥 Highest |
| 16 | Rebuild case studies with quantified outcomes (1,500-2,500 words each) | 15 hrs | High |
| 17 | Create comparison tables (wet vs dry vs hybrid) on product pages | 4 hrs | High |
| 18 | Add SearchAction to WebSite schema | 30 min | Medium |
| 19 | Launch YouTube channel with installation timelapses | 8 hrs | High |
| 20 | Add Open Graph and Twitter Card meta tags (enable in AIOSEO) | 1 hr | Medium |

### Strategic (Month 3+)

| # | Action | Impact |
|---|---|---|
| 21 | Pursue Wikipedia article for SPIG (90-year history, M&A notability) | 🔥 Highest — single biggest LLM training data impact |
| 22 | Publish technical white papers on cooling tower efficiency | High — builds deep authority |
| 23 | Pursue feature articles in Power Magazine, CTI publications | High — independent editorial coverage |
| 24 | Build LinkedIn thought leadership content program | High — B2B authority signals |
| 25 | Implement IndexNow protocol for faster content indexing | Medium |
| 26 | Publish 2+ technical articles per month ongoing | High — sustained content velocity |

---

## Generated Assets

### llms.txt Template

Deploy as `https://www.spig-gmab.com/llms.txt`:

```
# SPIG-GMAB — llms.txt
# Industrial cooling towers, water conservation, air pollution control

> SPIG-GMAB is an industrial technology company founded in 1936 in Italy, specializing in cooling tower engineering, water conservation, and air pollution control systems. The company operates globally with offices in Paruzzaro (Italy), Goteborg (Sweden), and Shanxi (China). SPIG-GMAB is a member of ESWET (European Suppliers of Waste-to-Energy Technology) and is owned by AUCTUS Capital Partners AG. The SPIG product line includes wet cooling towers (natural draft, induced draft, forced draft), dry cooling systems (air-cooled condensers, indirect dry cooling), hybrid cooling towers, and air pollution control equipment (flue gas treatment, heat recovery, polishing scrubbers).

## Key Pages
- Homepage: https://www.spig-gmab.com/
- Wet Cooling Towers: https://www.spig-gmab.com/wet-cooling-towers/
- Dry Cooling Systems: https://www.spig-gmab.com/dry-cooling-systems/
- Case Studies: https://www.spig-gmab.com/category/case-studies/
- News: https://www.spig-gmab.com/category/news/
- Contact: https://www.spig-gmab.com/contact/
- About / Ethics: https://www.spig-gmab.com/ethics/

## Company Facts
- Founded: 1936 (Italy)
- Headquarters: Paruzzaro, Italy
- Parent: AUCTUS Capital Partners AG
- Former parent: Babcock & Wilcox (NYSE: BW) until October 2024
- Trade membership: ESWET
- Operations: 50+ countries worldwide

## Contact
- Italy: +39 0322 245401 | Via Borgomanero, 34, 28040 Paruzzaro NO
- Sweden: +46 31 50 19 60 | Anders Carlssons gata 14, SE-417 55 Goteborg
- LinkedIn: https://www.linkedin.com/company/spig-gmab/
```

---

### Enhanced Organization Schema (replace on homepage)

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.spig-gmab.com/#organization",
  "name": "SPIG-GMAB",
  "alternateName": ["SPIG", "GMAB"],
  "url": "https://www.spig-gmab.com/",
  "logo": {
    "@type": "ImageObject",
    "url": "https://www.spig-gmab.com/wp-content/uploads/2024/07/logo_SPIG_GMAB-bw-1.png",
    "width": 596,
    "height": 109
  },
  "description": "SPIG-GMAB provides advanced cooling tower solutions, water conservation systems, and air pollution control technology for industrial applications worldwide. Founded in 1936.",
  "foundingDate": "1936",
  "parentOrganization": {
    "@type": "Organization",
    "name": "AUCTUS Capital Partners AG",
    "url": "https://www.auctus.eu/"
  },
  "areaServed": "Worldwide",
  "knowsAbout": ["Wet Cooling Towers", "Dry Cooling Systems", "Air Pollution Control", "Flue Gas Treatment", "Waste-to-Energy"],
  "memberOf": {
    "@type": "Organization",
    "name": "ESWET",
    "url": "https://eswet.eu/"
  },
  "contactPoint": [
    {
      "@type": "ContactPoint",
      "telephone": "+39-0322-245401",
      "contactType": "sales",
      "areaServed": "Europe",
      "availableLanguage": ["English", "Italian"]
    },
    {
      "@type": "ContactPoint",
      "telephone": "+46-31-50-19-60",
      "contactType": "sales",
      "areaServed": "Scandinavia",
      "availableLanguage": ["English", "Swedish"]
    }
  ],
  "location": [
    {
      "@type": "Place",
      "name": "SPIG Italy (Headquarters)",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "Via Borgomanero, 34",
        "addressLocality": "Paruzzaro",
        "postalCode": "28040",
        "addressCountry": "IT"
      }
    },
    {
      "@type": "Place",
      "name": "GMAB Sweden",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "Anders Carlssons gata 14",
        "addressLocality": "Goteborg",
        "postalCode": "SE-417 55",
        "addressCountry": "SE"
      }
    }
  ],
  "sameAs": [
    "https://www.linkedin.com/company/spig-gmab/"
  ]
}
```

---

### Service Schema Template (for /wet-cooling-towers/)

```json
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "Wet & Hybrid Cooling Towers",
  "description": "Natural draft and induced/forced draft wet cooling towers engineered for optimal plant efficiency. Capabilities include high seismic/wind load resistance, vibration control, corrosion resistance, low-noise emission, sub-freezing operation, and geothermal applications.",
  "provider": { "@id": "https://www.spig-gmab.com/#organization" },
  "serviceType": "Industrial Cooling Tower Engineering & Installation",
  "areaServed": "Worldwide",
  "url": "https://www.spig-gmab.com/wet-cooling-towers/"
}
```

---

## Methodology

This audit used the GEO-SEO Claude Code Skill (February 2026). Five parallel subagents analyzed:

| Subagent | Scope |
|---|---|
| geo-ai-visibility | AI crawler access, llms.txt, citability scoring, brand authority |
| geo-platform-analysis | Google AIO, ChatGPT, Perplexity, Bing Copilot readiness |
| geo-technical | SSR, HTTPS, hreflang, mobile, crawlability, structured data foundations |
| geo-content | E-E-A-T, content quality, readability, AI citation readiness |
| geo-schema | JSON-LD inventory, validation, rich result eligibility |

**GEO Score weighting:**
- AI Citability & Visibility: 25%
- Brand Authority Signals: 20%
- Content Quality & E-E-A-T: 20%
- Technical Foundations: 15%
- Structured Data: 10%
- Platform Optimization: 10%

---

*Report saved to: `GEO-AUDIT-REPORT-SPIG.md`*

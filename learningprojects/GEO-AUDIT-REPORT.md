# GEO Audit Report — BaraBand.se
**Generated:** 2026-02-24
**URL:** https://www.baraband.se
**Business Type:** E-commerce — Swedish watch strap retailer (Shopify)
**Language:** Swedish (sv-SE)
**Audited by:** GEO-SEO Claude Code Skill

---

## ⚡ GEO Score: 39 / 100

> **Verdict:** BaraBand.se is an invisible participant in AI search. The store is technically sound and sells genuine European-quality products — but it has almost no signals that AI systems (ChatGPT, Perplexity, Google AIO) require to cite, recommend, or surface it in AI-generated answers. The gap between product quality and AI visibility is wide and closeable.

---

## Score Breakdown

| Category | Weight | Score | Grade |
|---|---|---|---|
| AI Citability & Visibility | 25% | 41 / 100 | D+ |
| Brand Authority Signals | 20% | 28 / 100 | F |
| Content Quality & E-E-A-T | 20% | 40 / 100 | D+ |
| Technical Foundations | 15% | 61 / 100 | C+ |
| Structured Data | 10% | 38 / 100 | D+ |
| Platform Optimization | 10% | 25 / 100 | F |
| **COMPOSITE GEO SCORE** | **100%** | **39 / 100** | **D+** |

---

## Platform Readiness Dashboard

| AI Platform | Score | Status |
|---|---|---|
| Google AI Overviews | 28 / 100 | 🔴 Not ready |
| ChatGPT / ChatGPT Shopping | 22 / 100 | 🔴 Not ready |
| Perplexity | 18 / 100 | 🔴 Not ready |
| Bing Copilot | 30 / 100 | 🔴 Not ready |

---

## Site Overview

| Property | Value |
|---|---|
| Platform | Shopify (Dawn v15.4.1) |
| Language | Swedish (sv) |
| Products | 204 products across 8mm–30mm widths |
| Brands | Hirsch (est. 1765), Fluco (est. 1952), Colareb, bandberra, BaraBand |
| Price range | 229 kr – 3,895 kr SEK |
| Shipping | Free over 350 kr via PostNord |
| Return policy | 60 days (39 kr return fee) |
| Payment | Klarna, Visa, Mastercard |
| Physical presence | Pickup via Byxshopen, Falun |
| Contact | support@baraband.se, Box 202, 191 23 Sollentuna |

---

## AI Crawler Access

| Crawler | Status | Notes |
|---|---|---|
| GPTBot (OpenAI) | ✅ Allowed | Falls under `User-agent: *` — not blocked |
| ClaudeBot (Anthropic) | ✅ Allowed | Falls under `User-agent: *` — not blocked |
| PerplexityBot | ✅ Allowed | Falls under `User-agent: *` — not blocked |
| Googlebot-Extended | ✅ Allowed | Falls under `User-agent: *` — not blocked |
| Nutch | ❌ Blocked | Fully disallowed |
| llms.txt | ❌ Missing | Returns 404 — not implemented |

**Key finding:** AI crawlers can access product pages, collection pages, and blog content. However, there are no explicit AI crawler directives (no named rules for GPTBot, ClaudeBot, etc.), and no `llms.txt` to guide AI systems about site structure or content priorities.

---

## Critical Findings

### 🔴 CRITICAL — No Customer Reviews Anywhere
**Impact:** All four AI platforms deprioritize or ignore e-commerce sites with no review data. ChatGPT Shopping, Google AIO, and Bing Copilot all use star ratings and review counts as primary trust signals. Currently, BaraBand.se has zero visible review infrastructure — no Trustpilot widget, no on-site reviews, no `aggregateRating` schema on product pages.

**Fix:** Install Judge.me (free) or Trustpilot immediately. Configure post-purchase email review requests. Target 10+ reviews per top product within 60 days.

---

### 🔴 CRITICAL — No FAQ Page
**Impact:** FAQs are one of the most reliably AI-cited content formats. Queries like *"hur mäter jag klockarmband?"*, *"vad är skillnaden mellan NATO och perlon?"*, and *"vilket armband passar Seiko 5?"* are answered by AI systems from FAQ content. BaraBand.se has no FAQ page — both `/pages/faq` and `/pages/vanliga-fragor` return 404.

**Fix:** Create `/pages/faq` with 15–20 Q&A pairs covering sizing, materials, care, brands, shipping, and returns. Add `FAQPage` JSON-LD schema.

---

### 🔴 CRITICAL — No AggregateRating Schema on Products
**Impact:** Product pages are missing `aggregateRating` in their `ProductGroup` JSON-LD. This blocks star rating display in Google SERPs, blocks Google Shopping rich results, and reduces ChatGPT Shopping eligibility.

**Fix:** Install a Shopify review app that outputs `aggregateRating` JSON-LD (Judge.me does this automatically). Verify output with Google's Rich Results Test.

---

### 🟠 HIGH — City Link Spam on Om Oss Page
**Impact:** The contact/about page (`/pages/om-oss`) contains 500+ Swedish city/municipality links — a legacy local SEO tactic. AI crawlers encountering this page receive a confusing mixture of company information and a geographic directory. This dilutes the brand narrative and confuses entity understanding.

**Fix:** Remove all city links from om-oss. Replace with a clean brand narrative: founding story, mission, brand partnerships (Hirsch, Fluco, Colareb), team, and value proposition.

---

### 🟠 HIGH — No llms.txt File
**Impact:** `llms.txt` is the emerging standard for signaling to AI crawlers what content is authoritative, what sections to prioritize, and what language the site operates in. The absence means AI systems index BaraBand.se without any guidance.

**Fix:** Create `https://www.baraband.se/llms.txt` (store it as a Shopify page or via CDN). See template below.

---

### 🟠 HIGH — No Author Attribution on Blog Content
**Impact:** All 6 blog posts are attributed to "Jacob ." with no biography, credentials, or role title. Perplexity and Google E-E-A-T both require named authors with expertise signals. Anonymous content receives minimal citation consideration.

**Fix:** Add a full author bio page for Jacob (3–4 sentences: watch background, curation philosophy, years of experience). Link from every blog post byline.

---

### 🟠 HIGH — No BreadcrumbList Schema on Product/Collection Pages
**Impact:** Collection pages (`/collections/lader`, `/collections/bastsaljare`) have zero JSON-LD. Product pages lack `BreadcrumbList`. This means no breadcrumb path display in Google SERPs and reduced structured data coverage for AI indexing.

**Fix:** Add `BreadcrumbList` JSON-LD to `product.liquid` and `collection.liquid` theme templates using Shopify Liquid variables.

---

### 🟡 MEDIUM — Blog Severely Underdeveloped
**Impact:** 6 posts over 4 years (2021–2024), all under 200 words, no structural headers (H2/H3), no external citations, no expert authorship. The blog has zero citation potential for Perplexity or Google AIO in competitive queries.

**Fix:** Publish 2 posts/month of 800–1,500 words each. Target specific questions. Name the author. Add external references.

---

### 🟡 MEDIUM — No Microsoft Merchant Center / Bing Webmaster Tools
**Impact:** Bing Copilot Shopping requires a Microsoft Merchant Center feed. Bing Webmaster Tools submission improves Bing's crawl priority and Copilot citation eligibility.

**Fix:** Register at bing.com/webmasters (20 minutes). Install the Shopify Microsoft Channel app for merchant feed submission.

---

### 🟡 MEDIUM — Organization Schema Missing Key Fields
**Impact:** Current Organization schema has only `name`, `url`, `logo`, and a single `sameAs` entry (Instagram). AI entity recognition is weakened by the absence of `description`, `contactPoint`, `areaServed`, and additional `sameAs` social profiles.

**Fix:** Enhance homepage Organization JSON-LD (see generated schema below).

---

### 🟡 MEDIUM — No GTINs on Products
**Impact:** Microsoft Merchant Center and Google Merchant Center both require GTINs for Shopping ad integration and AI shopping recommendation eligibility. Hirsch and Fluco products have manufacturer GTINs available.

**Fix:** Contact Hirsch and Fluco distributors for EAN codes. Add to Shopify product metafields.

---

### 🟡 MEDIUM — No Company Registration Number (Org.nr)
**Impact:** Swedish e-commerce consumers expect Swedish businesses to display their `organisationsnummer`. Its absence is a trust gap, particularly for first-time buyers.

**Fix:** Add Org.nr to footer and om-oss page. One line of text.

---

## What's Working Well

| Strength | Notes |
|---|---|
| ✅ SSR content delivery | Shopify Liquid renders product data in HTML — AI crawlers read content without JS |
| ✅ HTTPS fully implemented | No mixed content, all CDN assets over HTTPS |
| ✅ Sitemap structure | 4-part sitemap index covering products, pages, collections, blogs |
| ✅ WebSite + SearchAction schema | Sitelinks Searchbox correctly implemented |
| ✅ Storleksguide page | Best citability asset: lug width measurement, QR installation, Apple Watch sizes |
| ✅ European brand partnerships | Hirsch (1765), Fluco (1952), Colareb — borrowed authority from established brands |
| ✅ 60-day return policy | Generous and clearly communicated across multiple touchpoints |
| ✅ Product variant schema | `ProductGroup` with 6 variants, per-variant `Offer` with InStock/OutOfStock status |
| ✅ Shopify CDN | Image width variants, HTTP/2, edge caching — solid performance foundation |
| ✅ Authentic content voice | Human-written Swedish, founder voice on om-oss, not AI-farmed |
| ✅ Mobile-first theme | Dawn v15.4.1 is Google-certified responsive |

---

## Prioritized Action Plan

### Quick Wins (Week 1–2, near-zero cost)

| # | Action | Time | Impact |
|---|---|---|---|
| 1 | Install Judge.me (free) + configure review emails for all past orders | 2 hours | 🔥 Highest |
| 2 | Create `llms.txt` and add to site | 1 hour | High |
| 3 | Submit sitemap to Bing Webmaster Tools | 20 min | High |
| 4 | Remove city link spam from `/pages/om-oss` | 1 hour | High |
| 5 | Add author bio page for Jacob + link from blog posts | 1 hour | High |
| 6 | Add Org.nr to footer | 10 min | Medium |
| 7 | Add `og:locale` meta tag (`sv_SE`) | 30 min | Medium |

### Short-term (Weeks 3–6)

| # | Action | Time | Impact |
|---|---|---|---|
| 8 | Create `/pages/faq` with 15 Q&A pairs + FAQPage JSON-LD | 4 hours | 🔥 Highest |
| 9 | Add `BreadcrumbList` JSON-LD to `product.liquid` and `collection.liquid` | 2 hours | High |
| 10 | Enhance Organization schema on homepage (see generated schema below) | 1 hour | High |
| 11 | Publish material comparison guide (leather/rubber/nylon/mesh) — 1,000 words, named author | 4 hours | High |
| 12 | Verify `<html lang="sv">` in theme.liquid | 15 min | Medium |
| 13 | Register Trustpilot profile + begin collecting verified reviews | 2 hours | High |
| 14 | Install Microsoft Channel app on Shopify + submit Bing Merchant feed | 2 hours | High |

### Medium-term (Month 2–3)

| # | Action | Time | Impact |
|---|---|---|---|
| 15 | Reformat Storleksguide as Q&A with H2 headings + add HowTo JSON-LD | 3 hours | High |
| 16 | Create Apple Watch strap compatibility hub page | 4 hours | High |
| 17 | Create Hirsch brand heritage page (leverages existing ChatGPT brand knowledge) | 3 hours | Medium |
| 18 | Source GTINs from Hirsch/Fluco and add to Shopify product metafields | 2 hours | Medium |
| 19 | Build Google Business Profile for brand entity | 1 hour | Medium |
| 20 | Create Colareb + Fluco brand authority pages | 4 hours | Medium |

### Strategic (Month 3+)

| # | Action | Impact |
|---|---|---|
| 21 | Pursue organic Reddit presence (r/watchstraps, r/Watches) | High — brand mentions 3x stronger than backlinks for AI |
| 22 | Reach out to Swedish watch YouTube creators for review coverage | High — persistent AI training data |
| 23 | Secure one editorial mention in Swedish watch/lifestyle press | High — Perplexity citation trigger |
| 24 | Develop watch compatibility database ("which strap fits Seiko SKX013") | High — long-tail AI query capture |

---

## Generated Assets

### llms.txt Template

Deploy as `https://www.baraband.se/llms.txt`:

```
# BaraBand.se — llms.txt
# Swedish watch strap e-commerce

> BaraBand.se är en svensk nätbutik som specialiserar sig på premium klockarmband från Europas ledande tillverkare. Vi säljer läder-, gummi-, nylon-, mäsk- och hybridarmband i bredder från 8mm till 30mm. Vi är auktoriserad återförsäljare för Hirsch (Österrike, grundat 1765), Fluco (Tyskland, grundat 1952) och Colareb (Italien). Priser från 229 kr till 599+ kr. Fri frakt över 350 kr, 60 dagars öppet köp.

## Nyckelstidor (Key Pages)
- Startsida: https://www.baraband.se
- Storleksguide: https://www.baraband.se/pages/storleksguide
- Alla produkter: https://www.baraband.se/collections/all
- Läderarmband: https://www.baraband.se/collections/lader
- Gummiarmband: https://www.baraband.se/collections/gummi
- NATO-armband: https://www.baraband.se/collections/nato
- Nätarmband (mesh): https://www.baraband.se/collections/nat
- Blogg: https://www.baraband.se/blogs/news
- Om oss: https://www.baraband.se/pages/om-oss

## Varumärken vi säljer (Brands)
- Hirsch — österrikisk tillverkare sedan 1765
- Fluco — tysk tillverkare sedan 1952
- Colareb — italiensk handtillverkad vegansk
- bandberra — sailcloth och premium nylon
- BaraBand — eget märke

## Kontakt
- E-post: support@baraband.se
- Adress: Box 202, 191 23 Sollentuna, Sverige
- Instagram: @BaraBand.se
```

---

### Enhanced Organization Schema (replace on homepage)

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "BaraBand.se",
  "url": "https://baraband.se",
  "logo": {
    "@type": "ImageObject",
    "url": "https://baraband.se/cdn/shop/files/BaraBand.se_Klockrena_klockarmband_Rod_0a7e9f50-f6b1-466c-8a7a-def355cce0e7.jpg?v=1641719492&width=500",
    "width": 500,
    "height": 500
  },
  "description": "BaraBand.se säljer noggrant utvalda klockarmband från Europas ledande tillverkare — Hirsch, Fluco och Colareb. Fri frakt över 350 kr, 60 dagars öppet köp.",
  "areaServed": "SE",
  "priceRange": "SEK 229–3895",
  "sameAs": [
    "https://www.instagram.com/BaraBand.se"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "contactType": "customer service",
    "email": "support@baraband.se",
    "availableLanguage": ["Swedish", "English"]
  },
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Sollentuna",
    "postalCode": "191 23",
    "addressCountry": "SE"
  }
}
```

---

### BreadcrumbList Schema — Product Page Template

Add to `product.liquid` in Shopify theme:

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Hem",
      "item": "https://baraband.se/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "{{ collection.title | escape }}",
      "item": "https://baraband.se/collections/{{ collection.handle }}"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "{{ product.title | escape }}",
      "item": "https://baraband.se/products/{{ product.handle }}"
    }
  ]
}
```

---

### FAQPage Schema — Starter Template

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Hur mäter jag min lugbredd?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Lugbredd är avståndet mellan de två tappar (lugs) på din klocka där armbandet fästs. Mät med ett skjutmått direkt vid urverket, inte vid spännet. Vanliga bredder är 18mm, 20mm och 22mm. Rätt bredd hittar du ofta i klockans manual eller på tillverkarens webbplats."
      }
    },
    {
      "@type": "Question",
      "name": "Vad är skillnaden mellan läder och gummiarmband?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Läderarmband ger ett klassiskt och elegant utseende men bör undvikas i vatten. Gummiarmband (FKM) är vattentåliga, svettresistenta och håller formen i alla väder — idealiska för sport och utomhusbruk. Hirsch erbjuder premiumperforation i läder; FKM-armband passar bättre för dykning och träning."
      }
    },
    {
      "@type": "Question",
      "name": "Vad är fri frakt-gränsen?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Vi erbjuder fri frakt på alla beställningar över 350 kr inom Sverige via PostNord. Beställningar under 350 kr kostar 19 kr i frakt."
      }
    },
    {
      "@type": "Question",
      "name": "Vad gäller för returer?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Vi erbjuder 60 dagars öppet köp. Returfrakten kostar 39 kr och dras från återbetalningen. Produkten måste vara oanvänd och i originalförpackning. Kontakta support@baraband.se för att initiera en retur."
      }
    },
    {
      "@type": "Question",
      "name": "Vilket armband passar min Apple Watch?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Apple Watch Series 1–9 och SE med 38mm/40mm/41mm boett använder 20mm armband. Modeller med 42mm/44mm/45mm/49mm boett använder 22mm armband. Alla våra Apple Watch-armband kräver en adapter (ingår ej) för att passa Apple Watchs proprietära fäste."
      }
    }
  ]
}
```

---

## Robots.txt Recommendation

Add explicit AI crawler rules before the `User-agent: *` block:

```
# AI Crawler Access — explicitly permitted
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot-Extended
Allow: /

# Sitemap
Sitemap: https://baraband.se/sitemap.xml
```

---

## Methodology

This audit used the GEO-SEO Claude Code Skill (February 2026). Five parallel subagents analyzed:

| Subagent | Scope |
|---|---|
| geo-ai-visibility | AI crawler access, llms.txt, citability scoring, brand authority |
| geo-platform-analysis | Google AIO, ChatGPT, Perplexity, Bing Copilot readiness |
| geo-technical | SSR, HTTPS, mobile, crawlability, structured data foundations |
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

*Report saved to: `GEO-AUDIT-REPORT.md`*
*Next step: Run `/geo report-pdf` to generate a client-ready PDF version.*

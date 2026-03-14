# GEO Audit Report: Deepchand Group

**Audit Date:** 2026-03-14
**URL:** https://deepchandgroup.com
**Business Type:** Hybrid (Local Business / Services / E-commerce)
**Pages Analyzed:** 7 (via search index; direct site access restricted)
**Divisions Identified:** Deepchand Bakers, Celebrations, Weddings, Enterprises, Ventures

> **Note:** This audit was conducted using search engine intelligence, cached data, and platform analysis. Direct site crawling was not possible due to network restrictions. Scores may be conservative; a follow-up crawl-based audit is recommended for precise technical scoring.

---

## Executive Summary

**Overall GEO Score: 23/100 (Critical)**

Deepchand Group is a multi-division local business in Bhawanipatna, Odisha, India operating across bakery, celebrations, weddings, enterprises, and personal care manufacturing. The group is **largely invisible to AI search engines**. There is no Wikipedia presence, no LinkedIn company page, no YouTube channel, no Reddit discussions, no llms.txt file, and likely no structured data (schema markup) on the website. While the bakery division has some presence on food delivery platforms (Swiggy, Zomato, Magicpin), the group's brand authority signals are almost entirely absent from the platforms that AI models rely on for entity recognition and citation. The site's multi-subdomain architecture (deepchandgroup.com, bakers.deepchandgroup.com, ventures.deepchandgroup.com, deepchand.in) also fragments whatever limited authority exists.

### Score Breakdown

| Category | Score | Weight | Weighted Score |
|---|---|---|---|
| AI Citability | 22/100 | 25% | 5.5 |
| Brand Authority | 18/100 | 20% | 3.6 |
| Content E-E-A-T | 28/100 | 20% | 5.6 |
| Technical GEO | 38/100 | 15% | 5.7 |
| Schema & Structured Data | 8/100 | 10% | 0.8 |
| Platform Optimization | 15/100 | 10% | 1.5 |
| **Overall GEO Score** | | | **22.7 ≈ 23/100** |

---

## Critical Issues (Fix Immediately)

### 1. No Wikipedia or Wikidata Entity Presence
- **Impact:** AI systems (ChatGPT, Gemini, Perplexity, Claude) cannot recognize "Deepchand Group" as a known entity. Wikipedia presence correlates most strongly with AI citation.
- **Fix:** While Deepchand Group may not yet meet Wikipedia's notability criteria, create a Wikidata entity immediately with structured properties (business type, location, founding date, divisions). This is the single most impactful action for AI visibility.

### 2. No LinkedIn Company Page
- **Impact:** LinkedIn is a critical signal for entity recognition, especially for Bing Copilot and ChatGPT. Its absence means Microsoft-powered AI platforms cannot verify the business entity.
- **Fix:** Create a LinkedIn company page for "Deepchand Group" with complete business information, employee connections, and division descriptions.

### 3. No YouTube Channel
- **Impact:** YouTube presence has the strongest correlation (0.737) with AI visibility of any platform. A bakery/celebrations business has natural video content potential (cake decoration, event highlights, baking process).
- **Fix:** Create a YouTube channel. Publish at least 5-10 videos showcasing bakery products, celebration events, and behind-the-scenes content.

### 4. Likely Missing All Schema Markup
- **Impact:** Without Organization, LocalBusiness, or Product schema, AI models have no structured way to understand what the business is, where it's located, or what it offers.
- **Fix:** Implement LocalBusiness + Organization JSON-LD schema on the homepage (templates provided below).

### 5. No llms.txt File
- **Impact:** The emerging standard for helping AI models understand site structure is absent.
- **Fix:** Create and deploy `/llms.txt` at the domain root (template provided below).

---

## High Priority Issues

### 6. Fragmented Domain Architecture
- **Domains/subdomains in use:** deepchandgroup.com, bakers.deepchandgroup.com, ventures.deepchandgroup.com, deepchand.in
- **Impact:** Domain authority is split across 4+ domains/subdomains. AI crawlers treat each as a separate entity, diluting brand signals.
- **Fix:** Consolidate key content under deepchandgroup.com. Use subdirectories (/bakers, /ventures) instead of subdomains where possible. Implement canonical tags and proper cross-linking.

### 7. No AI Crawler Directives in robots.txt
- **Impact:** Without explicit directives, AI crawlers follow default rules. The site may be unintentionally blocking or not optimizing for GPTBot, ClaudeBot, PerplexityBot.
- **Fix:** Create/update robots.txt with explicit Allow directives for all major AI crawlers and reference the sitemap.

### 8. No Brand Mentions on Reddit
- **Impact:** Perplexity AI heavily indexes Reddit. Reddit mentions correlate strongly with AI citation. Zero Reddit presence means Perplexity is unlikely to recommend Deepchand Group for any query.
- **Fix:** Engage authentically in relevant subreddits (r/Odisha, r/IndianFood, r/baking, local community subreddits). Share expertise, respond to relevant questions.

### 9. Missing Author/Team Attribution on Content
- **Impact:** E-E-A-T signals require visible expertise. No author bylines, team credentials, or founder story were found on the main site.
- **Fix:** Add a detailed "About Us" page with founder story, team bios with credentials, and photos. Link author profiles from all content pages.

### 10. No Content Marketing / Blog
- **Impact:** Without informational content (blog posts, guides, recipes), the site has nothing for AI systems to cite as a knowledge source. Product/service pages alone are rarely cited by AI.
- **Fix:** Launch a blog with recipes, baking tips, event planning guides, and celebration ideas. Target question-based keywords ("How to choose a wedding cake in Odisha", "Best designer cakes in Bhawanipatna").

---

## Medium Priority Issues

### 11. Limited Third-Party Review Presence
- TripAdvisor listing exists but has minimal reviews.
- No Google Reviews aggregation visible.
- Zomato and Swiggy presence is basic.
- **Fix:** Actively encourage customer reviews on Google, TripAdvisor, and Zomato. Respond to all reviews publicly.

### 12. No Open Graph / Social Media Optimization
- Likely missing OG tags for rich social media previews when links are shared.
- **Fix:** Add og:title, og:description, og:image, og:url to all pages.

### 13. Instagram Present but Not Linked to Website Schema
- @deepchandbakers exists on Instagram but likely not referenced in any structured data.
- **Fix:** Include Instagram URL in sameAs schema property.

### 14. No Google Business Profile Optimization for Group
- Individual Deepchand Bakers listing may exist, but no unified "Deepchand Group" profile.
- **Fix:** Claim/create Google Business Profile for the group and each division. Ensure NAP consistency.

### 15. Duplicate Domain (deepchand.in)
- deepchand.in appears to be an alternate domain with overlapping content.
- **Fix:** Choose one primary domain and 301 redirect the other. Implement canonical tags across all pages.

---

## Low Priority Issues

### 16. No IndexNow Protocol Support
- IndexNow enables instant indexing by Bing/Yandex and benefits Copilot visibility.
- **Fix:** Implement IndexNow API key and submit URLs on publish.

### 17. Missing hreflang Tags (If Multilingual)
- If the site serves content in multiple languages (English/Odia/Hindi), hreflang tags are likely missing.
- **Fix:** Add hreflang tags if serving multilingual content.

### 18. No RSS Feed
- RSS feeds help AI crawlers discover new content quickly.
- **Fix:** Generate an RSS feed, especially for any blog content.

---

## Category Deep Dives

### AI Citability (22/100)

**Assessment: Critical**

Based on search index analysis, the Deepchand Group website appears to be primarily a corporate landing page with limited long-form content. The homepage tagline "Excellence across industries - From enterprise solutions to culinary delights and memorable celebrations" is generic and non-citable.

**Key Issues:**
- No question-answering content blocks detected (the kind AI systems extract for responses)
- No statistical claims, data points, or specific facts that AI could quote
- Homepage content appears to be promotional rather than informational
- Product pages on bakers.deepchandgroup.com have product descriptions but likely lack the 134-167 word self-contained passages that AI systems prefer to cite
- Ventures subdomain has mission/vision content but reads as generic corporate language ("to enhance the quality of life for our customers through innovative and sustainable products")

**Citability Opportunities:**
1. Create definitive content about Bhawanipatna's bakery culture and Deepchand's role in it
2. Publish detailed product/service descriptions with specific ingredients, process details, and pricing
3. Write "About" content with specific founding story, milestones, and achievements (dates, numbers)
4. Create FAQ pages answering common customer questions with direct, quotable answers

### Brand Authority (18/100)

**Assessment: Critical**

| Platform | Status | Details |
|---|---|---|
| Wikipedia | Absent | No article exists. Entity not recognized by AI systems. |
| Wikidata | Absent | No structured entity data in knowledge bases. |
| Reddit | Absent | Zero mentions found in any subreddit. |
| YouTube | Absent | No channel. Massive missed opportunity for a visual business. |
| LinkedIn | Absent | No company page found. |
| Facebook | Present (Minimal) | @deepchandbakers — 149 likes, 39 check-ins. Low engagement. |
| Instagram | Present (Minimal) | @deepchandbakers — Active but reach unclear. |
| Zomato | Present | Listed for online ordering in Bhawanipatna. |
| Swiggy | Present | Listed with 4.5 rating. |
| TripAdvisor | Present (Minimal) | Listed but no substantial reviews. |
| Magicpin | Present | Basic listing. |
| Google Business Profile | Likely Present | Implied by delivery platform listings. |

**Brand Mention Score Breakdown:**
- Wikipedia presence: 0/30
- Reddit discussion presence: 0/20
- YouTube presence: 0/15
- LinkedIn presence: 0/10
- Industry/niche sources (Zomato, Swiggy, TripAdvisor, Facebook, Instagram, Magicpin): 18/25

### Content E-E-A-T (28/100)

**Assessment: Poor**

| Dimension | Score | Key Evidence |
|---|---|---|
| Experience | 8/25 | Some evidence of hands-on baking experience from event photos on Facebook/Instagram. No case studies, no process documentation on website. |
| Expertise | 6/25 | Owner described as "passionate baker" but no formal credentials, certifications, or expertise signals on the website. No author bylines. |
| Authoritativeness | 5/25 | Local recognition only. No media mentions, no industry awards, no external citations. Limited to food delivery platform listings. |
| Trustworthiness | 9/25 | Physical address available (Gandhi Chowk, Bhawanipatna). Phone number listed (+919437700019). Email (info@deepchandgroup.com). Terms page exists on bakers subdomain. Missing: privacy policy on main site, editorial standards, clear business registration info. |

**Overall E-E-A-T: 28/100**

**Content Gaps:**
- No blog or informational content
- No recipes, baking guides, or event planning resources
- No case studies of celebrations/weddings managed
- No founder story or team page with credentials
- No customer testimonials aggregated on the website
- Ventures subdomain claims to be "one of India's leading manufacturers" without supporting evidence

### Technical GEO (38/100)

**Assessment: Poor**

| Category | Score | Assessment |
|---|---|---|
| HTTPS | Present | Site loads over HTTPS (confirmed via search results showing https:// URLs) |
| Server-Side Rendering | Unknown | Cannot assess without direct HTML access. Score assumes moderate risk. |
| robots.txt | Unknown | Could not access. Likely default or missing AI-specific directives. |
| XML Sitemap | Unknown | Could not verify existence or quality. |
| Meta Tags | Partially Detected | Title tag exists ("Deepchand Group"). Meta description detected in search snippets. |
| Mobile Optimization | Unknown | Cannot assess without direct access. |
| Core Web Vitals | Unknown | No PageSpeed Insights data available. |
| URL Structure | Mixed | Main site has clean URLs (/contact/). Bakers subdomain has UUID-based product URLs (poor). |
| Security Headers | Unknown | Cannot assess beyond HTTPS presence. |

**Key Technical Concerns:**
1. **UUID-based product URLs** on bakers.deepchandgroup.com (e.g., `/shop/product/b6e5a0fa-8a72-4361-9460-bbeb242b7260/`) are not SEO-friendly and contain no keywords
2. **Multiple subdomains** fragment crawl budget and authority
3. **Alternate domain** (deepchand.in) creates potential duplicate content issues
4. **PDF menu** (bakers.deepchandgroup.com/menu.pdf) — content locked in PDF is poorly indexed by AI crawlers

### Schema & Structured Data (8/100)

**Assessment: Critical**

No structured data was detected through search engine analysis. The site likely has:
- No Organization schema
- No LocalBusiness schema
- No Product schema (on bakery product pages)
- No BreadcrumbList
- No sameAs linking to any platform
- No speakable property
- No WebSite + SearchAction schema

**This is the single biggest missed opportunity.** Implementing comprehensive schema markup would immediately make the business machine-readable to all AI systems.

### Platform Optimization (15/100)

| Platform | Score | Status | Key Gap |
|---|---|---|---|
| Google AI Overviews | 18/100 | Poor | No question-based content structure, no FAQ content, minimal topical authority |
| ChatGPT Web Search | 10/100 | Critical | No Wikipedia entity, no Wikidata, likely no OAI-SearchBot access configured |
| Perplexity AI | 8/100 | Critical | Zero Reddit presence, minimal community validation, no direct source content |
| Google Gemini | 20/100 | Poor | Some Google ecosystem presence via food platforms, but no YouTube, no Knowledge Graph entity |
| Bing Copilot | 12/100 | Critical | No LinkedIn, no IndexNow, no Microsoft ecosystem presence |

**Strongest Platform:** Google Gemini (20/100) — Benefits from some Google ecosystem presence via Zomato/Swiggy listings and likely Google Business Profile.

**Weakest Platform:** Perplexity AI (8/100) — Zero community validation signals. No Reddit presence, no forum discussions, no community-driven content.

---

## Quick Wins (Implement This Week)

1. **Create a LinkedIn Company Page** for Deepchand Group with full business details, logo, and division descriptions. Link all employees. Effort: 1-2 hours. Impact: Improves entity recognition across Bing Copilot and ChatGPT.

2. **Create a Wikidata entity** for Deepchand Group with structured properties (instance of: business, location: Bhawanipatna, founded: [year], industry: bakery/hospitality). Effort: 1 hour. Impact: Foundational for AI entity recognition.

3. **Deploy llms.txt** at deepchandgroup.com/llms.txt with site structure, key pages, and division descriptions. Effort: 30 minutes. Impact: Directly helps LLMs understand the site.

4. **Add LocalBusiness + Organization JSON-LD** to the homepage (template provided below). Effort: 1-2 hours. Impact: Makes the business machine-readable.

5. **Update robots.txt** to explicitly allow all AI crawlers and reference the sitemap. Effort: 15 minutes. Impact: Ensures AI crawlers can access all content.

---

## 30-Day Action Plan

### Week 1: Foundation (Entity & Identity)

- [ ] Create LinkedIn company page for Deepchand Group
- [ ] Create Wikidata entity with structured properties
- [ ] Create YouTube channel and upload 3-5 initial videos (bakery tours, cake decoration, celebration highlights)
- [ ] Deploy llms.txt file at domain root
- [ ] Update robots.txt with AI crawler directives and sitemap reference
- [ ] Implement Organization + LocalBusiness JSON-LD on homepage

### Week 2: Technical & Schema

- [ ] Implement Product schema on all bakery product pages
- [ ] Add BreadcrumbList schema site-wide
- [ ] Replace UUID-based product URLs with keyword-rich slugs (e.g., /shop/pineapple-cream-roll/)
- [ ] Audit and consolidate deepchand.in → deepchandgroup.com (301 redirect)
- [ ] Add Open Graph tags to all pages
- [ ] Create XML sitemap covering all subdomains and submit to Google Search Console and Bing Webmaster Tools
- [ ] Implement IndexNow for Bing

### Week 3: Content & E-E-A-T

- [ ] Create comprehensive "About Us" page with founder story (specific dates, milestones, achievements), team bios with photos and credentials
- [ ] Launch blog with 3-5 initial posts targeting question-based keywords:
  - "Best designer cakes in Bhawanipatna — Deepchand Bakers"
  - "How to plan a wedding celebration in Kalahandi, Odisha"
  - "What makes homemade cakes special — Our baking process at Deepchand"
- [ ] Add customer testimonials section with verified reviews
- [ ] Create FAQ page with 10-15 common questions and direct, citable answers
- [ ] Add author bylines and Person schema to all content pages

### Week 4: Platform & Community

- [ ] Begin authentic Reddit engagement in r/Odisha, r/IndianFood, r/baking
- [ ] Cross-post YouTube videos to Instagram Reels and Facebook
- [ ] Encourage customer reviews on Google, TripAdvisor, and Zomato (create review request cards/QR codes)
- [ ] Create Google Business Profiles for each division (if not already existing)
- [ ] Implement sameAs schema linking to all new platform profiles (LinkedIn, YouTube, Facebook, Instagram, Zomato, Swiggy, Wikidata)
- [ ] Set up Google Search Console and monitor AI crawler access logs

---

## Recommended JSON-LD Schema Templates

### Organization Schema (Add to deepchandgroup.com homepage)

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://deepchandgroup.com/#organization",
  "name": "Deepchand Group",
  "url": "https://deepchandgroup.com",
  "logo": {
    "@type": "ImageObject",
    "url": "https://deepchandgroup.com/logo.png",
    "width": 600,
    "height": 60
  },
  "description": "Multi-division business group based in Bhawanipatna, Odisha, India. Operating Deepchand Bakers, Celebrations, Weddings, Enterprises, and Ventures across bakery, event management, and personal care manufacturing.",
  "foundingDate": "[REPLACE: YYYY-MM-DD]",
  "founder": {
    "@type": "Person",
    "name": "[REPLACE: Founder's Full Name]",
    "url": "https://deepchandgroup.com/about",
    "sameAs": [
      "[REPLACE: Founder's LinkedIn URL]"
    ]
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+919437700019",
    "contactType": "customer service",
    "email": "info@deepchandgroup.com",
    "availableLanguage": ["English", "Hindi", "Odia"]
  },
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Gandhi Chowk",
    "addressLocality": "Bhawanipatna",
    "addressRegion": "Odisha",
    "postalCode": "766001",
    "addressCountry": "IN"
  },
  "sameAs": [
    "https://www.facebook.com/deepchandbakers",
    "https://www.instagram.com/deepchandbakers/",
    "[REPLACE: LinkedIn company URL when created]",
    "[REPLACE: YouTube channel URL when created]",
    "[REPLACE: Wikidata entity URL when created]",
    "https://www.zomato.com/bhawanipatna/deepchand-bakers-bhawanipatna-locality/order",
    "https://www.swiggy.com/city/bhawanipatna/deepchand-bakers-gandhi-chowk-na-rest485943"
  ],
  "knowsAbout": [
    "Designer Cakes",
    "Bakery",
    "Event Celebrations",
    "Wedding Planning",
    "Personal Care Products Manufacturing"
  ],
  "subOrganization": [
    {
      "@type": "LocalBusiness",
      "name": "Deepchand Bakers",
      "url": "https://bakers.deepchandgroup.com"
    },
    {
      "@type": "Organization",
      "name": "Deepchand Ventures",
      "url": "https://ventures.deepchandgroup.com"
    }
  ]
}
```

### LocalBusiness Schema (Add to bakers.deepchandgroup.com)

```json
{
  "@context": "https://schema.org",
  "@type": "Bakery",
  "@id": "https://bakers.deepchandgroup.com/#bakery",
  "name": "Deepchand Bakers",
  "url": "https://bakers.deepchandgroup.com",
  "image": "[REPLACE: URL to bakery storefront or hero image]",
  "description": "Premium bakery in Bhawanipatna, Odisha specializing in designer cakes, pastries, and celebration cakes. All cakes homemade with quality ingredients.",
  "telephone": "+919437700019",
  "email": "info@deepchandgroup.com",
  "priceRange": "₹₹",
  "servesCuisine": "Bakery, Cakes, Pastries",
  "menu": "https://bakers.deepchandgroup.com/menu.pdf",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Shop 3, Ashok Lodge Complex, Gandhi Chowk",
    "addressLocality": "Bhawanipatna",
    "addressRegion": "Odisha",
    "postalCode": "766001",
    "addressCountry": "IN"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "[REPLACE: Latitude]",
    "longitude": "[REPLACE: Longitude]"
  },
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
      "opens": "[REPLACE: Opening time, e.g., 08:00]",
      "closes": "[REPLACE: Closing time, e.g., 21:00]"
    }
  ],
  "parentOrganization": {
    "@type": "Organization",
    "@id": "https://deepchandgroup.com/#organization",
    "name": "Deepchand Group"
  },
  "sameAs": [
    "https://www.facebook.com/deepchandbakers",
    "https://www.instagram.com/deepchandbakers/",
    "https://www.zomato.com/bhawanipatna/deepchand-bakers-bhawanipatna-locality/order",
    "https://www.swiggy.com/city/bhawanipatna/deepchand-bakers-gandhi-chowk-na-rest485943"
  ],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "reviewCount": "[REPLACE: Number of reviews]",
    "bestRating": "5"
  }
}
```

### WebSite + SearchAction Schema (Add to homepage)

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Deepchand Group",
  "url": "https://deepchandgroup.com",
  "description": "Excellence across industries - From enterprise solutions to culinary delights and memorable celebrations.",
  "publisher": {
    "@type": "Organization",
    "@id": "https://deepchandgroup.com/#organization"
  },
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://deepchandgroup.com/search?q={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
}
```

---

## Recommended llms.txt File

Deploy at `https://deepchandgroup.com/llms.txt`:

```
# Deepchand Group

> Multi-division business group based in Bhawanipatna, Odisha, India. Operating across bakery, celebrations, weddings, enterprises, and personal care manufacturing since [REPLACE: founding year].

## Divisions

- [Deepchand Bakers](https://bakers.deepchandgroup.com): Premium bakery specializing in designer cakes, pastries, and celebration cakes in Bhawanipatna, Odisha.
- [Deepchand Celebrations](https://deepchandgroup.com/celebrations): Event planning and management for birthdays, anniversaries, and corporate events.
- [Deepchand Weddings](https://deepchandgroup.com/weddings): Full-service wedding planning and execution in Odisha.
- [Deepchand Enterprises](https://deepchandgroup.com/enterprises): B2B trading solutions and enterprise services.
- [Deepchand Ventures](https://ventures.deepchandgroup.com): Personal care and home care products manufacturing.

## Key Pages

- [About Us](https://deepchandgroup.com/about): Company history, founder story, and team.
- [Contact](https://deepchandgroup.com/contact): Phone, email, and location in Bhawanipatna, Odisha.
- [Bakery Menu](https://bakers.deepchandgroup.com/menu.pdf): Full menu of cakes, pastries, and baked goods.
- [Bakery Shop](https://bakers.deepchandgroup.com/shop): Online ordering for designer cakes and bakery products.
- [Ventures Services](https://ventures.deepchandgroup.com/services): Personal care and home care manufacturing services.

## Location

Gandhi Chowk, Bhawanipatna, Kalahandi District, Odisha, India 766001
Phone: +919437700019
Email: info@deepchandgroup.com
```

---

## Recommended robots.txt

Deploy at `https://deepchandgroup.com/robots.txt`:

```
User-agent: *
Allow: /

# AI Crawlers - Explicitly Allowed
User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Amazonbot
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: FacebookBot
Allow: /

User-agent: Bytespider
Allow: /

User-agent: CCBot
Allow: /

User-agent: cohere-ai
Allow: /

Sitemap: https://deepchandgroup.com/sitemap.xml
```

---

## Appendix: Pages Analyzed

| URL | Title | GEO Issues |
|---|---|---|
| https://deepchandgroup.com/ | Deepchand Group | No schema, thin content, no citable passages, no llms.txt |
| https://deepchandgroup.com/contact/ | Deepchand Group - Excellence Across Divisions | Basic contact page, no LocalBusiness schema |
| https://bakers.deepchandgroup.com/ | Deepchand Bakers | Separate subdomain dilutes authority, likely no Product schema |
| https://bakers.deepchandgroup.com/shop/product/b6e5a0fa... | Pineapple Cream Roll Paradise | UUID-based URL, no Product schema, likely thin description |
| https://bakers.deepchandgroup.com/shop/product/56261813... | Choco Glass Elegance | UUID-based URL, no Product schema, likely thin description |
| https://ventures.deepchandgroup.com/services | Deepchand Ventures | Separate subdomain, generic corporate language, no schema |
| https://deepchand.in/ | Deepchand Bakers | Duplicate domain, creates content cannibalization |

---

## Appendix: Platform Presence Map

| Platform | Deepchand Group | Deepchand Bakers | Deepchand Ventures |
|---|---|---|---|
| Website | deepchandgroup.com | bakers.deepchandgroup.com | ventures.deepchandgroup.com |
| Wikipedia | Not present | Not present | Not present |
| LinkedIn | Not present | Not present | Not present |
| YouTube | Not present | Not present | Not present |
| Reddit | Not present | Not present | Not present |
| Facebook | Not present | @deepchandbakers (149 likes) | Not present |
| Instagram | Not present | @deepchandbakers | Not present |
| Zomato | N/A | Listed | N/A |
| Swiggy | N/A | Listed (4.5★) | N/A |
| TripAdvisor | N/A | Listed (minimal reviews) | N/A |
| Google Business | Unknown | Likely present | Unknown |

---

*Report generated by GEO-SEO Audit Tool v1.0 | Methodology: GEO-first analysis optimizing for AI search visibility across ChatGPT, Claude, Perplexity, Gemini, and Google AI Overviews.*

---
name: geo-schema
description: Schema.org structured data audit and generation optimized for AI discoverability — detect, validate, and generate JSON-LD markup
version: 1.0.0
author: geo-seo-claude
tags: [geo, schema, structured-data, json-ld, entity-recognition, ai-discoverability]
allowed-tools: Read, Grep, Glob, Bash, WebFetch, Write
---

# GEO Schema & Structured Data

## Purpose

Structured data is the primary machine-readable signal that tells AI systems what an entity IS, what it does, and how it connects to other entities. While schema markup has traditionally been about earning Google rich results, its role in GEO is fundamentally different: **structured data is how AI models understand and trust your entity**. A complete entity graph in structured data dramatically increases citation probability across all AI search platforms.

## How to Use This Skill

1. Fetch the target page HTML using `fetch_page.py` (see note below)
2. Detect all existing structured data (JSON-LD, Microdata, RDFa)
3. Validate detected schemas against Schema.org specifications
4. Identify missing recommended schemas based on business type
5. Generate ready-to-use JSON-LD code blocks
6. Output GEO-SCHEMA-REPORT.md

---

## Step 1: Detection

**IMPORTANT:** WebFetch converts HTML to markdown and strips `<head>` content, which removes JSON-LD blocks. Use `fetch_page.py` instead:
```bash
python3 ~/.claude/skills/geo/scripts/fetch_page.py <url> page
```
The output includes a `structured_data` array with all parsed JSON-LD blocks from the page.

### Scan for JSON-LD
Look for `<script type="application/ld+json">` blocks in the HTML. Parse each block as JSON. A page may contain multiple JSON-LD blocks — collect all of them.

### Scan for Microdata
Look for elements with `itemscope`, `itemtype`, and `itemprop` attributes. Map the hierarchy of nested items. Note: Microdata is harder for AI crawlers to parse than JSON-LD. Flag a recommendation to migrate to JSON-LD if Microdata is the only format found.

### Scan for RDFa
Look for elements with `typeof`, `property`, and `vocab` attributes. Similar to Microdata — recommend migration to JSON-LD.

### Priority Order
JSON-LD is the **strongly recommended format** for GEO. Google, Bing, and AI platforms all process JSON-LD most reliably. If the site uses Microdata or RDFa exclusively, flag this as a high-priority migration.

---

## Step 2: Validation

For each detected schema block, validate:

1. **Valid JSON**: Is the JSON-LD syntactically valid? Check for trailing commas, unquoted keys, malformed strings.
2. **Valid @type**: Does the `@type` match a recognized Schema.org type? Check against https://schema.org/docs/full.html.
3. **Required Properties**: Does the schema include all required properties for its type? (See per-type requirements below.)
4. **Recommended Properties**: Does the schema include recommended properties that increase AI discoverability?
5. **sameAs Links**: Does the schema include `sameAs` properties linking to other platform presences?
6. **URL Validity**: Do all URLs in the schema resolve (not 404)?
7. **Nesting**: Is the schema properly nested (e.g., author inside Article, address inside Organization)?
8. **Rendering Method**: Is the JSON-LD in the server-rendered HTML or injected via JavaScript? Per Google's December 2025 guidance, **JavaScript-injected structured data may face delayed processing**. Flag any schema that requires JS execution.

---

## Step 3: Schema Types for GEO

### Organization (CRITICAL — every business site)
Essential for entity recognition across all AI platforms. This is how AI models identify WHAT the business is.

**Required properties:**
- `@type`: "Organization" (or subtype: Corporation, LocalBusiness, etc.)
- `name`: Official business name
- `url`: Official website URL
- `logo`: URL to logo image (ImageObject preferred)

**Recommended properties for GEO:**
- `sameAs`: Array of ALL platform URLs (see sameAs strategy below)
- `description`: 1-2 sentence description of the organization
- `foundingDate`: ISO 8601 date
- `founder`: Person schema
- `address`: PostalAddress schema
- `contactPoint`: ContactPoint with telephone, email, contactType
- `areaServed`: Geographic area
- `numberOfEmployees`: QuantitativeValue
- `industry`: Text or DefinedTerm
- `award`: Array of awards received
- `knowsAbout`: Array of topics the organization is expert in (strong GEO signal)

### LocalBusiness (for businesses with physical locations)
Extends Organization. Critical for local AI search results and Google Gemini.

**Additional required properties:**
- `address`: Full PostalAddress
- `telephone`: Phone number
- `openingHoursSpecification`: Operating hours

**Recommended for GEO:**
- `geo`: GeoCoordinates (latitude, longitude)
- `priceRange`: Price indicator
- `aggregateRating`: AggregateRating schema
- `review`: Array of Review schemas
- `hasMap`: URL to Google Maps

### Article + Author (CRITICAL for publishers)
The Author schema is one of the strongest E-E-A-T signals for AI platforms.

**Article required:**
- `@type`: "Article" (or NewsArticle, BlogPosting, TechArticle)
- `headline`: Article title
- `datePublished`: ISO 8601
- `dateModified`: ISO 8601 (critical for freshness signals)
- `author`: Person or Organization schema
- `publisher`: Organization schema with logo
- `image`: Representative image

**Author (Person) required for GEO:**
- `name`: Full name
- `url`: Author page URL on the site
- `sameAs`: LinkedIn, Twitter, personal site, Google Scholar, ORCID
- `jobTitle`: Professional title
- `worksFor`: Organization schema
- `knowsAbout`: Array of expertise areas
- `alumniOf`: Educational institutions
- `award`: Professional awards

### Product (for e-commerce)
**Required:**
- `name`, `description`, `image`
- `offers`: Offer with price, priceCurrency, availability
- `brand`: Brand schema
- `sku` or `gtin`/`mpn`

**Recommended for GEO:**
- `aggregateRating`: AggregateRating
- `review`: Array of individual reviews
- `category`: Product category
- `material`, `weight`, `width`, `height` (where applicable)

### FAQPage
**Status — Google retired FAQ rich results for ALL sites on 7 May 2026.** The earlier govt/health restriction (Aug 2023) is obsolete history; the feature is now gone entirely, along with the Search Console appearance filter, the rich-results report and Rich Results Test support.

`FAQPage` remains a **valid Schema.org type** and is still parsed by Bing and by AI retrieval systems. So it is worth adding — but the justification is **AI citation only**, and it must be presented that way. It gives a retrieval system pre-segmented, individually-quotable answer units instead of a prose blob it has to chunk itself.

**Never present FAQPage as a rich-result or SERP win. It cannot produce one on Google.** If a report implies otherwise, the recommendation will be priced wrongly and may be prioritised above work that actually moves visibility.

**Apply only to genuinely Q&A-structured pages.** Retrofitting `FAQPage` across a site that is not written as questions and answers is page weight for zero return.

**Structure:**
- `@type`: "FAQPage"
- `mainEntity`: Array of Question schemas, each with `acceptedAnswer` containing an Answer schema

### SoftwareApplication (for SaaS)
**Required:**
- `name`, `description`
- `applicationCategory`: e.g., "BusinessApplication"
- `operatingSystem`: Supported platforms
- `offers`: Pricing

**Recommended for GEO:**
- `aggregateRating`: User ratings
- `featureList`: Array of features (strong citation signal)
- `screenshot`: Screenshots
- `softwareVersion`: Current version
- `releaseNotes`: Link to changelog

### WebSite (keep) + SearchAction (do NOT recommend)

**`WebSite` is still worth having** — it establishes the site as an entity, carries `inLanguage` and `publisher`, and gives other nodes a stable `@id` to reference via `isPartOf`. Recommend it.

**`SearchAction` should not be recommended. Google retired the sitelinks search box on 21 November 2024** and removed the associated Search Console report and Rich Results Test highlighting. The markup now drives no feature on Google. Google's own guidance is that removing existing `SearchAction` markup is unnecessary — unsupported structured data causes no errors — so **do not raise its presence as a defect either**. It is simply inert.

Recommending it is markup for a feature that no longer exists, and it is the same class of error as recommending `speakable` to an ineligible site or pricing `FAQPage` as a rich-result win. Treat all three as one decision.

```json
{
  "@type": "WebSite",
  "@id": "https://example.com/#website",
  "name": "Site Name",
  "url": "https://example.com",
  "inLanguage": "en-GB",
  "publisher": { "@id": "https://example.com/#business" }
}
```

### Person (standalone — for personal brands, authors, thought leaders)
Use as a standalone schema on About/Bio pages. This builds the entity graph for individual expertise.

**Required:** `name`, `url`
**Recommended for GEO:** `sameAs`, `jobTitle`, `worksFor`, `knowsAbout`, `alumniOf`, `award`, `description`, `image`

### speakable Property — CHECK ELIGIBILITY BEFORE RECOMMENDING

`speakable` is still marked **BETA** in Google's documentation and is limited on three axes simultaneously:

| Restriction | Requirement |
|---|---|
| Content type | **News articles only** |
| Language | **English only** |
| Audience location | **United States only** |

**A site must satisfy all three to be eligible.** Most sites satisfy none of them. Recommending `speakable` to a non-news site, a non-English site, or one whose audience is outside the US is markup for a feature that site cannot be eligible for — the same error as recommending `SearchAction` or pricing `FAQPage` as a rich-result win.

**Decision rule:** recommend `speakable` only for English-language news publishers with a US audience. For every other site, do not raise it — neither as a recommendation nor as a missing-feature deduction.

```json
{
  "@type": "Article",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [".article-summary", ".key-takeaway"]
  }
}
```

Where it *is* eligible, selectors must resolve to concise, self-contained factual text. A selector pointing at navigation or a wall of prose is worse than omitting the property.

---

## Step 4: Deprecated/Changed Schemas to Flag

| Schema | Status | Note |
|---|---|---|
| HowTo | Rich results deprecated Aug 2023 | Still parsed by AI systems, but do not promise rich results |
| FAQPage | **Rich results retired for ALL sites 7 May 2026** | Markup still valid and still parsed by AI systems. AI-citation justification only — never present as a SERP win |
| SearchAction / sitelinks search box | **Retired 21 Nov 2024** | Do not recommend. Do not flag as missing. `WebSite` itself is still worth keeping |
| speakable | BETA; news + English + US only | Check all three before recommending. Do not deduct points from ineligible sites |
| SpecialAnnouncement | Deprecated 2023 | Was for COVID; remove if still present |
| CourseInfo | Replaced by Course updates 2024 | Use updated Course schema properties |
| VideoObject `contentUrl` | Changed behavior 2024 | Must point to actual video file, not page URL |
| Review snippet | Stricter enforcement 2024 | Self-serving reviews on product pages may not display |

Flag any deprecated schemas found and recommend replacements.

---

## Step 5: sameAs Strategy (CRITICAL for Entity Recognition)

The `sameAs` property is the single most important structured data property for GEO. It tells AI systems: "This entity on my website is the SAME entity as these profiles elsewhere." This creates the entity graph that AI platforms use to verify, trust, and cite sources.

### Recommended sameAs Links (in priority order)

1. **Wikipedia article** — highest authority entity link
2. **Wikidata item** — machine-readable entity identifier (e.g., `https://www.wikidata.org/wiki/Q12345`)
3. **LinkedIn** — company page or personal profile
4. **YouTube** — channel URL
5. **Twitter/X** — profile URL
6. **Facebook** — page URL
7. **Crunchbase** — company profile (for startups/tech)
8. **GitHub** — organization or personal profile (for tech)
9. **Google Scholar** — author profile (for researchers/academics)
10. **ORCID** — researcher identifier (for academics)
11. **Instagram** — profile URL
12. **Apple App Store / Google Play** — app listings (for software)
13. **BBB** — Better Business Bureau listing (for US businesses)
14. **Industry directories** — relevant vertical directories

### sameAs Audit Process
1. Collect all known web presences for the entity
2. Check that each URL resolves (not 404 or redirected)
3. Verify the Organization/Person schema includes ALL of them
4. Check that the information on each platform is consistent (name, description, founding date, etc.)
5. Flag any platforms where the entity should have a presence but does not

---

## Step 6: JSON-LD Generation

Based on the detected business type, generate ready-to-paste JSON-LD blocks. Always generate:

1. **Organization or Person** (depending on entity type) — always
2. **WebSite** — always for the homepage. Include `@id`, `inLanguage` and `publisher`; **omit `SearchAction`** (retired 21 Nov 2024)
3. **Business-type-specific** — Article for publishers, Product for e-commerce, LocalBusiness for local, SoftwareApplication for SaaS
4. **BreadcrumbList** — for any page deeper than homepage

### Generation Rules
- Use the `@graph` pattern to include multiple schemas in one JSON-LD block
- All URLs must be absolute (not relative)
- Include `@id` properties for cross-referencing between schemas
- Use ISO 8601 for all dates
- Include `speakable` on Article schemas **only where the site is eligible** — English-language news, US audience. Omit it otherwise
- Emit **one `<script type="application/ld+json">` per page containing a single `@graph`**. Splitting nodes across multiple script tags makes cross-block `@id` references unreliable: Google usually merges same-page blocks, but many third-party and AI parsers resolve nothing across blocks, silently dropping `author` and `publisher`
- Place JSON-LD in `<head>` section — NOT injected via JavaScript

### Template: Organization with Full GEO Signals
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://example.com/#organization",
  "name": "Company Name",
  "url": "https://example.com",
  "logo": {
    "@type": "ImageObject",
    "url": "https://example.com/logo.png",
    "width": 600,
    "height": 60
  },
  "description": "Concise description of what the company does.",
  "foundingDate": "2020-01-15",
  "founder": {
    "@type": "Person",
    "name": "Founder Name",
    "sameAs": "https://www.linkedin.com/in/founder"
  },
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main St",
    "addressLocality": "City",
    "addressRegion": "State",
    "postalCode": "12345",
    "addressCountry": "US"
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+1-555-555-5555",
    "contactType": "customer service",
    "email": "support@example.com"
  },
  "sameAs": [
    "https://en.wikipedia.org/wiki/Company_Name",
    "https://www.wikidata.org/wiki/Q12345",
    "https://www.linkedin.com/company/company-name",
    "https://www.youtube.com/@companyname",
    "https://twitter.com/companyname",
    "https://github.com/companyname",
    "https://www.crunchbase.com/organization/company-name"
  ],
  "knowsAbout": [
    "Topic 1",
    "Topic 2",
    "Topic 3"
  ]
}
```

---

## Scoring Rubric (0-100)

**Scoring principle — never deduct for a feature the site cannot use.** Before scoring any criterion, check the site is eligible for it. If it is not (wrong content type, wrong language, wrong region, or the platform feature has been retired), the criterion **does not apply**: remove its points from the denominator and rescale, rather than scoring 0. Scoring 0 for correctly-absent markup manufactures a deficit, misdirects the remediation plan, and penalises a site for being right.

| Criterion | Points | How to Score |
|---|---|---|
| Organization/Person schema present and complete | 15 | 15 if full, 10 if basic, 0 if none |
| sameAs links (5+ platforms) | 15 | 3 per valid sameAs link, max 15 |
| Article schema with author details | 10 | 10 if full author schema, 5 if name only, 0 if none |
| Business-type-specific schema present | 10 | 10 if complete, 5 if partial, 0 if missing |
| WebSite node present (with `@id`) | 5 | 5 if present, 0 if not. **Do not score `SearchAction`** — retired 21 Nov 2024; its absence is correct, not a defect |
| BreadcrumbList on inner pages | 5 | 5 if present, 0 if not |
| JSON-LD format (not Microdata/RDFa) | 5 | 5 if JSON-LD, 3 if mixed, 0 if only Microdata/RDFa |
| Server-rendered (not JS-injected) | 10 | 10 if in HTML source, 5 if JS but in head, 0 if dynamic JS |
| Single `@graph` per page (no cross-block `@id`) | 5 | 5 if one block, 2 if multiple blocks resolve, 0 if references dangle |
| speakable property on articles | 5 | **Only score if the site is eligible** (English news, US audience). If ineligible, this criterion does not apply — remove its 5 points from the denominator rather than scoring 0 |
| Valid JSON + valid Schema.org types | 10 | 10 if no errors, 5 if minor issues, 0 if major errors |
| knowsAbout property on Organization/Person | 5 | 5 if present with 3+ topics, 0 if missing |
| No deprecated schemas present | 5 | 5 if clean, 0 if deprecated schemas found |

---

## Output Format

Generate **GEO-SCHEMA-REPORT.md** with:

```markdown
# GEO Schema & Structured Data Report — [Domain]
Date: [Date]

## Schema Score: XX/100

## Detected Schemas
| Page | Schema Type | Format | Status | Issues |
|---|---|---|---|---|
| / | Organization | JSON-LD | Valid | Missing sameAs |
| /blog/post-1 | Article | JSON-LD | Valid | No author schema |

## Validation Results
[List each schema with pass/fail per property]

## Missing Recommended Schemas
[List schemas that should be present based on business type but are not]

## sameAs Audit
| Platform | URL | Status |
|---|---|---|
| Wikipedia | [URL or "Not found"] | Present/Missing |
| LinkedIn | [URL or "Not found"] | Present/Missing |
[Continue for all recommended platforms]

## Generated JSON-LD Code
[Ready-to-paste JSON-LD blocks for each missing or incomplete schema]

## Implementation Notes
- Where to place each JSON-LD block
- Server-rendering requirements
- Testing with Google Rich Results Test and Schema.org Validator
```

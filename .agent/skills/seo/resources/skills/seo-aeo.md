---
name: seo-aeo
description: >
  Answer Engine Optimization audit — optimizes for zero-click rich results:
  Featured Snippets, People Also Ask (PAA), Knowledge Panel, and Sitelinks
  Searchbox. Distinct from GEO (AI-generated summaries). Use when user says
  "featured snippet", "people also ask", "knowledge panel", "answer box",
  "zero-click", or "AEO".
---

# Answer Engine Optimization (AEO)

AEO targets **zero-click rich results** in both traditional search and AI-powered search interfaces. Unlike GEO (AI Overview / Perplexity passage citation), AEO targets specific SERP features that display answers directly on the results page.

## AEO vs GEO

| Target | Signal Selection | Optimization Focus |
|--------|-----------------|-------------------|
| **Featured Snippet** (AEO) | Best direct answer to exact query | 40-55 word answer immediately after matching H-tag |
| **People Also Ask** (AEO) | Question-intent pages, conversational H-tags | Question-phrased H2/H3, concise 30-50 word answer |
| **Knowledge Panel** (AEO) | Entity KG match (Wikipedia/Wikidata) | `sameAs`, Organization/Person schema, entity disambiguation |
| **Sitelinks Searchbox** (AEO) | Site authority + WebSite schema | `WebSite` + `SearchAction` schema |
| **AI Overview** (GEO) | Passage-level citability, brand authority | `llms.txt`, structured data, citation-ready prose |

## Audit Checklist

### 1. Featured Snippet Optimization

**Detection:**
- Check if the target URL currently owns any Featured Snippets (requires GSC or manual SERP check)
- Identify the primary keyword intent: informational (paragraph), list, or table snippet

**Optimization requirements:**

#### Paragraph Snippet (most common for informational queries)
- [ ] Direct answer in the **first 40-55 words** of the first paragraph after a relevant H2 or H3
- [ ] Answer starts with the keyword or a variant: "X is...", "X refers to...", "To do X..."
- [ ] No jargon in the first answer sentence — plain language
- [ ] Supporting context paragraph follows (2-4 sentences)

#### List Snippet (procedures, rankings, comparisons)
- [ ] Use `<ol>` (ordered) or `<ul>` (unordered) immediately after the H2/H3 question
- [ ] 5-9 list items — more than 9 triggers "more items" truncation
- [ ] Each item ≤ 12 words for clean display
- [ ] H2/H3 must be phrased as the actual question users search

#### Table Snippet (comparisons, pricing, specifications)
- [ ] Use `<table>` with `<th>` header row
- [ ] ≤4 columns (wider tables are truncated)
- [ ] First column is the primary entity (product, plan, country)

**`speakable` schema (voice + Google Assistant):**
```json
{
  "@type": "Article",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [".article-summary", "[itemprop='description']"]
  }
}
```

---

### 2. People Also Ask (PAA) Optimization

PAA questions are selected by Google based on semantic relatedness to the primary query. Owning multiple PAA entries significantly increases SERP real estate.

**Optimization requirements:**
- [ ] Identify the top 5-8 PAA questions for your primary keyword (check SERPs manually or via ahrefs/SemRush)
- [ ] Each PAA question should have its own H2 or H3 phrased **exactly as the question** users ask
- [ ] Directly below each question H-tag: a 30-50 word direct answer paragraph
- [ ] Avoid filler phrases ("Great question!", "In this article we will...") — Google penalizes these for PAA
- [ ] Add `FAQPage` schema **only if your site qualifies** (restricted to government/healthcare authority sites post-2023); for others, use `Article` with `speakable`

**Example HTML structure for PAA:**
```html
<h2>What is Qwen3-TTS voice cloning?</h2>
<p>Qwen3-TTS is an open-source text-to-speech model from Alibaba that enables
offline voice cloning from a 3-10 second audio sample. It runs entirely locally,
requiring no cloud API, making it suitable for OpSec-sensitive environments.</p>
```

---

### 3. Knowledge Panel Signals

Knowledge Panels are sourced from Google's Knowledge Graph. They appear for entities (people, organizations, products/brands).

**Entity presence checklist:**
- [ ] **Wikipedia article** exists for the entity (person, company, product) — highest signal
- [ ] **Wikidata QID** assigned — use `entity_checker.py` to check
- [ ] **`sameAs` properties** in Organization/Person schema point to Wikipedia, LinkedIn, Twitter/X, Crunchbase:
  ```json
  {
    "@type": "Organization",
    "name": "Example Corp",
    "sameAs": [
      "https://en.wikipedia.org/wiki/Example_Corp",
      "https://www.linkedin.com/company/example-corp",
      "https://twitter.com/examplecorp"
    ]
  }
  ```
- [ ] **Google Business Profile** claimed and consistent name/address/phone (NAP)
- [ ] **Social profiles** publicly linked from the website
- [ ] **Logo** via `Organization` schema with `logo` property pointing to a stable URL

**Common mistakes:**
- Inconsistent entity name across platforms (e.g., "Example Corp" vs "Example Corporation")
- No Wikipedia article → no Knowledge Panel (organic mentions in 3rd-party authoritative sources help)
- `sameAs` pointing to broken or redirected URLs

---

### 4. Sitelinks Searchbox

Appears when users search your brand directly. Requires:
- High brand search volume (signal: GSC showing branded queries)
- `WebSite` schema with `SearchAction` pointing to your internal search URL

**Required schema:**
```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "url": "https://example.com/",
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://example.com/search?q={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
}
```

- [ ] Schema added to **homepage only**
- [ ] `urlTemplate` returns a valid results page (not 404)
- [ ] Internal site search is functional and indexes your content

---

## Output Format

### AEO Audit Report

```markdown
## AEO Audit — [URL]

### Featured Snippet Readiness
- Current ownership: [Yes/No/Unknown]
- Answer block present: [Yes/No] — [Location if found]
- Answer word count: [N] words (target: 40-55)
- Confidence: [Confirmed/Likely/Hypothesis]

### PAA Coverage
- Questions identified: [List]
- Questions with matching H-tags + direct answers: [N/M]
- Gaps (no coverage): [List]

### Knowledge Panel Signals
- Wikipedia: [Present/Absent]
- Wikidata QID: [Present/Absent]
- sameAs count: [N]
- Missing sameAs: [List]

### Sitelinks Searchbox
- WebSite schema: [Present/Absent]
- SearchAction: [Valid/Invalid/Missing]

### Priority Fixes
[Ordered by impact]
```

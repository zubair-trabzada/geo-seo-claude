# Scoring Methodology

The GEO Score is a single composite number from 0 to 100 that summarises how well a website is optimised for discovery, citation, and recommendation by AI systems such as ChatGPT, Perplexity, Claude, and Google AI Overviews. It is computed as a weighted average of six category sub-scores, each evaluated independently by a specialised subagent. A high score signals strong readiness for generative-engine visibility; a low score points to concrete gaps with an accompanying prioritised action plan.

---

## Weight table

| Category | Weight |
|---|---|
| AI Citability & Visibility | 25% |
| Brand Authority Signals | 20% |
| Content Quality & E-E-A-T | 20% |
| Technical Foundations | 15% |
| Structured Data | 10% |
| Platform Optimization | 10% |

---

## How the composite score is computed

Each subagent returns a sub-score on a 0–100 scale. The orchestrator in [`skills/geo-audit/SKILL.md`](../skills/geo-audit/SKILL.md) multiplies each sub-score by its weight and sums the results.

**Formula (from `skills/geo-audit/SKILL.md`):**

```
GEO_Score = (Citability   * 0.25)
          + (Brand        * 0.20)
          + (EEAT         * 0.20)
          + (Technical    * 0.15)
          + (Schema       * 0.10)
          + (Platform     * 0.10)
```

**Pseudo-code:**

```python
weights = {
    "citability": 0.25,
    "brand":      0.20,
    "eeat":       0.20,
    "technical":  0.15,
    "schema":     0.10,
    "platform":   0.10,
}

geo_score = sum(sub_scores[k] * w for k, w in weights.items())
# geo_score is in [0, 100]
```

**Score interpretation (from `skills/geo-audit/SKILL.md`):**

| Range | Rating | Meaning |
|---|---|---|
| 90–100 | Excellent | Highly likely to be cited by AI |
| 75–89 | Good | Strong foundation with room for improvement |
| 60–74 | Fair | Moderate presence; significant opportunities |
| 40–59 | Poor | Weak signals; AI systems may struggle to cite |
| 0–39 | Critical | Largely invisible to AI systems |

---

## AI Citability & Visibility (25%)

**Implemented by:** [`agents/geo-ai-visibility.md`](../agents/geo-ai-visibility.md) and [`scripts/citability_scorer.py`](../scripts/citability_scorer.py)

### What the scorer looks at

The citability sub-score is itself a weighted composite of four components (weights from `agents/geo-ai-visibility.md`):

| Component | Weight |
|---|---|
| Citability Score | 35% |
| Brand Mention Score | 30% |
| Crawler Access Score | 25% |
| llms.txt Score | 10% |

**Citability scoring** (`scripts/citability_scorer.py`) analyses every substantive content block on the page — sections bounded by headings — and scores each one across five dimensions:

| Dimension | Max points | Key signals |
|---|---|---|
| Answer Block Quality | 30 | Definition patterns ("X is a…", "X refers to…"), answer appearing in the first 60 words, question-based heading, short clear sentences (5–25 words), attributed claims ("research shows…") |
| Self-Containment | 25 | Word count in the 134–167 word optimal range (10 pts), 100–200 word range (7 pts), 80–250 word range (4 pts); pronoun density below 2% (8 pts); 3+ proper nouns (7 pts) |
| Structural Readability | 20 | Average sentence length 10–20 words (8 pts); list-like transition words (4 pts); numbered items or step references (4 pts); paragraph breaks (4 pts) |
| Statistical Density | 15 | Percentages (3 pts each, max 6); dollar amounts (3 pts each, max 5); numbers with unit context (2 pts each, max 4); year references (2 pts); named sources (2 pts) |
| Uniqueness Signals | 10 | Original-research language ("our study found…") (5 pts); case study or real-world example references (3 pts); specific tool/product mentions (2 pts) |

The passage score is the sum of all five dimensions (maximum 100). The page-level citability score is the average of the top five scoring blocks, or all blocks when fewer than five exist.

**Crawler Access Score** (`agents/geo-ai-visibility.md`) starts at 100 and deducts:
- 15 points per critical crawler blocked (GPTBot, ClaudeBot, PerplexityBot, OAI-SearchBot, GoogleBot)
- 5 points per secondary crawler blocked
- 10 points if no sitemap is referenced in robots.txt
- Floor at 0

**llms.txt Score** (`agents/geo-ai-visibility.md` and `scripts/llmstxt_generator.py`):
- 0 — absent
- 30 — present but malformed
- 50 — present, valid format, minimal content
- 70 — present, valid, covers primary content areas
- 90–100 — comprehensive, with `/llms-full.txt` also available

### What good vs bad looks like

A good AI Citability score (70+) means the page has multiple passages that are self-contained, fact-dense, and directly answer questions; all major AI crawlers are allowed in robots.txt; and an llms.txt file is present and well-structured. A poor score (below 40) typically indicates thin or highly context-dependent prose, blocked AI crawlers, and no llms.txt.

---

## Brand Authority Signals (20%)

**Implemented by:** [`agents/geo-ai-visibility.md`](../agents/geo-ai-visibility.md) and [`scripts/brand_scanner.py`](../scripts/brand_scanner.py)

### What the scorer looks at

Brand authority is assessed by checking the brand's presence on platforms that AI models draw on heavily when forming entity knowledge. The Brand Mention Score (used as input to the AI Visibility composite above) is built from:

| Platform | Points available | Method |
|---|---|---|
| Wikipedia | 30 | Wikipedia API search; Wikidata entity lookup (`scripts/brand_scanner.py`) |
| Industry / niche sources | 25 | Review platforms (G2, Trustpilot, Capterra), press mentions, authoritative industry sites |
| Reddit | 20 | Presence, recency, and sentiment of brand discussions |
| YouTube | 15 | Official channel existence and third-party video coverage |
| LinkedIn | 10 | Company page presence and activity |

The correlation values cited in `scripts/brand_scanner.py` come from an Ahrefs December 2025 study of 75,000 brands: YouTube shows the strongest correlation (0.737) with AI citations; domain rating / backlinks show a weak correlation (0.266).

### What good vs bad looks like

A strong brand authority score requires an active Wikipedia presence (the highest-weight signal), community-level discussion on Reddit, and a YouTube presence with educational or review content. A brand with no Wikipedia page, no Reddit discussion, and no YouTube presence will score near 0 on this sub-score regardless of how well-known it is in traditional search.

---

## Content Quality & E-E-A-T (20%)

**Implemented by:** [`agents/geo-content.md`](../agents/geo-content.md)

### What the scorer looks at

The content agent evaluates the page against Google's E-E-A-T framework. Each of the four dimensions is scored 0–25 and then normalised to 0–15 for weighting within the content score:

| Dimension | Max (raw) | Key signals checked |
|---|---|---|
| Experience | 25 | Original research or data, case studies with measurable outcomes, first-hand accounts, before/after comparisons, specific names and figures |
| Expertise | 25 | Named author with credentials, linked author page with biography, technical depth, methodology transparency, Person schema |
| Authoritativeness | 25 | About page quality, external citations, industry recognition, media mentions, sameAs schema links |
| Trustworthiness | 25 | HTTPS, visible contact information, privacy policy, editorial standards, transparent sourcing, publication and update dates |

Beyond E-E-A-T, the full content score (0–100) also incorporates:

| Component | Weight | Signals |
|---|---|---|
| E-E-A-T (combined, normalised) | 60% | Four dimensions above |
| Content Metrics | 15% | Word count classification (thin < 300 words; deep-dive 3000+ words), approximate Flesch readability, paragraph length, heading hierarchy |
| AI Content Assessment | 10% | Absence of generic AI-pattern phrases, presence of authorial voice, original data |
| Topical Authority | 10% | Content breadth (related pages), internal linking depth, hub-and-cluster structure |
| Content Freshness | 5% | Publication and modification dates visible, recency for time-sensitive topics |

### What good vs bad looks like

A score of 70+ requires a clearly identified author with verifiable credentials, original data or case studies, transparent sourcing, HTTPS, and content that goes beyond surface-level coverage of the topic. A score below 30 typically means no author attribution, no external sources, no HTTPS, and content that could have been written by anyone with no subject-matter exposure.

---

## Technical Foundations (15%)

**Implemented by:** [`agents/geo-technical.md`](../agents/geo-technical.md)

### What the scorer looks at

The technical agent computes a score from nine weighted components:

| Component | Weight |
|---|---|
| Server-Side Rendering / JS dependency | 25% |
| Meta tags & indexability | 15% |
| Crawlability (robots.txt, sitemap) | 15% |
| Security headers | 10% |
| Core Web Vitals risk | 10% |
| Mobile optimization | 10% |
| URL structure | 5% |
| Response headers & status | 5% |
| Additional checks | 5% |

Server-side rendering carries the highest weight because AI crawlers (GPTBot, ClaudeBot, PerplexityBot) generally do not execute JavaScript. A page that requires JS to render its main content is effectively invisible to AI crawlers regardless of how well the content itself is written.

Security header deductions (from `agents/geo-technical.md`):
- No HTTPS: -30 points
- No HSTS: -10 points
- No CSP: -10 points
- No X-Frame-Options: -5 points
- No X-Content-Type-Options: -5 points
- No Referrer-Policy: -5 points
- No Permissions-Policy: -3 points

Core Web Vitals (LCP, INP, CLS) are assessed as Low / Medium / High risk from static HTML analysis. The agent notes explicitly that actual measurements require field data (PageSpeed Insights or CrUX).

### What good vs bad looks like

A high technical score requires full server-side rendering, a well-formed robots.txt that allows AI crawlers, a referenced XML sitemap, HTTPS with HSTS, and clean meta tags. A critical finding is any client-side-only SPA where the HTML body is empty without JavaScript execution — in that state, no amount of content optimisation helps AI discoverability.

---

## Structured Data (10%)

**Implemented by:** [`agents/geo-schema.md`](../agents/geo-schema.md)

### What the scorer looks at

The schema agent detects JSON-LD, Microdata, and RDFa structured data in the page source and scores completeness across ten components:

| Component | Max points | Criteria |
|---|---|---|
| Organization / LocalBusiness | 20 | Present (10 pts); sameAs linking to 3+ platforms (20 pts) |
| Article / content schema | 15 | Present (8 pts); author as Person object (12 pts); dateModified present (15 pts) |
| Person schema for author | 15 | Present (8 pts); sameAs present (12 pts); jobTitle and knowsAbout present (15 pts) |
| sameAs completeness | 15 | 1–2 platforms (5 pts); 3–4 platforms (10 pts); 5+ platforms including Wikipedia (15 pts) |
| speakable property | 10 | Present and targeting content sections (10 pts) |
| BreadcrumbList | 5 | Present and valid (5 pts) |
| WebSite + SearchAction | 5 | Present and valid (5 pts) |
| No deprecated schemas | 5 | No HowTo (removed Sep 2023) or SpecialAnnouncement schemas present |
| JSON-LD format | 5 | All schemas in JSON-LD rather than Microdata or RDFa |
| Validation (no errors) | 5 | All schemas pass syntax and property validation |

The agent also flags schemas that are injected by JavaScript rather than present in the initial HTML response, because AI crawlers will not execute JavaScript and will miss those schemas entirely.

Deprecated and restricted statuses checked (from `agents/geo-schema.md`):
- HowTo: removed from Google rich results September 2023
- FAQPage: restricted to government and health authority sites since August 2023
- SpecialAnnouncement: deprecated

### What good vs bad looks like

A high schema score requires an Organization schema with sameAs links to at least five platforms including Wikipedia, properly nested Person schemas for all content authors, Article schema with dateModified, and all schemas delivered as server-rendered JSON-LD. A score near zero means no structured data at all, which removes any explicit entity-linking signal for AI models.

---

## Platform Optimization (10%)

**Implemented by:** [`agents/geo-platform-analysis.md`](../agents/geo-platform-analysis.md)

### What the scorer looks at

The platform agent scores readiness for five AI search platforms independently and aggregates them. Each platform has its own sub-scoring breakdown:

**Google AI Overviews:** Content structure (40 pts) — question-based headings, direct answer paragraphs, comparison tables; source authority signals (30 pts); technical signals (30 pts).

**ChatGPT web search:** Entity recognition (35 pts) — Wikipedia and Wikidata presence, sameAs schema; content preferences (40 pts) — factual, citable statements with attribution; crawler access (25 pts) — OAI-SearchBot and ChatGPT-User allowed in robots.txt.

**Perplexity AI:** Community validation (Reddit, Quora, Stack Overflow) and source directness scored separately.

**Google Gemini and Bing Copilot:** Each platform evaluated against its documented sourcing and ranking signals.

The README notes that only 11% of domains are cited by both ChatGPT and Google AI Overviews for the same query, which motivates treating platform readiness as a distinct scoring dimension rather than folding it into technical or content categories.

### What good vs bad looks like

A strong platform score requires passing the crawler-access and entity-recognition checks that appear in the other categories, plus platform-specific structural patterns: question-answering headings and direct-answer paragraphs for Google AIO, Wikipedia and Wikidata presence for ChatGPT, and community-platform presence for Perplexity. Because this category overlaps with several other categories, a site that scores well on AI Citability and Brand Authority will often score reasonably here too.

---

## Caveats

**Deterministic vs LLM-judged scoring.** The citability scorer (`scripts/citability_scorer.py`) and the llms.txt validator (`scripts/llmstxt_generator.py`) are fully deterministic: given the same HTML, they return the same numerical result every time. The Brand Authority, Content E-E-A-T, Technical, Schema, and Platform scores are produced by LLM subagents following documented rubrics; they are guided evaluations rather than reproducible computations. Two runs on the same URL may produce small differences in LLM-judged categories.

**Weights are opinionated.** The 25/20/20/15/10/10 weight distribution reflects the judgement of the tool's authors about the relative importance of each category for AI citation likelihood at the time of writing. These weights are not derived from a controlled study and are subject to change as AI search platforms evolve.

**Diagnostic, not a guarantee.** The GEO Score is a diagnostic instrument. A high score improves the structural conditions for AI citation but does not guarantee that any particular AI system will cite or recommend the site. AI model behaviour depends on many factors outside the scope of this tool, including model training data, query phrasing, and competitor content.

**Schema validation is structural, not semantic.** The schema agent checks that JSON-LD is syntactically valid, uses recognised Schema.org types and properties, and includes required fields. It does not verify that the values are accurate or that the described entity matches the actual organisation or person. A schema block that passes validation may still contain incorrect information.

**llms.txt is an emerging standard.** The llms.txt specification referenced by `scripts/llmstxt_generator.py` and `agents/geo-ai-visibility.md` is not yet universally adopted by AI crawlers. Its presence or absence does not guarantee any specific crawler behaviour at this time.

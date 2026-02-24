---
name: geo-competitors
description: >
  GEO competitor analysis and benchmarking. Compares a target website against
  up to 5 competitors across 8 AI-visibility dimensions: citability, brand
  authority, content depth, crawler access, schema coverage, llms.txt, technical
  GEO, and content freshness. Produces a weighted comparison matrix, gap analysis,
  opportunity map, and prioritized action plan. Use when user says "competitors",
  "compare", "benchmark", "vs", "competitive analysis", or provides multiple URLs.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
  - Write
---

# GEO Competitor Analysis Skill

> **Core Insight:** Competitive GEO analysis differs fundamentally from traditional SEO
> competitor analysis. In traditional SEO, you compare backlink profiles, keyword rankings,
> and domain authority. In GEO, the signals that matter are brand mentions (3x stronger than
> backlinks — Ahrefs Dec 2025, 75K brands), AI citability of content passages, crawler access
> policies, and structured data completeness. A site with DR 90 can be invisible to AI if it
> blocks crawlers and writes uncitable content. A DR 30 site can dominate AI citations with
> well-structured, answer-first content. (Georgia Tech 2024; Gartner predicts 50% search
> traffic drop by 2028.)

---

## 8 Comparison Dimensions

| # | Dimension | Weight | What It Measures |
|---|-----------|--------|------------------|
| 1 | **AI Citability** | 25% | Average citability score across top pages — answer blocks, self-containment, statistics, structure |
| 2 | **Brand Authority** | 20% | Presence on AI-cited platforms: YouTube (~0.737 correlation), Reddit, Wikipedia, LinkedIn |
| 3 | **Content Depth** | 15% | Average word count per page, percentage of pages with 1,000+ words |
| 4 | **Crawler Access** | 10% | Number of AI crawlers allowed out of 14 checked (GPTBot, ClaudeBot, PerplexityBot, etc.) |
| 5 | **Schema Coverage** | 10% | Count of distinct JSON-LD schema types + completeness of implementation |
| 6 | **llms.txt** | 5% | Presence and quality of /llms.txt and /llms-full.txt files |
| 7 | **Technical GEO** | 10% | HTTPS, server-side rendering, canonical URLs, hreflang, security headers |
| 8 | **Content Freshness** | 5% | Most recent content publication date across scanned pages |

---

## Scoring Rubric (0-100)

Each dimension is scored on a 0-100 scale:

| Score Range | Tier | Meaning |
|-------------|------|---------|
| **90-100** | Excellent | Best-in-class for this dimension |
| **70-89** | Good | Solid implementation, minor improvements possible |
| **50-69** | Fair | Functional but significant gaps exist |
| **30-49** | Poor | Major deficiencies, likely hurting AI visibility |
| **0-29** | Critical | Missing or fundamentally broken |

### Weighted GEO Score

The overall **GEO Competitor Score** is the weighted sum across all 8 dimensions:

```
GEO Score = (Citability × 0.25) + (Brand × 0.20) + (Content Depth × 0.15) +
            (Crawler Access × 0.10) + (Schema × 0.10) + (llms.txt × 0.05) +
            (Technical × 0.10) + (Freshness × 0.05)
```

---

## Competitive Position Labels

Position is determined by comparing the target's score against the competitor average for each dimension:

| Position | Difference from Avg | Meaning |
|----------|-------------------|---------|
| **Leading** | > +15 points | Target outperforms competitors |
| **Parity** | ±15 points | Roughly equal to competitors |
| **Trailing** | -15 to -30 points | Behind competitors — action needed |
| **Critical Gap** | < -30 points | Severely behind — urgent action required |

---

## Analysis Procedure

### Step 1: Validate Inputs
- Confirm target URL is accessible
- Confirm 1-5 competitor URLs are provided
- Normalize URLs (add https:// if missing, strip trailing slashes)

### Step 2: Lightweight Scan (Each Site)
For each site (target + competitors), perform a lightweight scan:
1. Fetch homepage (HTML, meta tags, structured data, headers)
2. Fetch `/robots.txt` — check AI crawler access
3. Fetch `/llms.txt` and `/llms-full.txt`
4. Discover pages from sitemap or internal links (max 5 pages per site)
5. Fetch and analyze up to 4 additional pages
6. Score each page's content for AI citability
7. Check brand signals (YouTube, Reddit, Wikipedia, LinkedIn)

**Use the Python script when available:**
```bash
python3 ~/.claude/skills/geo/scripts/competitor_analyzer.py <target> <comp1> [comp2] ...
```

**Manual fallback:** If the script is unavailable, perform each step using WebFetch and score manually using the rubric above.

### Step 3: Score All Dimensions
Apply the scoring rubric to produce a 0-100 score for each of the 8 dimensions for every site.

### Step 4: Compare and Rank
- Build comparison matrix (target vs each competitor per dimension)
- Calculate weighted GEO score for each site
- Rank all sites by weighted total
- Determine competitive position per dimension

### Step 5: Gap Analysis
Identify dimensions where the target trails competitors:
- Calculate difference from competitor average and best-in-class
- Classify each gap: Leading / Parity / Trailing / Critical Gap
- Weight gaps by dimension importance

### Step 6: Action Plan
Generate a prioritized action plan:
- **Critical** gaps first (position = Critical Gap)
- **High** priority next (difference > 15 from average)
- **Medium** priority last (difference ≤ 15)
- Each action includes: dimension, current score, target score, specific recommendations

---

## Output Format

Generate a file named `GEO-COMPETITOR-ANALYSIS.md` with this structure:

```markdown
# GEO Competitor Analysis

**Target:** [target URL]
**Competitors:** [list]
**Analysis Date:** [date]
**Overall Rank:** [X of Y]

---

## Executive Summary

**[Target domain]** scores **[X]/100** on the weighted GEO scale, ranking **#[N]** out of
[total] sites analyzed. [1-2 sentence summary of key finding].

### Competitive Position Overview
| Position | Count | Dimensions |
|----------|-------|------------|
| Leading | [n] | [list] |
| Parity | [n] | [list] |
| Trailing | [n] | [list] |
| Critical Gap | [n] | [list] |

---

## Comparison Matrix

| Dimension (Weight) | [Target] | [Comp 1] | [Comp 2] | ... | Position |
|---------------------|----------|----------|----------|-----|----------|
| AI Citability (25%) | [score] | [score] | [score] | ... | [position] |
| Brand Authority (20%) | [score] | [score] | [score] | ... | [position] |
| Content Depth (15%) | [score] | [score] | [score] | ... | [position] |
| Crawler Access (10%) | [score] | [score] | [score] | ... | [position] |
| Schema Coverage (10%) | [score] | [score] | [score] | ... | [position] |
| llms.txt (5%) | [score] | [score] | [score] | ... | [position] |
| Technical GEO (10%) | [score] | [score] | [score] | ... | [position] |
| Content Freshness (5%) | [score] | [score] | [score] | ... | [position] |
| **Weighted Total** | **[X]** | **[X]** | **[X]** | ... | **#[rank]** |

---

## Gap Analysis

### Critical Gaps
[For each dimension where position = Critical Gap]
- **[Dimension]:** Target scores [X] vs competitor avg [Y] (gap: [diff])
  - Why it matters: [explanation]
  - Impact: [weighted impact on overall score]

### Trailing Dimensions
[For each dimension where position = Trailing]
- **[Dimension]:** [same format]

---

## Opportunity Map

### Where You Lead
[Dimensions where target outperforms — leverage these strengths]

### Quick Wins
[Gaps that can be closed with minimal effort]

### Strategic Investments
[Gaps that require significant effort but have high impact]

---

## Action Plan

### Priority 1: Critical Fixes
| Action | Dimension | Current | Target | Impact |
|--------|-----------|---------|--------|--------|
| [specific action] | [dim] | [score] | [score] | [High/Critical] |

### Priority 2: High-Impact Improvements
[same table format]

### Priority 3: Medium-Term Optimizations
[same table format]

---

## Methodology

- **Pages scanned per site:** up to 5
- **Scoring:** 0-100 per dimension, weighted total
- **Data sources:** robots.txt, llms.txt, HTML analysis, schema detection, brand signals
- **Limitations:** Lightweight scan (not a full crawl), brand signals are approximate

*Generated by GEO-SEO Claude — [date]*
```

---

## Quality Gates

- **Max competitors:** 5 per analysis
- **Max pages per site:** 5 (focus on homepage + key pages)
- **Timeout:** 30 seconds per page fetch
- **Rate limiting:** 1-second delay between requests to the same domain
- **Robots.txt:** Always respect — never crawl blocked paths
- **Total runtime:** Expect 2-5 minutes for a full competitive analysis

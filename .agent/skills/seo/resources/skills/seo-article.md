---
name: seo-article
description: >
  LLM-first article and blog post SEO analysis with keyword extraction,
  content-gap identification, title/meta rewrite suggestions, and paragraph-level
  improvement proposals. Use when user says "article SEO", "optimize this blog
  post", "rewrite meta/title for this article", or "content optimization for a
  post".
---

# SEO Sub-Skill: Article Analysis

**Trigger**: `seo article <url>`

This sub-skill focuses on deep keyword research and content analysis for a specific article or blog post, leveraging LLM intelligence for natural language optimization rather than rigid rules.

Apply `resources/references/llm-audit-rubric.md` for evidence standards, confidence labels, severity mapping, and report structure.

## Process

### 1. Data Extraction
Run the article extraction script to fetch the page, parse the content structure (title, meta, headings, paragraphs, images), and perform initial keyword extraction (TF-IDF) alongside LSI keyword discovery (via Google Autocomplete).

```bash
python3 <SKILL_DIR>/scripts/article_seo.py <url> --keyword "<optional_target_keyword>" --json
```

### 2. LLM-Driven Analysis
Feed the JSON output from the extractor into your context.

Act as an expert SEO Editor and analyze the extracted data to provide:
1. **Title Tag & Meta Description Optimization**: Suggest high-CTR, keyword-optimized replacements if the current ones are missing or suboptimal.
2. **Context-Aware Content Enrichment**: Identify specific paragraphs where LSI (Latent Semantic Indexing) keywords can be injected naturally to build topical depth—always avoiding keyword stuffing. Provide the exact "Current Paragraph" and the "Suggested Replacement".
3. **Image SEO**: Suggest descriptive, keyword-aware alt text for any images missing the `alt` attribute.

### 3. Reporting
Format your generated SEO recommendations clearly using Markdown, ensuring the user receives actionable, copy-pasteable "before and after" examples.

---
name: seo-plan
description: >
  Strategic SEO planning for new or existing websites. Industry-specific
  templates, competitive analysis, content strategy, and implementation
  roadmap. Use when user says "SEO plan", "SEO strategy", "content strategy",
  "site architecture", or "SEO roadmap".
---

# Strategic SEO Planning

## Process

### 1. Discovery
- Business type, target audience, competitors, goals
- Current site assessment (if exists)
- Budget and timeline constraints
- Key performance indicators (KPIs)

### 2. Competitive Analysis
- Identify top 5 competitors
- Analyze their content strategy, schema usage, technical setup
- Identify keyword gaps and content opportunities
- Assess their E-E-A-T signals
- Estimate their domain authority

### 3. Architecture Design
- Load industry template from `resources/templates/`
- Design URL hierarchy and content pillars
- Plan internal linking strategy
- Sitemap structure with quality gates applied
- Information architecture for user journeys

### 4. Content Strategy
- Content gaps vs competitors — use `scripts/competitor_gap.py` for data-driven analysis
- Page types and estimated counts
- Blog/resource topics and publishing cadence
- E-E-A-T building plan (author bios, credentials, experience signals)
- Content calendar with priorities

### 4.5 Topical Authority Cluster Planning

**Why:** Google's Helpful Content system rewards sites demonstrating comprehensive topical expertise. A single page on "red team ops" ranks worse than a hub of 8-15 interlinked articles covering the topic from multiple angles.

#### Hub-and-Spoke Model

```
                    [Pillar Page]
                   /      |       \
          [Cluster 1] [Cluster 2] [Cluster 3]
          /    \        |    \        |    \
       [Sub] [Sub]   [Sub] [Sub]  [Sub] [Sub]
```

#### Pillar Page Requirements
- **Word count**: 3,000-5,000 words (comprehensive overview)
- **Structure**: Covers all major subtopics at surface level, links to each cluster article for depth
- **Target keyword**: Head term (e.g., "cobalt strike beacon")
- **Internal links**: Bidirectional links to/from every cluster article
- **Schema**: Add `Article` or `WebPage` schema with `about` and `mentions` properties

#### Cluster Article Requirements
- **Word count**: 1,500-3,000 words (deep dive on one aspect)
- **Target keyword**: Long-tail variant (e.g., "cobalt strike beacon sleep mask")
- **Internal links**: Must link back to pillar page + 2-3 sibling cluster articles
- **Freshness**: Update cluster articles when new information becomes available

#### Planning Process
1. **Identify 3-5 pillar topics** from your core competencies or target keywords
2. **Generate 8-15 cluster topics** per pillar using:
   - Google Autocomplete / People Also Ask
   - `scripts/competitor_gap.py` for competitor-covered subtopics
   - `scripts/article_seo.py --json` for related keyword extraction
3. **Map content to URLs** following flat architecture: `/pillar/cluster-article`
4. **Set internal link rules**: every cluster → pillar (required), cluster ↔ cluster (2-3 siblings)
5. **Track coverage**: maintain a topic-cluster spreadsheet with status and publish dates

#### Industry Cluster Templates

| Industry | Example Pillar | Cluster Topics (sample) |
|----------|---------------|------------------------|
| Cybersecurity | Penetration Testing | OSINT, Web App Testing, Network Pentesting, Reporting, Tools, Methodology, Compliance |
| SaaS | Product Documentation | Getting Started, API Reference, Integrations, Troubleshooting, Best Practices, Migration |
| E-commerce | Product Category | Buying Guide, Comparison, Care Guide, Reviews, FAQ, Accessories |
| Local Service | Service Area | City-specific pages, Service FAQ, Pricing, Before/After, Testimonials |

### 5. Technical Foundation
- Hosting and performance requirements
- Schema markup plan per page type
- Core Web Vitals baseline targets
- AI search readiness requirements
- Mobile-first considerations

### 6. Implementation Roadmap (4 phases)

#### Phase 1 — Foundation (weeks 1-4)
- Technical setup and infrastructure
- Core pages (home, about, contact, main services)
- Essential schema implementation
- Analytics and tracking setup

#### Phase 2 — Expansion (weeks 5-12)
- Content creation for primary pages
- Blog launch with initial posts
- Internal linking structure
- Local SEO setup (if applicable)

#### Phase 3 — Scale (weeks 13-24)
- Advanced content development
- Link building and outreach
- GEO optimization
- Performance optimization

#### Phase 4 — Authority (months 7-12)
- Thought leadership content
- PR and media mentions
- Advanced schema implementation
- Continuous optimization

## Industry Templates

Load from `resources/templates/`:
- `saas.md` — SaaS/software companies
- `local-service.md` — Local service businesses
- `ecommerce.md` — E-commerce stores
- `publisher.md` — Content publishers/media
- `agency.md` — Agencies and consultancies
- `generic.md` — General business template

## Output

### Deliverables
- `SEO-STRATEGY.md` — Complete strategic plan
- `COMPETITOR-ANALYSIS.md` — Competitive insights
- `CONTENT-CALENDAR.md` — Content roadmap
- `IMPLEMENTATION-ROADMAP.md` — Phased action plan
- `SITE-STRUCTURE.md` — URL hierarchy and architecture
- `TOPIC-CLUSTERS.md` — Pillar/cluster mapping with internal link plan

### KPI Targets
| Metric | Baseline | 3 Month | 6 Month | 12 Month |
|--------|----------|---------|---------|----------|
| Organic Traffic | ... | ... | ... | ... |
| Keyword Rankings | ... | ... | ... | ... |
| Domain Authority | ... | ... | ... | ... |
| Indexed Pages | ... | ... | ... | ... |
| Core Web Vitals | ... | ... | ... | ... |
| Topical Coverage % | ... | ... | ... | ... |

### Success Criteria
- Clear, measurable goals per phase
- Resource requirements defined
- Dependencies identified
- Risk mitigation strategies


<!-- Updated: 2026-03-02 -->
# Blog Post SEO Strategy Template

## Content Structure & Best Practices

### Essential Elements
- **Title Tag**: 50-60 characters, front-load main keyword, include numbers/brackets (e.g., "[2026 Guide]")
- **Meta Description**: 140-160 characters, natural language, clear value proposition
- **H1 Heading**: Only ONE per page, closely matching title tag
- **Introduction**: Hook the reader, state the problem, explain what they will learn (include primary keyword in first 100 words)
- **Body**: Use H2s for main sections, H3s for subsections
- **Conclusion**: Summarize key points, clear Call To Action (CTA)

### Minimum Requirements
- **Word Count**: 1,200+ words (longer for competitive keywords)
- **Paragraph Length**: 2-4 sentences max for scanability
- **Images**: At least 1 hero image + 1 image per 400 words
- **Image Alt Text**: Descriptive, naturally include keywords where relevant

## Internal & External Linking

- **Internal Links**: 3-5 links to other relevant content on your site (use descriptive anchor text)
- **External Links**: 2-3 links to high-authority, non-competing external sources (Wikipedia, research studies, official documentation)

## Keyword Optimization Strategy

1. **Primary Keyword**:
   - URL slug
   - Title tag
   - H1 heading
   - First 100 words
   - 1-2 times in H2s
   - Natural distribution in body (1-2% density)

2. **LSI / Secondary Keywords**:
   - Include in H2/H3 subheadings
   - Sprinkle naturally throughout content
   - Use in image alt text

## E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness)

- Include Author Name, Bio, and Photo
- Link to author's social profiles/portfolio (sameAs)
- Date published and Date modified clearly visible
- Cite sources and link to data

## Required Schema Markup

Use `BlogPosting` or `Article` schema.

```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://example.com/blog/your-post-url"
  },
  "headline": "Your Post Headline",
  "description": "Your meta description here.",
  "image": "https://example.com/featured-image.jpg",
  "author": {
    "@type": "Person",
    "name": "Author Name",
    "url": "https://example.com/author-bio"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Your Company",
    "logo": {
      "@type": "ImageObject",
      "url": "https://example.com/logo.png"
    }
  },
  "datePublished": "2026-03-02T08:00:00+08:00",
  "dateModified": "2026-03-02T08:00:00+08:00"
}
```

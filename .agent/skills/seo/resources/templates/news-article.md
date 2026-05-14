<!-- Updated: 2026-03-02 -->
# News Article SEO Strategy Template

## Content Structure & Best Practices

### Essential Elements
- **Headline**: Needs to be highly engaging and click-worthy. Focus on timeliness and relevance. Include primary keyword.
- **Standfirst / Summary**: A short summary paragraph just below the headline.
- **Lede**: The first paragraph must contain the most critical information (Who, what, when, where, why).
- **Body**: Inverted pyramid structure (most important info first, background later).
- **Date/Time**: Extremely visible timestamps for when the article was published and last updated.

### Google News Specifics
- **Timeliness**: Content must be fresh.
- **Transparency**: Clear author bylines, contact info, and publication details.
- **Originality**: Focus on original reporting, not syndication.
- **No Deception**: Avoid clickbait or misleading headlines.

## Internal & External Linking

- Link to previous relevant coverage on your own site.
- Outbound links should cite original sources, statements, or relevant background info.

## Keyword Optimization Strategy

- **Primary Subject/Entity**: Needs to be in the URL, Headline tag, and the Lede.
- **Trending Terms**: Incorporate currently trending phrases related to the topic.
- Use exact names of entities (people, organizations, locations).

## E-E-A-T (Critical for News)

- **Expertise/Authoritativeness**: The author must have clear credentials or a track record of covering this beat.
- **Trustworthiness**: Clear editorial policies, correction policies, and fact-checking statements available on the site level.
- **Experience**: "On the ground" reporting or firsthand accounts are highly valued.

## Required Schema Markup

Must use `NewsArticle` schema. Highly recommended to use `Speakable` schema for voice search (smart speakers).

```json
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "Breaking News Headline",
  "image": [
    "https://example.com/photos/1x1/photo.jpg",
    "https://example.com/photos/4x3/photo.jpg",
    "https://example.com/photos/16x9/photo.jpg"
   ],
  "datePublished": "2026-03-02T08:00:00+08:00",
  "dateModified": "2026-03-02T09:30:00+08:00",
  "author": [{
      "@type": "Person",
      "name": "Jane Journalist",
      "url": "https://example.com/profile/jane-journalist"
    }]
}
```

#!/usr/bin/env python3
"""
Competitor Topic Gap Analyzer

Crawls competitor sitemaps / pages, extracts H-tag topics, and identifies
content gaps by comparing against your site's topic coverage.

No API keys required — uses sitemaps and on-page content only.

Usage:
    python competitor_gap.py https://yoursite.com --competitor https://competitor.com --json
    python competitor_gap.py https://yoursite.com --competitor https://c1.com --competitor https://c2.com
"""

import argparse
import json
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from urllib.parse import urlparse, urljoin

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 required. Install with: pip install beautifulsoup4")
    sys.exit(1)


USER_AGENT = "Mozilla/5.0 (compatible; SEOSkill-GapAnalysis/1.0)"

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "with", "by", "of", "from", "as", "is", "are", "was", "were", "be",
    "been", "this", "that", "these", "those", "it", "he", "she", "they",
    "we", "you", "your", "my", "their", "our", "its", "which", "who",
    "what", "where", "when", "why", "how", "all", "any", "both", "each",
    "few", "more", "most", "other", "some", "such", "no", "not", "only",
    "own", "same", "so", "than", "too", "very", "can", "will", "just",
    "should", "have", "has", "had", "do", "does", "did", "about", "into",
    "would", "could", "here", "there", "also", "get", "got", "make", "use",
}


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def fetch_page(url: str, timeout: int = 10) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def extract_sitemap_urls(site_url: str, limit: int = 100) -> list:
    """Extract URLs from sitemap.xml."""
    parsed = urlparse(site_url)
    sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"

    html = fetch_page(sitemap_url)
    if not html:
        return []

    urls = re.findall(r"<loc>([^<]+)</loc>", html)

    # Handle sitemap index (sitemaps pointing to other sitemaps)
    if any("sitemap" in u.lower() and u.endswith(".xml") for u in urls[:5]):
        expanded = []
        for sub_url in urls[:10]:
            time.sleep(0.3)
            sub_html = fetch_page(sub_url)
            if sub_html:
                expanded.extend(re.findall(r"<loc>([^<]+)</loc>", sub_html))
        urls = expanded

    return urls[:limit]


# ---------------------------------------------------------------------------
# Topic extraction
# ---------------------------------------------------------------------------

def extract_topics(html: str) -> dict:
    """Extract topics from H-tags and title of a page."""
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    topics = {
        "title": title,
        "h1": [],
        "h2": [],
        "h3": [],
    }

    for tag in ["h1", "h2", "h3"]:
        for h in soup.find_all(tag):
            text = h.get_text(strip=True)
            if text and len(text) > 3:
                topics[tag].append(text)

    return topics


def normalize_topic(text: str) -> str:
    """Normalize a topic string for comparison."""
    words = re.findall(r"\b[a-z]+\b", text.lower())
    return " ".join(w for w in words if w not in STOP_WORDS and len(w) > 2)


def extract_topic_phrases(topics: dict) -> set:
    """Extract normalized topic phrases from H-tags."""
    phrases = set()
    for source in ["title", "h1", "h2", "h3"]:
        items = topics[source]
        if isinstance(items, str):
            items = [items]
        for text in items:
            norm = normalize_topic(text)
            if norm and len(norm.split()) >= 2:
                phrases.add(norm)
    return phrases


# ---------------------------------------------------------------------------
# Site crawl (lightweight — sitemap + top pages)
# ---------------------------------------------------------------------------

def crawl_site_topics(site_url: str, max_pages: int = 50) -> dict:
    """
    Crawl a site's sitemap and extract topics from each page.
    Returns {url: {title, h1, h2, h3}} and a set of all topic phrases.
    """
    urls = extract_sitemap_urls(site_url, limit=max_pages)

    if not urls:
        # Fallback: crawl homepage and extract internal links
        homepage = fetch_page(site_url)
        if homepage:
            soup = BeautifulSoup(homepage, "html.parser")
            base_domain = urlparse(site_url).netloc
            for a in soup.find_all("a", href=True):
                full = urljoin(site_url, a["href"])
                if urlparse(full).netloc == base_domain:
                    urls.append(full)
            urls = list(set(urls))[:max_pages]

    page_topics = {}
    all_phrases = set()

    for url in urls:
        time.sleep(0.3)
        html = fetch_page(url)
        if not html:
            continue

        topics = extract_topics(html)
        page_topics[url] = topics
        all_phrases.update(extract_topic_phrases(topics))

    return {
        "pages_crawled": len(page_topics),
        "page_topics": page_topics,
        "all_phrases": all_phrases,
    }


# ---------------------------------------------------------------------------
# Gap analysis
# ---------------------------------------------------------------------------

def find_topic_gaps(your_phrases: set, competitor_data: dict) -> dict:
    """
    Compare your topic coverage vs competitors.
    Returns gaps (topics competitors cover that you don't).
    """
    gaps = []
    competitor_only = set()

    for comp_url, comp in competitor_data.items():
        comp_phrases = comp["all_phrases"]
        comp_unique = comp_phrases - your_phrases

        for phrase in comp_unique:
            competitor_only.add(phrase)
            gaps.append({
                "topic": phrase,
                "competitor": comp_url,
                "competitor_pages": comp["pages_crawled"],
            })

    # Deduplicate and count coverage
    topic_coverage = Counter()
    for gap in gaps:
        topic_coverage[gap["topic"]] += 1

    # Sort by coverage (topics covered by more competitors = higher priority)
    prioritized = []
    seen = set()
    for topic, count in topic_coverage.most_common():
        if topic not in seen:
            sources = [g["competitor"] for g in gaps if g["topic"] == topic]
            prioritized.append({
                "topic": topic,
                "covered_by_competitors": count,
                "competitors": sources,
                "priority": "High" if count >= 2 else "Medium",
            })
            seen.add(topic)

    # Your unique topics (competitive advantage)
    your_unique = your_phrases - competitor_only

    return {
        "gaps": prioritized[:50],
        "your_unique_topics": len(your_unique),
        "competitor_unique_topics": len(competitor_only),
        "overlap_topics": len(your_phrases & competitor_only),
        "total_your_topics": len(your_phrases),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Competitor Topic Gap Analyzer — finds content gaps from competitor sitemaps/pages"
    )
    parser.add_argument("url", help="Your site URL")
    parser.add_argument("--competitor", action="append", required=True, help="Competitor URL (can specify multiple)")
    parser.add_argument("--max-pages", type=int, default=50, help="Max pages to crawl per site (default: 50)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    print(f"Crawling your site: {args.url}...", file=sys.stderr)
    your_data = crawl_site_topics(args.url, max_pages=args.max_pages)

    competitor_data = {}
    for comp_url in args.competitor:
        print(f"Crawling competitor: {comp_url}...", file=sys.stderr)
        competitor_data[comp_url] = crawl_site_topics(comp_url, max_pages=args.max_pages)

    print("Analyzing topic gaps...", file=sys.stderr)
    gap_report = find_topic_gaps(your_data["all_phrases"], competitor_data)

    report = {
        "your_site": args.url,
        "your_pages_crawled": your_data["pages_crawled"],
        "your_topics": len(your_data["all_phrases"]),
        "competitors": {
            url: {"pages_crawled": d["pages_crawled"], "topics": len(d["all_phrases"])}
            for url, d in competitor_data.items()
        },
        "analysis": gap_report,
    }

    if args.json:
        # Convert sets to lists for JSON serialization
        report_json = json.loads(json.dumps(report, default=lambda x: list(x) if isinstance(x, set) else str(x)))
        print(json.dumps(report_json, indent=2))
        return

    print(f"\nTopic Gap Analysis")
    print("=" * 60)
    print(f"Your Site          : {args.url} ({your_data['pages_crawled']} pages, {len(your_data['all_phrases'])} topics)")
    for url, d in competitor_data.items():
        print(f"Competitor         : {url} ({d['pages_crawled']} pages, {len(d['all_phrases'])} topics)")

    ga = gap_report
    print(f"\nCoverage Summary:")
    print(f"  Your unique topics             : {ga['your_unique_topics']}")
    print(f"  Competitor-only topics (GAPS)   : {ga['competitor_unique_topics']}")
    print(f"  Shared topics                  : {ga['overlap_topics']}")

    if ga["gaps"]:
        print(f"\nTop Content Gaps ({len(ga['gaps'])} found):")
        for gap in ga["gaps"][:20]:
            icon = "🔴" if gap["priority"] == "High" else "⚠️"
            comp_str = ", ".join(urlparse(c).netloc for c in gap["competitors"])
            print(f"  {icon} \"{gap['topic']}\" — covered by {gap['covered_by_competitors']} competitor(s): {comp_str}")

        print("\nRecommendation: Create content targeting the high-priority gap topics above.")
        print("Start with topics covered by 2+ competitors (highest opportunity).")
    else:
        print("\n✅ No significant topic gaps found — your content coverage is strong!")


if __name__ == "__main__":
    main()

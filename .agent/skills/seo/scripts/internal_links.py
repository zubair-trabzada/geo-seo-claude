#!/usr/bin/env python3
"""
Analyze internal link structure of a website.

Checks link count, anchor text distribution, orphan page detection,
and link depth from homepage.

Usage:
    python internal_links.py https://example.com
    python internal_links.py https://example.com --depth 2 --json
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 required. Install with: pip install beautifulsoup4")
    sys.exit(1)


HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SEOSkill/1.0)"}


def extract_internal_links(html: str, page_url: str, domain: str) -> list:
    """Extract internal links from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
            continue

        absolute = urljoin(page_url, href)
        parsed = urlparse(absolute)

        # Only internal links
        if parsed.netloc != domain:
            continue

        # Normalize: remove fragments, trailing slashes
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if normalized.endswith("/") and len(parsed.path) > 1:
            normalized = normalized.rstrip("/")

        if normalized in seen:
            continue
        seen.add(normalized)

        anchor_text = tag.get_text(strip=True)[:80] or "[no text]"
        nofollow = "nofollow" in (tag.get("rel", []) or [])
        links.append({
            "url": normalized,
            "anchor_text": anchor_text,
            "nofollow": nofollow,
            "source": page_url,
        })

    return links


def crawl_site(start_url: str, max_depth: int = 2, max_pages: int = 50,
               max_workers: int = 5, timeout: int = 10) -> dict:
    """
    Crawl internal links up to max_depth.

    Args:
        start_url: Starting URL (usually homepage)
        max_depth: Maximum crawl depth
        max_pages: Maximum pages to crawl
        max_workers: Concurrent request threads
        timeout: Per-page timeout

    Returns:
        Dictionary with link structure analysis
    """
    parsed = urlparse(start_url)
    domain = parsed.netloc

    result = {
        "start_url": start_url,
        "domain": domain,
        "pages_crawled": 0,
        "total_internal_links": 0,
        "unique_pages_found": 0,
        "max_depth_reached": 0,
        "pages": {},
        "anchor_texts": {},
        "link_distribution": {},
        "orphan_candidates": [],
        "nofollow_links": [],
        "issues": [],
        "recommendations": [],
        "error": None,
    }

    # BFS crawl
    visited = set()
    queue = [(start_url, 0)]  # (url, depth)
    all_links = []
    page_link_counts = {}
    pages_linking_to = defaultdict(set)  # url -> set of pages linking to it
    pages_found_at_depth = defaultdict(list)

    def fetch_page(url):
        try:
            resp = requests.get(url, timeout=timeout, headers=HEADERS, allow_redirects=True)
            if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
                return resp.text, resp.url
        except requests.exceptions.RequestException:
            pass
        return None, url

    while queue and len(visited) < max_pages:
        # Process current batch
        batch = []
        while queue and len(batch) < max_workers:
            url, depth = queue.pop(0)
            if url in visited or depth > max_depth:
                continue
            visited.add(url)
            batch.append((url, depth))

        if not batch:
            break

        # Fetch pages concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_page, url): (url, depth) for url, depth in batch}
            for future in as_completed(futures):
                url, depth = futures[future]
                html, final_url = future.result()

                if html is None:
                    continue

                links = extract_internal_links(html, final_url, domain)
                page_link_counts[url] = len(links)
                pages_found_at_depth[depth].append(url)
                result["max_depth_reached"] = max(result["max_depth_reached"], depth)

                for link in links:
                    all_links.append(link)
                    pages_linking_to[link["url"]].add(url)

                    if link["nofollow"]:
                        result["nofollow_links"].append(link)

                    # Add to crawl queue
                    if link["url"] not in visited and depth + 1 <= max_depth:
                        queue.append((link["url"], depth + 1))

    result["pages_crawled"] = len(visited)
    result["total_internal_links"] = len(all_links)
    result["unique_pages_found"] = len(pages_linking_to)

    # Anchor text distribution
    anchor_counter = Counter(link["anchor_text"] for link in all_links if link["anchor_text"] != "[no text]")
    result["anchor_texts"] = dict(anchor_counter.most_common(20))

    # Link distribution (outgoing links per page)
    result["link_distribution"] = {
        "min": min(page_link_counts.values()) if page_link_counts else 0,
        "max": max(page_link_counts.values()) if page_link_counts else 0,
        "avg": round(sum(page_link_counts.values()) / max(1, len(page_link_counts)), 1),
    }

    # Pages info
    for url in visited:
        outgoing = page_link_counts.get(url, 0)
        incoming = len(pages_linking_to.get(url, set()))
        result["pages"][url] = {
            "outgoing_links": outgoing,
            "incoming_links": incoming,
        }

    # Orphan candidates (pages with 0 or 1 incoming links, excluding start)
    for url, sources in pages_linking_to.items():
        if url != start_url and len(sources) <= 1:
            result["orphan_candidates"].append({
                "url": url,
                "incoming_links": len(sources),
            })

    # Issues
    if result["orphan_candidates"]:
        result["issues"].append(
            f"⚠️ {len(result['orphan_candidates'])} potential orphan page(s) "
            f"(≤1 internal link pointing to them)"
        )

    # Check for pages with too few outgoing links
    low_link_pages = [url for url, count in page_link_counts.items() if count < 3]
    if low_link_pages:
        result["issues"].append(
            f"⚠️ {len(low_link_pages)} page(s) have fewer than 3 internal links"
        )

    # Check for pages with excessive links
    high_link_pages = [url for url, count in page_link_counts.items() if count > 100]
    if high_link_pages:
        result["issues"].append(
            f"⚠️ {len(high_link_pages)} page(s) have >100 internal links — may dilute link equity"
        )

    # Check nofollow on internal links
    if result["nofollow_links"]:
        result["issues"].append(
            f"⚠️ {len(result['nofollow_links'])} internal link(s) have nofollow — "
            f"this wastes link equity"
        )

    # Check anchor text issues
    no_text_links = sum(1 for l in all_links if l["anchor_text"] == "[no text]")
    if no_text_links:
        result["issues"].append(
            f"⚠️ {no_text_links} link(s) have no anchor text"
        )

    # Recommendations
    if result["orphan_candidates"]:
        result["recommendations"].append(
            "Add internal links pointing to orphan pages from related content"
        )
    if result["link_distribution"]["avg"] < 5:
        result["recommendations"].append(
            "Increase internal linking — aim for 3-5 relevant links per 1000 words"
        )

    return result


def main():
    parser = argparse.ArgumentParser(description="Analyze internal link structure")
    parser.add_argument("url", help="Website URL (usually homepage)")
    parser.add_argument("--depth", "-d", type=int, default=2,
                        help="Max crawl depth (default: 2)")
    parser.add_argument("--max-pages", "-m", type=int, default=50,
                        help="Max pages to crawl (default: 50)")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    result = crawl_site(args.url, max_depth=args.depth, max_pages=args.max_pages)

    if args.json:
        # Trim for readability
        output = {k: v for k, v in result.items()}
        # Convert sets to lists for JSON
        for url, info in output.get("pages", {}).items():
            if isinstance(info, set):
                output["pages"][url] = list(info)
        print(json.dumps(output, indent=2, default=str))
        return

    if result["error"]:
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"Internal Link Analysis — {result['domain']}")
    print("=" * 50)
    print(f"Pages crawled: {result['pages_crawled']}")
    print(f"Unique pages found: {result['unique_pages_found']}")
    print(f"Total internal links: {result['total_internal_links']}")
    print(f"Max depth reached: {result['max_depth_reached']}")

    dist = result["link_distribution"]
    print(f"\nLinks per page: min={dist['min']}, max={dist['max']}, avg={dist['avg']}")

    if result["orphan_candidates"]:
        print(f"\n⚠️ Potential Orphan Pages ({len(result['orphan_candidates'])}):")
        for orphan in result["orphan_candidates"][:10]:
            print(f"  • {orphan['url']} ({orphan['incoming_links']} incoming)")

    if result["anchor_texts"]:
        print(f"\nTop Anchor Texts:")
        for text, count in list(result["anchor_texts"].items())[:10]:
            print(f"  [{count}x] \"{text}\"")

    if result["nofollow_links"]:
        print(f"\n⚠️ Nofollow Internal Links ({len(result['nofollow_links'])}):")
        for link in result["nofollow_links"][:5]:
            print(f"  • {link['url']} (from {link['source']})")

    if result["issues"]:
        print(f"\nIssues:")
        for issue in result["issues"]:
            print(f"  {issue}")

    if result["recommendations"]:
        print(f"\nRecommendations:")
        for rec in result["recommendations"]:
            print(f"  💡 {rec}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Duplicate & Thin Content Detector

Detects near-duplicate pages and thin content across a site using
MinHash / Jaccard similarity and word-count thresholds.

Usage:
    python duplicate_content.py https://example.com --depth 2 --json
    python duplicate_content.py https://example.com --threshold 0.85
"""

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from collections import defaultdict
from urllib.parse import urljoin, urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 required. Install with: pip install beautifulsoup4")
    sys.exit(1)


USER_AGENT = "Mozilla/5.0 (compatible; SEOSkill-DupCheck/1.0)"

# Quality gates from resources/references/quality-gates.md
THIN_CONTENT_THRESHOLDS = {
    "blog_post": 1500,
    "landing_page": 800,
    "product_page": 300,
    "location_page": 350,
    "default": 300,
}


# ---------------------------------------------------------------------------
# Fetch & extract
# ---------------------------------------------------------------------------

def fetch_page(url: str, timeout: int = 12) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ct = resp.headers.get("Content-Type", "")
            if "text/html" not in ct:
                return ""
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def extract_text(html: str) -> str:
    """Extract visible body text, stripping nav/footer/scripts."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    body = soup.find("body")
    if not body:
        return ""
    return body.get_text(separator=" ", strip=True)


def extract_internal_links(html: str, base_url: str) -> list:
    """Extract internal links from a page."""
    soup = BeautifulSoup(html, "html.parser")
    base_domain = urlparse(base_url).netloc
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
            continue
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if clean.endswith("/"):
                clean = clean[:-1]
            links.append(clean)
    return list(set(links))


# ---------------------------------------------------------------------------
# Shingle-based MinHash for near-duplicate detection
# ---------------------------------------------------------------------------

def shingle(text: str, k: int = 5) -> set:
    """Create k-word shingles from text."""
    words = re.findall(r"\b[a-z]+\b", text.lower())
    if len(words) < k:
        return {" ".join(words)}
    return {" ".join(words[i:i+k]) for i in range(len(words) - k + 1)}


def minhash_signature(shingles: set, num_hashes: int = 100) -> list:
    """Compute MinHash signature for a set of shingles."""
    sig = []
    for i in range(num_hashes):
        min_hash = float("inf")
        for s in shingles:
            h = int(hashlib.md5(f"{i}:{s}".encode()).hexdigest(), 16)
            if h < min_hash:
                min_hash = h
        sig.append(min_hash)
    return sig


def jaccard_from_minhash(sig1: list, sig2: list) -> float:
    """Estimate Jaccard similarity from two MinHash signatures."""
    if not sig1 or not sig2:
        return 0.0
    matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
    return matches / len(sig1)


def exact_hash(text: str) -> str:
    """SHA-256 of normalized text for exact duplicate detection."""
    normalized = re.sub(r"\s+", " ", text.lower().strip())
    return hashlib.sha256(normalized.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Crawl
# ---------------------------------------------------------------------------

def crawl_site(start_url: str, max_pages: int = 50, depth: int = 2) -> dict:
    """
    Crawl a site starting from start_url.
    Returns {url: {"text": str, "word_count": int, "html": str}}.
    """
    visited = {}
    queue = [(start_url, 0)]
    seen = {start_url}

    while queue and len(visited) < max_pages:
        url, d = queue.pop(0)
        time.sleep(0.5)  # polite delay

        html = fetch_page(url)
        if not html:
            continue

        text = extract_text(html)
        word_count = len(re.findall(r"\b\w+\b", text))

        visited[url] = {
            "text": text,
            "word_count": word_count,
        }

        if d < depth:
            for link in extract_internal_links(html, url):
                if link not in seen and len(seen) < max_pages * 3:
                    seen.add(link)
                    queue.append((link, d + 1))

    return visited


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def detect_duplicates(pages: dict, similarity_threshold: float = 0.85) -> dict:
    """
    Detect exact and near-duplicate pages.
    Returns report with exact dupes, near-dupes, and thin content.
    """
    # Step 1: Exact duplicates (hash comparison)
    hash_groups = defaultdict(list)
    signatures = {}

    for url, data in pages.items():
        text = data["text"]
        if not text.strip():
            continue
        h = exact_hash(text)
        hash_groups[h].append(url)

        # MinHash signature for near-duplicate comparison
        s = shingle(text)
        if s:
            signatures[url] = minhash_signature(s)

    exact_dupes = []
    for h, urls in hash_groups.items():
        if len(urls) > 1:
            exact_dupes.append({
                "type": "exact_duplicate",
                "severity": "Critical",
                "urls": urls,
                "finding": f"{len(urls)} pages have identical content.",
                "fix": "Consolidate into a single canonical page and redirect duplicates with 301.",
            })

    # Step 2: Near-duplicates (MinHash Jaccard)
    near_dupes = []
    urls = list(signatures.keys())
    checked = set()

    for i in range(len(urls)):
        for j in range(i + 1, len(urls)):
            pair = (urls[i], urls[j])
            if pair in checked:
                continue
            checked.add(pair)

            sim = jaccard_from_minhash(signatures[urls[i]], signatures[urls[j]])
            if sim >= similarity_threshold:
                # Skip if already in exact dupes
                if any(urls[i] in ed["urls"] and urls[j] in ed["urls"] for ed in exact_dupes):
                    continue
                near_dupes.append({
                    "type": "near_duplicate",
                    "severity": "Warning",
                    "similarity": round(sim, 3),
                    "url_a": urls[i],
                    "url_b": urls[j],
                    "word_count_a": pages[urls[i]]["word_count"],
                    "word_count_b": pages[urls[j]]["word_count"],
                    "finding": f"Pages are {sim:.0%} similar — likely near-duplicate content.",
                    "fix": "Differentiate content significantly, or set one as canonical and noindex the other.",
                })

    # Step 3: Thin content
    thin_pages = []
    for url, data in pages.items():
        wc = data["word_count"]
        threshold = THIN_CONTENT_THRESHOLDS["default"]
        if wc < threshold:
            thin_pages.append({
                "type": "thin_content",
                "severity": "Warning" if wc >= 100 else "Critical",
                "url": url,
                "word_count": wc,
                "threshold": threshold,
                "finding": f"Only {wc} words (minimum: {threshold}).",
                "fix": f"Expand content to at least {threshold} words of substantive, unique content, or noindex if low-value.",
            })

    return {
        "pages_analyzed": len(pages),
        "exact_duplicates": exact_dupes,
        "near_duplicates": near_dupes,
        "thin_content": thin_pages,
        "summary": {
            "exact_duplicate_groups": len(exact_dupes),
            "near_duplicate_pairs": len(near_dupes),
            "thin_pages": len(thin_pages),
            "avg_word_count": round(
                sum(p["word_count"] for p in pages.values()) / max(1, len(pages))
            ),
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Duplicate & Thin Content Detector (MinHash / Jaccard similarity)"
    )
    parser.add_argument("url", help="Start URL to crawl")
    parser.add_argument("--depth", type=int, default=2, help="Crawl depth (default: 2)")
    parser.add_argument("--max-pages", type=int, default=50, help="Max pages to crawl (default: 50)")
    parser.add_argument("--threshold", type=float, default=0.85,
                        help="Jaccard similarity threshold for near-duplicates (default: 0.85)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    print(f"Crawling {args.url} (depth={args.depth}, max={args.max_pages})...", file=sys.stderr)
    pages = crawl_site(args.url, max_pages=args.max_pages, depth=args.depth)
    print(f"Crawled {len(pages)} pages. Analyzing...", file=sys.stderr)

    report = detect_duplicates(pages, similarity_threshold=args.threshold)

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print(f"\nDuplicate & Thin Content Report")
    print("=" * 60)
    print(f"Pages Analyzed    : {report['pages_analyzed']}")
    print(f"Avg Word Count    : {report['summary']['avg_word_count']}")

    if report["exact_duplicates"]:
        print(f"\nExact Duplicates ({report['summary']['exact_duplicate_groups']} groups):")
        for group in report["exact_duplicates"]:
            print(f"  🔴 {len(group['urls'])} identical pages:")
            for url in group["urls"]:
                print(f"     - {url}")
            print(f"     Fix: {group['fix']}")

    if report["near_duplicates"]:
        print(f"\nNear-Duplicates ({report['summary']['near_duplicate_pairs']} pairs):")
        for pair in report["near_duplicates"]:
            print(f"  ⚠️  {pair['similarity']:.0%} similar:")
            print(f"     A: {pair['url_a']} ({pair['word_count_a']} words)")
            print(f"     B: {pair['url_b']} ({pair['word_count_b']} words)")
            print(f"     Fix: {pair['fix']}")

    if report["thin_content"]:
        print(f"\nThin Content ({report['summary']['thin_pages']} pages):")
        for page in sorted(report["thin_content"], key=lambda x: x["word_count"]):
            icon = "🔴" if page["severity"] == "Critical" else "⚠️"
            print(f"  {icon} {page['url']} — {page['word_count']} words (min: {page['threshold']})")

    if not report["exact_duplicates"] and not report["near_duplicates"] and not report["thin_content"]:
        print("\n✅ No duplicate or thin content issues detected.")


if __name__ == "__main__":
    main()

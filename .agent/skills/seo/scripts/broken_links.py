#!/usr/bin/env python3
"""
Check for broken links on a web page.

Crawls all links (internal + external) on a page, checks HTTP status.
Reports broken (4xx/5xx), redirected (3xx), and timeout links.

Usage:
    python broken_links.py https://example.com
    python broken_links.py https://example.com --json
    python broken_links.py https://example.com --internal-only
"""

import argparse
import json
import sys
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
    print("Error: beautifulsoup4 library required. Install with: pip install beautifulsoup4")
    sys.exit(1)


HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SEOSkill/1.0)"}


def extract_links(html: str, base_url: str) -> list:
    """Extract all links from HTML content."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()

        # Skip anchors, javascript, mailto, tel
        if href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
            continue

        absolute = urljoin(base_url, href)
        if absolute in seen:
            continue
        seen.add(absolute)

        anchor_text = tag.get_text(strip=True)[:80] or "[no text]"
        links.append({
            "url": absolute,
            "anchor_text": anchor_text,
            "is_internal": urlparse(absolute).netloc == urlparse(base_url).netloc,
        })

    return links


def check_link(link: dict, timeout: int = 10) -> dict:
    """Check a single link's HTTP status."""
    url = link["url"]
    result = {**link, "status": None, "error": None, "redirect": None, "response_time_ms": None}

    try:
        resp = requests.head(url, timeout=timeout, headers=HEADERS,
                             allow_redirects=True, verify=False)

        # Some servers reject HEAD, fall back to GET
        if resp.status_code == 405:
            resp = requests.get(url, timeout=timeout, headers=HEADERS,
                                allow_redirects=True, verify=False, stream=True)

        result["status"] = resp.status_code
        result["response_time_ms"] = round(resp.elapsed.total_seconds() * 1000)

        # Check if redirected
        if resp.history:
            result["redirect"] = {
                "from": url,
                "to": resp.url,
                "hops": len(resp.history),
                "codes": [r.status_code for r in resp.history],
            }

    except requests.exceptions.Timeout:
        result["error"] = "timeout"
    except requests.exceptions.ConnectionError:
        result["error"] = "connection_failed"
    except requests.exceptions.TooManyRedirects:
        result["error"] = "too_many_redirects"
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)[:100]

    return result


def check_broken_links(url: str, internal_only: bool = False,
                       max_workers: int = 10, timeout: int = 10) -> dict:
    """
    Check all links on a page for broken links.

    Args:
        url: Page URL to check
        internal_only: Only check internal links
        max_workers: Concurrent request threads
        timeout: Per-request timeout in seconds

    Returns:
        Dictionary with all link check results
    """
    result = {
        "page_url": url,
        "total_links": 0,
        "checked": 0,
        "broken": [],
        "redirected": [],
        "timeout": [],
        "healthy": 0,
        "summary": {},
        "issues": [],
        "error": None,
    }

    # Fetch page
    try:
        resp = requests.get(url, timeout=15, headers=HEADERS)
        if resp.status_code != 200:
            result["error"] = f"Failed to fetch page: HTTP {resp.status_code}"
            return result
        html = resp.text
    except requests.exceptions.RequestException as e:
        result["error"] = f"Failed to fetch page: {e}"
        return result

    # Extract links
    links = extract_links(html, url)
    if internal_only:
        links = [l for l in links if l["is_internal"]]

    result["total_links"] = len(links)

    if not links:
        result["issues"].append("⚠️ No links found on page")
        return result

    # Check all links concurrently
    checked = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check_link, link, timeout): link for link in links}
        for future in as_completed(futures):
            checked.append(future.result())

    result["checked"] = len(checked)

    for link in checked:
        status = link["status"]

        if link["error"]:
            if link["error"] == "timeout":
                result["timeout"].append(link)
            else:
                result["broken"].append(link)
        elif status and status >= 400:
            result["broken"].append(link)
        elif link["redirect"]:
            result["redirected"].append(link)
        else:
            result["healthy"] += 1

    # Generate summary
    result["summary"] = {
        "total": result["total_links"],
        "healthy": result["healthy"],
        "broken": len(result["broken"]),
        "redirected": len(result["redirected"]),
        "timeout": len(result["timeout"]),
    }

    # Generate issues
    if result["broken"]:
        result["issues"].append(
            f"🔴 {len(result['broken'])} broken link(s) found"
        )
    if result["timeout"]:
        result["issues"].append(
            f"⚠️ {len(result['timeout'])} link(s) timed out"
        )
    if result["redirected"]:
        chains = [l for l in result["redirected"]
                  if l.get("redirect", {}).get("hops", 0) > 1]
        if chains:
            result["issues"].append(
                f"⚠️ {len(chains)} redirect chain(s) detected (>1 hop)"
            )

    return result


def main():
    parser = argparse.ArgumentParser(description="Check for broken links on a page")
    parser.add_argument("url", help="Page URL to check")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--internal-only", "-i", action="store_true",
                        help="Only check internal links")
    parser.add_argument("--workers", "-w", type=int, default=10,
                        help="Concurrent workers (default: 10)")
    parser.add_argument("--timeout", "-t", type=int, default=10,
                        help="Per-link timeout in seconds (default: 10)")

    args = parser.parse_args()
    result = check_broken_links(args.url, internal_only=args.internal_only,
                                max_workers=args.workers, timeout=args.timeout)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    if result["error"]:
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"Broken Link Check — {result['page_url']}")
    print("=" * 50)
    s = result["summary"]
    print(f"Total: {s['total']} | ✅ Healthy: {s['healthy']} | "
          f"🔴 Broken: {s['broken']} | ↪️ Redirected: {s['redirected']} | "
          f"⏱️ Timeout: {s['timeout']}")

    if result["broken"]:
        print(f"\n🔴 Broken Links:")
        for link in result["broken"]:
            status = link["status"] or link["error"]
            loc = "internal" if link["is_internal"] else "external"
            print(f"  [{status}] ({loc}) {link['url']}")
            print(f"         anchor: \"{link['anchor_text']}\"")

    if result["redirected"]:
        chains = [l for l in result["redirected"]
                  if l.get("redirect", {}).get("hops", 0) > 1]
        if chains:
            print(f"\n⚠️ Redirect Chains (>1 hop):")
            for link in chains:
                r = link["redirect"]
                print(f"  {link['url']}")
                print(f"    → {r['to']} ({r['hops']} hops: {r['codes']})")

    if result["timeout"]:
        print(f"\n⏱️ Timed Out:")
        for link in result["timeout"]:
            print(f"  {link['url']}")

    if result["issues"]:
        print(f"\nIssues:")
        for issue in result["issues"]:
            print(f"  {issue}")


if __name__ == "__main__":
    main()

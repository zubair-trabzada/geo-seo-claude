#!/usr/bin/env python3
"""
Check redirect chains for a URL.

Follows the full redirect chain, reports each hop (status + destination),
detects mixed HTTP/HTTPS, redirect loops, and chain length issues.

Usage:
    python redirect_checker.py https://example.com
    python redirect_checker.py https://example.com http://example.com --json
"""

import argparse
import json
import sys
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)


HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SEOSkill/1.0)"}


def check_redirects(url: str, max_redirects: int = 10, timeout: int = 10) -> dict:
    """
    Follow and analyze the redirect chain for a URL.

    Args:
        url: URL to check
        max_redirects: Maximum redirects to follow
        timeout: Request timeout in seconds

    Returns:
        Dictionary with redirect chain analysis
    """
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"

    result = {
        "url": url,
        "final_url": None,
        "chain": [],
        "total_hops": 0,
        "total_time_ms": 0,
        "has_loop": False,
        "has_mixed_protocol": False,
        "issues": [],
        "error": None,
    }

    seen = set()
    current = url

    try:
        for i in range(max_redirects + 1):
            if current in seen:
                result["has_loop"] = True
                result["issues"].append(f"🔴 Redirect loop detected at: {current}")
                break
            seen.add(current)

            resp = requests.head(current, timeout=timeout, headers=HEADERS,
                                 allow_redirects=False)

            hop = {
                "step": i + 1,
                "url": current,
                "status": resp.status_code,
                "time_ms": round(resp.elapsed.total_seconds() * 1000),
            }

            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("Location", "")
                if not location:
                    hop["error"] = "Redirect with no Location header"
                    result["chain"].append(hop)
                    result["issues"].append(f"🔴 Redirect at step {i+1} has no Location header")
                    break

                # Resolve relative URLs
                if not urlparse(location).scheme:
                    from urllib.parse import urljoin
                    location = urljoin(current, location)

                hop["redirect_to"] = location
                hop["redirect_type"] = {
                    301: "permanent (301)",
                    302: "temporary (302)",
                    303: "see other (303)",
                    307: "temporary (307)",
                    308: "permanent (308)",
                }.get(resp.status_code, f"unknown ({resp.status_code})")

                result["chain"].append(hop)
                result["total_time_ms"] += hop["time_ms"]
                current = location
            else:
                # Final destination
                hop["final"] = True
                result["chain"].append(hop)
                result["final_url"] = current
                result["total_time_ms"] += hop["time_ms"]
                break
        else:
            result["issues"].append(f"🔴 Too many redirects (>{max_redirects})")

    except requests.exceptions.RequestException as e:
        result["error"] = str(e)

    result["total_hops"] = max(0, len(result["chain"]) - 1)

    # Check for mixed protocol
    protocols = set()
    for hop in result["chain"]:
        protocols.add(urlparse(hop["url"]).scheme)
    if "http" in protocols and "https" in protocols:
        result["has_mixed_protocol"] = True
        result["issues"].append("⚠️ Mixed HTTP/HTTPS in redirect chain")

    # Check chain length
    if result["total_hops"] > 2:
        result["issues"].append(
            f"🔴 Long redirect chain ({result['total_hops']} hops) — degrades crawl efficiency"
        )
    elif result["total_hops"] > 1:
        result["issues"].append(
            f"⚠️ Redirect chain has {result['total_hops']} hops — aim for max 1"
        )

    # Check for 302 where 301 should be used
    for hop in result["chain"]:
        if hop["status"] == 302:
            result["issues"].append(
                f"⚠️ Temporary redirect (302) at step {hop['step']} — "
                f"use 301 for permanent moves to preserve link equity"
            )

    return result


def main():
    parser = argparse.ArgumentParser(description="Check redirect chains")
    parser.add_argument("urls", nargs="+", help="URL(s) to check")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    results = []
    for url in args.urls:
        results.append(check_redirects(url))

    if args.json:
        output = results if len(results) > 1 else results[0]
        print(json.dumps(output, indent=2))
        return

    for result in results:
        if result["error"]:
            print(f"Error checking {result['url']}: {result['error']}")
            continue

        print(f"Redirect Chain — {result['url']}")
        print("=" * 50)

        if not result["chain"]:
            print("  No response received")
            continue

        for hop in result["chain"]:
            status = hop["status"]
            time_ms = hop["time_ms"]

            if hop.get("final"):
                icon = "✅" if 200 <= status < 300 else "🔴"
                print(f"  {icon} [{status}] {hop['url']} ({time_ms}ms) — FINAL")
            else:
                redirect_type = hop.get("redirect_type", "")
                print(f"  ↪️ [{status}] {hop['url']} ({time_ms}ms)")
                print(f"       → {hop.get('redirect_to', '?')} ({redirect_type})")

        print(f"\nTotal hops: {result['total_hops']} | Total time: {result['total_time_ms']}ms")

        if result["issues"]:
            print(f"\nIssues:")
            for issue in result["issues"]:
                print(f"  {issue}")
        print()


if __name__ == "__main__":
    main()

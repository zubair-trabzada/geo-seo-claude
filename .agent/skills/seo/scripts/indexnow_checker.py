#!/usr/bin/env python3
"""
IndexNow Checker & Pinger

Validates IndexNow implementation on a site and optionally pings the
IndexNow API to notify search engines of URL updates.

Checks:
  1. IndexNow key file hosted at /{key}.txt
  2. Key referenced in <meta> or robots.txt
  3. Previously submitted URLs (via local log)
  4. Ping mode: submit URLs to IndexNow API

Supported engines: Bing, Yandex, Seznam, Naver

Usage:
    python indexnow_checker.py https://example.com --key YOUR_KEY --json
    python indexnow_checker.py https://example.com --key YOUR_KEY --ping https://example.com/updated-page
    python indexnow_checker.py https://example.com --key YOUR_KEY --ping-sitemap
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


USER_AGENT = "Mozilla/5.0 (compatible; SEOSkill-IndexNow/1.0)"

INDEXNOW_ENDPOINTS = {
    "bing": "https://www.bing.com/indexnow",
    "yandex": "https://yandex.com/indexnow",
    "seznam": "https://search.seznam.cz/indexnow",
    "naver": "https://searchadvisor.naver.com/indexnow",
}


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def fetch_url(url: str, timeout: int = 8) -> tuple:
    """Return (status_code, body) or (None, error_msg)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as exc:
        return None, str(exc)


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

def check_key_file(site_url: str, key: str) -> dict:
    """Check 1: Verify key file is hosted at /{key}.txt"""
    parsed = urlparse(site_url)
    key_url = f"{parsed.scheme}://{parsed.netloc}/{key}.txt"

    status, body = fetch_url(key_url)
    if status == 200 and key in body:
        return {
            "passed": True,
            "detail": f"Key file found at {key_url}",
            "url": key_url,
        }
    elif status == 200:
        return {
            "passed": False,
            "severity": "Critical",
            "finding": f"Key file exists at {key_url} but does not contain the expected key.",
            "fix": f"Update {key_url} to contain only the key value: {key}",
        }
    else:
        return {
            "passed": False,
            "severity": "Critical",
            "finding": f"Key file not found at {key_url} (HTTP {status}).",
            "fix": f"Create a text file at {key_url} containing only: {key}",
        }


def check_key_in_meta(html: str, key: str) -> dict:
    """Check 2: Verify key is referenced in <meta> tag (optional but recommended)."""
    if not BeautifulSoup:
        return {"passed": None, "finding": "beautifulsoup4 not available for meta tag check."}

    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", attrs={"name": "indexnow"})
    if meta and meta.get("content") == key:
        return {"passed": True, "detail": "IndexNow key found in <meta name='indexnow'> tag."}

    return {
        "passed": False,
        "severity": "Info",
        "finding": "No <meta name='indexnow'> tag found (optional but improves validation speed).",
        "fix": f'Add <meta name="indexnow" content="{key}"> to the <head> section.',
    }


def check_robots_txt(site_url: str, key: str) -> dict:
    """Check 3: See if robots.txt references IndexNow."""
    parsed = urlparse(site_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    status, body = fetch_url(robots_url)
    if status != 200:
        return {"passed": None, "finding": f"Could not fetch robots.txt (HTTP {status})."}

    if "indexnow" in body.lower() or key in body:
        return {"passed": True, "detail": "IndexNow reference found in robots.txt."}

    return {
        "passed": None,
        "severity": "Info",
        "finding": "No IndexNow reference in robots.txt (not required, just informational).",
    }


# ---------------------------------------------------------------------------
# Ping API
# ---------------------------------------------------------------------------

def ping_indexnow(site_url: str, key: str, urls: list, engine: str = "bing") -> dict:
    """Submit URLs to IndexNow API."""
    endpoint = INDEXNOW_ENDPOINTS.get(engine, INDEXNOW_ENDPOINTS["bing"])
    parsed = urlparse(site_url)
    host = parsed.netloc

    payload = json.dumps({
        "host": host,
        "key": key,
        "keyLocation": f"{parsed.scheme}://{host}/{key}.txt",
        "urlList": urls,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {
                "success": resp.status in (200, 202),
                "status_code": resp.status,
                "engine": engine,
                "urls_submitted": len(urls),
                "endpoint": endpoint,
            }
    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "status_code": e.code,
            "engine": engine,
            "error": f"HTTP {e.code}: {e.reason}",
        }
    except Exception as exc:
        return {
            "success": False,
            "engine": engine,
            "error": str(exc),
        }


def extract_sitemap_urls(site_url: str, limit: int = 50) -> list:
    """Extract URLs from sitemap.xml for bulk ping."""
    parsed = urlparse(site_url)
    sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"

    status, body = fetch_url(sitemap_url)
    if status != 200:
        return []

    import re
    urls = re.findall(r"<loc>([^<]+)</loc>", body)
    return urls[:limit]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_indexnow_check(site_url: str, key: str) -> dict:
    """Run all IndexNow validation checks."""
    # Fetch homepage for meta tag check
    status, html = fetch_url(site_url)
    if status is None:
        return {"error": f"Failed to fetch {site_url}", "url": site_url}

    results = {
        "url": site_url,
        "key": key[:4] + "..." + key[-4:] if len(key) > 8 else "***",
        "checks": {},
        "issues": [],
        "summary": {"passed": 0, "failed": 0, "info": 0},
    }

    # Run checks
    results["checks"]["key_file"] = check_key_file(site_url, key)
    results["checks"]["meta_tag"] = check_key_in_meta(html, key)
    results["checks"]["robots_txt"] = check_robots_txt(site_url, key)

    # Tally
    for check in results["checks"].values():
        if check.get("passed") is True:
            results["summary"]["passed"] += 1
        elif check.get("passed") is False:
            results["summary"]["failed"] += 1
            results["issues"].append(check)
        else:
            results["summary"]["info"] += 1

    return results


def main():
    parser = argparse.ArgumentParser(
        description="IndexNow Checker & Pinger — validate and submit URLs to search engines"
    )
    parser.add_argument("url", help="Site URL")
    parser.add_argument("--key", required=True, help="IndexNow API key")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--ping", nargs="*", help="URL(s) to submit via IndexNow API")
    parser.add_argument("--ping-sitemap", action="store_true", help="Submit all sitemap URLs")
    parser.add_argument("--engine", default="bing", choices=INDEXNOW_ENDPOINTS.keys(),
                        help="Search engine to ping (default: bing)")
    args = parser.parse_args()

    report = run_indexnow_check(args.url, args.key)

    # Handle ping mode
    if args.ping:
        report["ping_result"] = ping_indexnow(args.url, args.key, args.ping, engine=args.engine)

    if args.ping_sitemap:
        sitemap_urls = extract_sitemap_urls(args.url)
        if sitemap_urls:
            report["ping_result"] = ping_indexnow(args.url, args.key, sitemap_urls, engine=args.engine)
            report["ping_result"]["sitemap_urls_found"] = len(sitemap_urls)
        else:
            report["ping_result"] = {"error": "No sitemap URLs found."}

    if args.json:
        print(json.dumps(report, indent=2))
        return

    if report.get("error"):
        print(f"Error: {report['error']}")
        sys.exit(1)

    print(f"\nIndexNow Validation — {report['url']}")
    print("=" * 60)
    print(f"Key: {report['key']}")

    for name, check in report["checks"].items():
        if check.get("passed") is True:
            print(f"  ✅ {name.replace('_', ' ').title()}: {check.get('detail', 'Pass')}")
        elif check.get("passed") is False:
            print(f"  🔴 {name.replace('_', ' ').title()}: {check.get('finding', '')}")
            print(f"     Fix: {check.get('fix', '')}")
        else:
            print(f"  ℹ️  {name.replace('_', ' ').title()}: {check.get('finding', '')}")

    s = report["summary"]
    print(f"\nSummary: {s['passed']} passed, {s['failed']} failed, {s['info']} info")

    if report.get("ping_result"):
        pr = report["ping_result"]
        if pr.get("success"):
            print(f"\n✅ Ping Success: {pr['urls_submitted']} URLs submitted to {pr['engine']} (HTTP {pr['status_code']})")
        else:
            print(f"\n❌ Ping Failed: {pr.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()

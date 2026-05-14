#!/usr/bin/env python3
"""
Parse and analyze robots.txt for SEO and AI crawler management.

Usage:
    python robots_checker.py https://example.com
    python robots_checker.py https://example.com --json
"""

import argparse
import json
import sys
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)


# AI crawlers to check for explicit management
AI_CRAWLERS = [
    "GPTBot",
    "ChatGPT-User",
    "ClaudeBot",
    "PerplexityBot",
    "Google-Extended",
    "Applebot-Extended",
    "Bytespider",
    "CCBot",
    "anthropic-ai",
    "FacebookBot",
    "Amazonbot",
]

# Standard crawlers for reference
STANDARD_CRAWLERS = [
    "Googlebot",
    "Bingbot",
    "Yandex",
    "Baiduspider",
    "DuckDuckBot",
]


def fetch_robots_txt(url: str, timeout: int = 15) -> dict:
    """Fetch and parse robots.txt from a domain."""
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"
        parsed = urlparse(url)

    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    result = {
        "url": robots_url,
        "status": None,
        "raw": None,
        "user_agents": {},
        "sitemaps": [],
        "crawl_delays": {},
        "ai_crawler_status": {},
        "issues": [],
        "error": None,
    }

    try:
        resp = requests.get(robots_url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (compatible; SEOSkill/1.0)"
        })
        result["status"] = resp.status_code

        if resp.status_code == 404:
            result["issues"].append("🔴 No robots.txt found — all crawlers allowed by default")
            # Still check AI crawlers
            for crawler in AI_CRAWLERS:
                result["ai_crawler_status"][crawler] = "allowed (no robots.txt)"
            return result

        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code}"
            return result

        result["raw"] = resp.text
        _parse_robots(resp.text, result)

    except requests.exceptions.RequestException as e:
        result["error"] = str(e)

    return result


def _parse_robots(content: str, result: dict):
    """Parse robots.txt content into structured data."""
    current_agents = []

    for line in content.splitlines():
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue

        # Split on first colon
        if ":" not in line:
            continue

        directive, _, value = line.partition(":")
        directive = directive.strip().lower()
        value = value.strip()

        if directive == "user-agent":
            current_agents = [value]
            if value not in result["user_agents"]:
                result["user_agents"][value] = {"allow": [], "disallow": []}

        elif directive == "disallow" and current_agents:
            for agent in current_agents:
                if agent not in result["user_agents"]:
                    result["user_agents"][agent] = {"allow": [], "disallow": []}
                if value:
                    result["user_agents"][agent]["disallow"].append(value)

        elif directive == "allow" and current_agents:
            for agent in current_agents:
                if agent not in result["user_agents"]:
                    result["user_agents"][agent] = {"allow": [], "disallow": []}
                result["user_agents"][agent]["allow"].append(value)

        elif directive == "sitemap":
            result["sitemaps"].append(value)

        elif directive == "crawl-delay" and current_agents:
            for agent in current_agents:
                try:
                    result["crawl_delays"][agent] = float(value)
                except ValueError:
                    pass

    # Analyze AI crawler management
    managed_agents = set(result["user_agents"].keys())

    for crawler in AI_CRAWLERS:
        if crawler in managed_agents:
            rules = result["user_agents"][crawler]
            if rules["disallow"] and "/" in rules["disallow"]:
                result["ai_crawler_status"][crawler] = "fully blocked"
            elif rules["disallow"]:
                result["ai_crawler_status"][crawler] = f"partially blocked ({len(rules['disallow'])} paths)"
            elif rules["allow"]:
                result["ai_crawler_status"][crawler] = "explicitly allowed"
            else:
                result["ai_crawler_status"][crawler] = "declared but no rules"
        else:
            # Check wildcard rules
            if "*" in managed_agents:
                wildcard = result["user_agents"]["*"]
                if wildcard["disallow"] and "/" in wildcard["disallow"]:
                    result["ai_crawler_status"][crawler] = "blocked by wildcard (*)"
                else:
                    result["ai_crawler_status"][crawler] = "not managed (inherits * rules)"
            else:
                result["ai_crawler_status"][crawler] = "not managed (allowed by default)"

    # Generate issues
    unmanaged = [c for c, s in result["ai_crawler_status"].items()
                 if "not managed" in s or "allowed by default" in s]
    if unmanaged:
        result["issues"].append(
            f"⚠️ {len(unmanaged)} AI crawlers not explicitly managed: {', '.join(unmanaged[:5])}"
        )

    if not result["sitemaps"]:
        result["issues"].append("⚠️ No Sitemap directive found in robots.txt")


def main():
    parser = argparse.ArgumentParser(description="Analyze robots.txt for SEO and AI crawlers")
    parser.add_argument("url", help="Website URL or domain")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    result = fetch_robots_txt(args.url)

    if args.json:
        # Exclude raw content from JSON for brevity
        output = {k: v for k, v in result.items() if k != "raw"}
        print(json.dumps(output, indent=2))
        return

    if result["error"]:
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"robots.txt Analysis — {result['url']}")
    print("=" * 50)
    print(f"Status: {result['status']}")

    if result["sitemaps"]:
        print(f"\nSitemaps ({len(result['sitemaps'])}):")
        for sm in result["sitemaps"]:
            print(f"  • {sm}")

    print(f"\nUser-Agents ({len(result['user_agents'])}):")
    for agent, rules in result["user_agents"].items():
        allow_count = len(rules["allow"])
        disallow_count = len(rules["disallow"])
        print(f"  {agent}: {disallow_count} disallow, {allow_count} allow")

    if result["crawl_delays"]:
        print(f"\nCrawl Delays:")
        for agent, delay in result["crawl_delays"].items():
            print(f"  {agent}: {delay}s")

    print(f"\nAI Crawler Management:")
    for crawler, status in result["ai_crawler_status"].items():
        icon = "✅" if "blocked" in status else "⚠️" if "not managed" in status else "ℹ️"
        print(f"  {icon} {crawler}: {status}")

    if result["issues"]:
        print(f"\nIssues ({len(result['issues'])}):")
        for issue in result["issues"]:
            print(f"  {issue}")


if __name__ == "__main__":
    main()

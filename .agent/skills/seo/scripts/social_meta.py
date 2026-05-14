#!/usr/bin/env python3
"""
Validate Open Graph and Twitter Card meta tags.

Checks og:title, og:description, og:image, og:url, twitter:card, etc.
against platform requirements and best practices.

Usage:
    python social_meta.py https://example.com
    python social_meta.py https://example.com --json
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

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 required. Install with: pip install beautifulsoup4")
    sys.exit(1)


HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SEOSkill/1.0)"}

# Required and recommended OG tags
OG_REQUIREMENTS = {
    "og:title": {"required": True, "max_length": 60, "min_length": 10},
    "og:description": {"required": True, "max_length": 200, "min_length": 50},
    "og:image": {"required": True},
    "og:url": {"required": True},
    "og:type": {"required": True},
    "og:site_name": {"required": False},
    "og:locale": {"required": False},
}

# Twitter Card tags
TWITTER_REQUIREMENTS = {
    "twitter:card": {"required": True, "valid_values": ["summary", "summary_large_image", "app", "player"]},
    "twitter:title": {"required": False, "max_length": 70},
    "twitter:description": {"required": False, "max_length": 200},
    "twitter:image": {"required": False},
    "twitter:site": {"required": False},
    "twitter:creator": {"required": False},
}


def check_social_meta(url: str, timeout: int = 15) -> dict:
    """
    Validate social media meta tags for a URL.

    Args:
        url: URL to check
        timeout: Request timeout in seconds

    Returns:
        Dictionary with social meta analysis
    """
    result = {
        "url": url,
        "score": 0,
        "og_tags": {},
        "twitter_tags": {},
        "og_present": [],
        "og_missing": [],
        "twitter_present": [],
        "twitter_missing": [],
        "issues": [],
        "recommendations": [],
        "preview": {
            "title": None,
            "description": None,
            "image": None,
            "site_name": None,
        },
        "error": None,
    }

    try:
        resp = requests.get(url, timeout=timeout, headers=HEADERS)
        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code}"
            return result

        soup = BeautifulSoup(resp.text, "html.parser")
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)
        return result

    total_checks = 0
    passed_checks = 0

    # Extract Open Graph tags
    for meta in soup.find_all("meta"):
        prop = meta.get("property", "")
        name = meta.get("name", "")
        content = meta.get("content", "")

        if prop.startswith("og:"):
            result["og_tags"][prop] = content
        if name.startswith("twitter:") or prop.startswith("twitter:"):
            key = name or prop
            result["twitter_tags"][key] = content

    # Validate OG tags
    for tag, rules in OG_REQUIREMENTS.items():
        total_checks += 1
        value = result["og_tags"].get(tag)

        if value:
            result["og_present"].append(tag)
            passed_checks += 1

            # Check length constraints
            if "max_length" in rules and len(value) > rules["max_length"]:
                result["issues"].append(
                    f"⚠️ {tag} is too long ({len(value)} chars, max {rules['max_length']})"
                )
            if "min_length" in rules and len(value) < rules["min_length"]:
                result["issues"].append(
                    f"⚠️ {tag} is too short ({len(value)} chars, min {rules['min_length']})"
                )

            # Validate og:image
            if tag == "og:image":
                if not value.startswith(("http://", "https://")):
                    result["issues"].append("⚠️ og:image should be an absolute URL")

            # Validate og:url
            if tag == "og:url":
                if not value.startswith(("http://", "https://")):
                    result["issues"].append("⚠️ og:url should be an absolute URL")

        elif rules["required"]:
            result["og_missing"].append(tag)
            result["issues"].append(f"🔴 Missing required: {tag}")

    # Validate Twitter tags
    for tag, rules in TWITTER_REQUIREMENTS.items():
        total_checks += 1
        value = result["twitter_tags"].get(tag)

        if value:
            result["twitter_present"].append(tag)
            passed_checks += 1

            if "valid_values" in rules and value not in rules["valid_values"]:
                result["issues"].append(
                    f"⚠️ {tag} has invalid value '{value}' — "
                    f"valid: {', '.join(rules['valid_values'])}"
                )
            if "max_length" in rules and len(value) > rules["max_length"]:
                result["issues"].append(
                    f"⚠️ {tag} is too long ({len(value)} chars, max {rules['max_length']})"
                )
        elif rules["required"]:
            result["twitter_missing"].append(tag)
            result["issues"].append(f"⚠️ Missing: {tag}")

    # Calculate score
    if total_checks > 0:
        result["score"] = round((passed_checks / total_checks) * 100)

    # Build preview
    result["preview"]["title"] = (
        result["og_tags"].get("og:title") or
        result["twitter_tags"].get("twitter:title") or
        (soup.title.string if soup.title else None)
    )
    result["preview"]["description"] = (
        result["og_tags"].get("og:description") or
        result["twitter_tags"].get("twitter:description")
    )
    result["preview"]["image"] = (
        result["og_tags"].get("og:image") or
        result["twitter_tags"].get("twitter:image")
    )
    result["preview"]["site_name"] = result["og_tags"].get("og:site_name", "")

    # Recommendations
    if not result["og_tags"]:
        result["recommendations"].append(
            "Add Open Graph tags for rich social media previews on Facebook, LinkedIn, etc."
        )
    if not result["twitter_tags"]:
        result["recommendations"].append(
            "Add Twitter Card tags for rich previews on X (Twitter)"
        )
    if result["og_tags"].get("og:image") and not result["og_tags"].get("og:image:width"):
        result["recommendations"].append(
            "Add og:image:width and og:image:height for optimal rendering (1200×630 recommended)"
        )

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate social media meta tags")
    parser.add_argument("url", help="URL to check")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    result = check_social_meta(args.url)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    if result["error"]:
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"Social Meta Tags — {result['url']}")
    print("=" * 50)
    print(f"Score: {result['score']}/100")

    # OG Summary
    print(f"\nOpen Graph ({len(result['og_present'])}/{len(OG_REQUIREMENTS)}):")
    for tag in OG_REQUIREMENTS:
        value = result["og_tags"].get(tag)
        if value:
            display = value[:60] + "..." if len(value) > 60 else value
            print(f"  ✅ {tag}: {display}")
        else:
            req = "required" if OG_REQUIREMENTS[tag]["required"] else "optional"
            icon = "🔴" if req == "required" else "ℹ️"
            print(f"  {icon} {tag}: missing ({req})")

    # Twitter Summary
    print(f"\nTwitter Card ({len(result['twitter_present'])}/{len(TWITTER_REQUIREMENTS)}):")
    for tag in TWITTER_REQUIREMENTS:
        value = result["twitter_tags"].get(tag)
        if value:
            print(f"  ✅ {tag}: {value[:60]}")
        else:
            req = "required" if TWITTER_REQUIREMENTS[tag]["required"] else "optional"
            icon = "⚠️" if req == "required" else "ℹ️"
            print(f"  {icon} {tag}: missing ({req})")

    # Preview
    p = result["preview"]
    if p["title"]:
        print(f"\nSocial Preview:")
        print(f"  Title: {p['title']}")
        print(f"  Description: {(p['description'] or 'None')[:80]}")
        print(f"  Image: {p['image'] or 'None'}")

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

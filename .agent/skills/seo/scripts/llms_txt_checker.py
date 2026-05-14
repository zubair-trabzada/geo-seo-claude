#!/usr/bin/env python3
"""
Check for llms.txt file and validate its format.

llms.txt is a proposed standard for providing LLM-friendly site information.
See: https://llmstxt.org/

Usage:
    python llms_txt_checker.py https://example.com
    python llms_txt_checker.py https://example.com --json
"""

import argparse
import json
import re
import sys

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)


def check_llms_txt(url: str, timeout: int = 15) -> dict:
    """
    Fetch and validate llms.txt from a domain.

    Args:
        url: Website URL or domain
        timeout: Request timeout in seconds

    Returns:
        Dictionary with validation results
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"
        parsed = urlparse(url)

    base = f"{parsed.scheme}://{parsed.netloc}"

    result = {
        "url": f"{base}/llms.txt",
        "full_url": f"{base}/llms-full.txt",
        "exists": False,
        "full_exists": False,
        "status": None,
        "full_status": None,
        "content": None,
        "parsed": {
            "title": None,
            "description": None,
            "sections": [],
            "links": [],
        },
        "quality": {
            "score": 0,
            "issues": [],
            "suggestions": [],
        },
        "error": None,
    }

    headers = {"User-Agent": "Mozilla/5.0 (compatible; SEOSkill/1.0)"}

    # Check llms.txt
    try:
        resp = requests.get(f"{base}/llms.txt", timeout=timeout, headers=headers)
        result["status"] = resp.status_code

        if resp.status_code == 200:
            result["exists"] = True
            result["content"] = resp.text
            _parse_llms_txt(resp.text, result)
            _score_quality(result)
        elif resp.status_code == 404:
            result["quality"]["issues"].append("🔴 No llms.txt found")
            result["quality"]["suggestions"].append(
                "Create /llms.txt with site name, description, and key page links"
            )
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)

    # Check llms-full.txt (optional extended version)
    try:
        resp = requests.get(f"{base}/llms-full.txt", timeout=timeout, headers=headers)
        result["full_status"] = resp.status_code
        result["full_exists"] = resp.status_code == 200
    except requests.exceptions.RequestException:
        pass

    return result


def _parse_llms_txt(content: str, result: dict):
    """Parse llms.txt content into structured data."""
    lines = content.strip().splitlines()

    if not lines:
        result["quality"]["issues"].append("⚠️ llms.txt is empty")
        return

    # First line should be the title (# Title)
    first_line = lines[0].strip()
    if first_line.startswith("# "):
        result["parsed"]["title"] = first_line[2:].strip()
    else:
        result["quality"]["issues"].append("⚠️ First line should be a title (# Site Name)")

    # Look for description (> blockquote)
    current_section = None

    for line in lines[1:]:
        line = line.strip()

        if not line:
            continue

        if line.startswith("> "):
            desc = line[2:].strip()
            if not result["parsed"]["description"]:
                result["parsed"]["description"] = desc
            else:
                result["parsed"]["description"] += " " + desc

        elif line.startswith("## "):
            current_section = line[3:].strip()
            result["parsed"]["sections"].append({
                "name": current_section,
                "links": [],
            })

        elif line.startswith("- ["):
            # Parse markdown links: - [Title](URL): Description
            match = re.match(r'-\s*\[([^\]]+)\]\(([^)]+)\)(?::\s*(.*))?', line)
            if match:
                link = {
                    "title": match.group(1),
                    "url": match.group(2),
                    "description": match.group(3) or "",
                }
                result["parsed"]["links"].append(link)
                if result["parsed"]["sections"]:
                    result["parsed"]["sections"][-1]["links"].append(link)


def _score_quality(result: dict):
    """Score the quality of llms.txt content."""
    score = 0
    parsed = result["parsed"]
    quality = result["quality"]

    # Title present (+20)
    if parsed["title"]:
        score += 20
    else:
        quality["issues"].append("⚠️ Missing title")

    # Description present (+20)
    if parsed["description"]:
        score += 20
        if len(parsed["description"]) < 20:
            quality["issues"].append("⚠️ Description too short")
        elif len(parsed["description"]) > 50:
            score += 5  # Bonus for good description
    else:
        quality["issues"].append("⚠️ Missing description (> blockquote)")
        quality["suggestions"].append("Add a description: > Brief site description")

    # Sections present (+15)
    if parsed["sections"]:
        score += 15
        if len(parsed["sections"]) >= 3:
            score += 5  # Bonus for good organization
    else:
        quality["suggestions"].append("Add sections (## Section Name) to organize content")

    # Links present (+20)
    if parsed["links"]:
        score += 20
        if len(parsed["links"]) >= 5:
            score += 5  # Bonus for comprehensive links
        if len(parsed["links"]) >= 10:
            score += 5
    else:
        quality["issues"].append("⚠️ No links found")
        quality["suggestions"].append("Add key page links: - [Page Title](URL): Description")

    # Content length (+5)
    content_len = len(result["content"] or "")
    if content_len > 200:
        score += 5

    quality["score"] = min(score, 100)


def main():
    parser = argparse.ArgumentParser(description="Check llms.txt for AI search optimization")
    parser.add_argument("url", help="Website URL or domain")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    result = check_llms_txt(args.url)

    if args.json:
        output = {k: v for k, v in result.items() if k != "content"}
        print(json.dumps(output, indent=2))
        return

    if result["error"]:
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"llms.txt Check — {result['url']}")
    print("=" * 50)

    if result["exists"]:
        print(f"Status: ✅ Found (HTTP {result['status']})")
        print(f"Title: {result['parsed']['title'] or 'None'}")
        print(f"Description: {result['parsed']['description'] or 'None'}")
        print(f"Sections: {len(result['parsed']['sections'])}")
        print(f"Links: {len(result['parsed']['links'])}")
        print(f"Quality Score: {result['quality']['score']}/100")
    else:
        print(f"Status: 🔴 Not found (HTTP {result['status']})")

    if result["full_exists"]:
        print(f"\nllms-full.txt: ✅ Found")
    else:
        print(f"\nllms-full.txt: ❌ Not found")

    if result["quality"]["issues"]:
        print(f"\nIssues:")
        for issue in result["quality"]["issues"]:
            print(f"  {issue}")

    if result["quality"]["suggestions"]:
        print(f"\nSuggestions:")
        for sug in result["quality"]["suggestions"]:
            print(f"  💡 {sug}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Hreflang Validator

Validates hreflang implementations against all 8 checks defined in
resources/skills/seo-hreflang.md:

  1. Self-referencing tags
  2. Bidirectional return tags
  3. x-default presence
  4. ISO 639-1 language code format
  5. ISO 3166-1 Alpha-2 region code format
  6. Canonical URL alignment
  7. HTTP/HTTPS protocol consistency
  8. Cross-domain / sitemap-based hreflang detection

Usage:
    python hreflang_checker.py https://example.com/page
    python hreflang_checker.py https://example.com/page --json
    python hreflang_checker.py https://example.com/page --verify-returns
"""

import argparse
import json
import re
import sys
import time
import urllib.request
import urllib.parse
from urllib.parse import urlparse, urljoin

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 required. Install with: pip install beautifulsoup4")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Reference data (ISO 639-1 + ISO 3166-1 Alpha-2)
# ---------------------------------------------------------------------------

# Valid ISO 639-1 two-letter language codes (subset — common + frequently misused)
VALID_LANG_CODES = {
    "af", "sq", "am", "ar", "hy", "as", "az", "eu", "be", "bn", "bs", "bg",
    "ca", "ceb", "zh", "co", "hr", "cs", "da", "nl", "en", "eo", "et", "fi",
    "fr", "fy", "gl", "ka", "de", "el", "gu", "ht", "ha", "haw", "he", "hi",
    "hu", "is", "ig", "id", "ga", "it", "ja", "jv", "kn", "kk", "km", "rw",
    "ko", "ku", "ky", "lo", "la", "lv", "lt", "lb", "mk", "mg", "ms", "ml",
    "mt", "mi", "mr", "mn", "my", "ne", "no", "ny", "or", "ps", "fa", "pl",
    "pt", "pa", "ro", "ru", "sm", "gd", "sr", "st", "sn", "sd", "si", "sk",
    "sl", "so", "es", "su", "sw", "sv", "tl", "tg", "ta", "tt", "te", "th",
    "tr", "tk", "uk", "ur", "ug", "uz", "vi", "cy", "xh", "yi", "yo", "zu",
}

# Common wrong codes and their corrections
COMMON_LANG_MISTAKES = {
    "eng": "en",   # ISO 639-2 (3-letter), not valid for hreflang
    "jp": "ja",    # Wrong code for Japanese
    "zh-cn": "zh-Hans",  # Simplified Chinese region variant gone wrong
    "zh-tw": "zh-Hant",  # Traditional Chinese
    "iw": "he",    # Old code for Hebrew
    "in": "id",    # Old code for Indonesian
}

# Valid ISO 3166-1 Alpha-2 region codes (common ones)
VALID_REGION_CODES = {
    "AF", "AL", "DZ", "AD", "AO", "AG", "AR", "AM", "AU", "AT", "AZ",
    "BS", "BH", "BD", "BB", "BY", "BE", "BZ", "BJ", "BT", "BO", "BA",
    "BW", "BR", "BN", "BG", "BF", "BI", "CV", "KH", "CM", "CA", "CF",
    "TD", "CL", "CN", "CO", "KM", "CG", "CD", "CR", "CI", "HR", "CU",
    "CY", "CZ", "DK", "DJ", "DM", "DO", "EC", "EG", "SV", "GQ", "ER",
    "EE", "SZ", "ET", "FJ", "FI", "FR", "GA", "GM", "GE", "DE", "GH",
    "GR", "GD", "GT", "GN", "GW", "GY", "HT", "HN", "HU", "IS", "IN",
    "ID", "IR", "IQ", "IE", "IL", "IT", "JM", "JP", "JO", "KZ", "KE",
    "KI", "KP", "KR", "KW", "KG", "LA", "LV", "LB", "LS", "LR", "LY",
    "LI", "LT", "LU", "MG", "MW", "MY", "MV", "ML", "MT", "MH", "MR",
    "MU", "MX", "FM", "MD", "MC", "MN", "ME", "MA", "MZ", "MM", "NA",
    "NR", "NP", "NL", "NZ", "NI", "NE", "NG", "NO", "OM", "PK", "PW",
    "PA", "PG", "PY", "PE", "PH", "PL", "PT", "QA", "RO", "RU", "RW",
    "KN", "LC", "VC", "WS", "SM", "ST", "SA", "SN", "RS", "SC", "SL",
    "SG", "SK", "SI", "SB", "SO", "ZA", "SS", "ES", "LK", "SD", "SR",
    "SE", "CH", "SY", "TW", "TJ", "TZ", "TH", "TL", "TG", "TO", "TT",
    "TN", "TR", "TM", "TV", "UG", "UA", "AE", "GB", "US", "UY", "UZ",
    "VU", "VE", "VN", "YE", "ZM", "ZW",
    # Common non-sovereign but valid in context
    "HK", "MO", "PR", "GU", "VI", "AS",
}

# Common region mistakes
COMMON_REGION_MISTAKES = {
    "UK": "GB",   # UK is not a valid ISO 3166-1 code; use GB
    "LA": None,   # Latin America is not a country
    "EU": None,   # European Union is not a country
}

USER_AGENT = "Mozilla/5.0 (compatible; SEOSkill-hreflang/1.0)"


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def fetch_html(url: str, timeout: int = 10) -> tuple[str, str]:
    """Return (html, final_url) after fetching. Returns ('', url) on error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore"), resp.url
    except Exception as exc:
        return "", url


def fetch_robots_txt(base_url: str) -> str:
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    html, _ = fetch_html(robots_url, timeout=6)
    return html


# ---------------------------------------------------------------------------
# Hreflang tag extraction
# ---------------------------------------------------------------------------

def extract_hreflang_from_html(soup: BeautifulSoup, page_url: str) -> list[dict]:
    """
    Extract hreflang tags from <link rel="alternate" hreflang="..."> in <head>.
    Returns list of {lang, url, raw_lang, raw_url}.
    """
    tags = []
    for link in soup.find_all("link", rel="alternate"):
        lang = link.get("hreflang", "").strip()
        href = link.get("href", "").strip()
        if not lang or not href:
            continue
        # Resolve relative URLs
        absolute = urljoin(page_url, href)
        tags.append({
            "lang": lang.lower() if lang != "x-default" else "x-default",
            "raw_lang": lang,
            "url": absolute,
            "raw_url": href,
        })
    return tags


def extract_hreflang_from_http_headers(url: str) -> list[dict]:
    """Check HTTP Link headers for hreflang (used for non-HTML files)."""
    tags = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="HEAD")
        with urllib.request.urlopen(req, timeout=8) as resp:
            link_header = resp.headers.get("Link", "")
            if not link_header:
                return []
            # Parse: <url>; rel="alternate"; hreflang="lang"
            for part in link_header.split(","):
                part = part.strip()
                url_match = re.search(r'<([^>]+)>', part)
                hreflang_match = re.search(r'hreflang="([^"]+)"', part)
                rel_match = re.search(r'rel="([^"]+)"', part)
                if url_match and hreflang_match and rel_match and "alternate" in rel_match.group(1):
                    tags.append({
                        "lang": hreflang_match.group(1).lower(),
                        "raw_lang": hreflang_match.group(1),
                        "url": url_match.group(1),
                        "raw_url": url_match.group(1),
                        "source": "http_header",
                    })
    except Exception:
        pass
    return tags


def check_sitemap_hreflang(base_url: str) -> dict:
    """Check /sitemap.xml for xhtml:link hreflang attributes."""
    parsed = urlparse(base_url)
    sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"
    html, _ = fetch_html(sitemap_url, timeout=8)
    if not html:
        return {"found": False, "url": sitemap_url}

    # Check for xhtml:link in sitemap (hreflang sitemap pattern)
    has_xhtml_link = "xhtml:link" in html or 'rel="alternate"' in html
    lang_matches = re.findall(r'hreflang="([^"]+)"', html)

    return {
        "found": bool(lang_matches),
        "url": sitemap_url,
        "has_xhtml_namespace": "xmlns:xhtml" in html,
        "language_variants_found": list(set(lang_matches)) if lang_matches else [],
        "note": "Sitemap-based hreflang detected." if lang_matches else "No hreflang found in sitemap.",
    }


# ---------------------------------------------------------------------------
# Validation logic (maps 1:1 to seo-hreflang.md checks)
# ---------------------------------------------------------------------------

def validate_lang_code(lang_tag: str) -> dict:
    """
    Validate a single hreflang value (e.g., 'en-US', 'fr', 'x-default').
    Returns {valid, lang, region, issues}.
    """
    if lang_tag == "x-default":
        return {"valid": True, "lang": "x-default", "region": None, "issues": []}

    issues = []
    parts = lang_tag.split("-", 1)
    lang = parts[0].lower()
    region = parts[1].upper() if len(parts) > 1 else None

    # Check for 3-letter ISO 639-2 codes (invalid for hreflang)
    if len(lang) == 3:
        correction = COMMON_LANG_MISTAKES.get(lang)
        issue = f"3-letter language code '{lang}' is not valid for hreflang (ISO 639-1 required)."
        if correction:
            issue += f" Use '{correction}' instead."
        issues.append(issue)
    elif lang not in VALID_LANG_CODES:
        correction = COMMON_LANG_MISTAKES.get(lang)
        issue = f"Unknown language code '{lang}'."
        if correction:
            issue += f" Did you mean '{correction}'?"
        issues.append(issue)

    # Check for ambiguous zh without script qualifier
    if lang == "zh" and region is None:
        issues.append("'zh' is ambiguous — use 'zh-Hans' (Simplified) or 'zh-Hant' (Traditional).")

    # Validate region code
    if region:
        if region in COMMON_REGION_MISTAKES:
            fix = COMMON_REGION_MISTAKES[region]
            if fix:
                issues.append(f"Region '{region}' is not a valid ISO 3166-1 code. Use '{fix}'.")
            else:
                issues.append(f"'{region}' is not a valid ISO 3166-1 country code (supranational regions not supported).")
        elif region not in VALID_REGION_CODES:
            issues.append(f"Unknown region code '{region}' — verify against ISO 3166-1 Alpha-2.")

    return {
        "valid": len(issues) == 0,
        "lang": lang,
        "region": region,
        "issues": issues,
    }


def check_self_reference(tags: list[dict], page_url: str) -> dict:
    """Check 1: Self-referencing tag must be present and URL must match canonical."""
    normalized_page = page_url.rstrip("/")
    for tag in tags:
        tag_url = tag["url"].rstrip("/")
        if tag_url == normalized_page:
            return {"passed": True, "detail": "Self-referencing hreflang tag found."}

    return {
        "passed": False,
        "severity": "Critical",
        "finding": "No self-referencing hreflang tag found.",
        "fix": "Add <link rel=\"alternate\" hreflang=\"{lang}\" href=\"{page_url}\"> pointing to this page's own canonical URL.",
    }


def check_x_default(tags: list[dict]) -> dict:
    """Check 3: x-default tag presence."""
    x_defaults = [t for t in tags if t["lang"] == "x-default"]
    if not x_defaults:
        return {
            "passed": False,
            "severity": "High",
            "finding": "No x-default hreflang tag found.",
            "fix": "Add <link rel=\"alternate\" hreflang=\"x-default\" href=\"{fallback_url}\"> pointing to your language selector or primary language version.",
        }
    if len(x_defaults) > 1:
        return {
            "passed": False,
            "severity": "High",
            "finding": f"Multiple x-default tags found ({len(x_defaults)}). Only one is allowed.",
            "fix": "Remove duplicate x-default tags. Keep only one pointing to the language selector or primary version.",
        }
    return {"passed": True, "detail": f"x-default present → {x_defaults[0]['url']}"}


def check_protocol_consistency(tags: list[dict]) -> dict:
    """Check 7: All URLs in the hreflang set must use the same protocol."""
    protocols = {urlparse(t["url"]).scheme for t in tags if t["url"]}
    if len(protocols) > 1:
        return {
            "passed": False,
            "severity": "Medium",
            "finding": f"Mixed protocols in hreflang set: {', '.join(sorted(protocols))}.",
            "fix": "Standardize all hreflang URLs to HTTPS. Update any remaining HTTP URLs.",
        }
    return {"passed": True, "detail": f"All hreflang URLs use: {list(protocols)[0] if protocols else 'unknown'}"}


def check_lang_codes(tags: list[dict]) -> list[dict]:
    """Checks 4 & 5: Validate each language/region code."""
    issues = []
    for tag in tags:
        if tag["lang"] == "x-default":
            continue
        validation = validate_lang_code(tag["raw_lang"])
        if not validation["valid"]:
            for issue_text in validation["issues"]:
                issues.append({
                    "passed": False,
                    "severity": "High",
                    "lang_tag": tag["raw_lang"],
                    "url": tag["url"],
                    "finding": issue_text,
                    "fix": "Fix the language/region code to use ISO 639-1 + ISO 3166-1 Alpha-2 format.",
                })
    return issues


def check_return_tags(
    tags: list[dict],
    page_url: str,
    verify_remote: bool = False,
    timeout: int = 8,
) -> list[dict]:
    """
    Check 2: Bidirectional return tags.
    If verify_remote=True, fetches each alternate URL and checks for a reciprocal tag.
    Without remote fetch, returns Hypothesis-confidence findings.
    """
    issues = []
    non_self = [t for t in tags if t["url"].rstrip("/") != page_url.rstrip("/")
                and t["lang"] != "x-default"]

    if not non_self:
        return []

    if not verify_remote:
        issues.append({
            "passed": None,  # Cannot confirm without fetching
            "severity": "Info",
            "confidence": "Hypothesis",
            "finding": f"Found {len(non_self)} alternate URL(s). Return tag verification requires --verify-returns flag.",
            "fix": "Run with --verify-returns to fetch each alternate and confirm bidirectional hreflang.",
            "alternates": [t["url"] for t in non_self],
        })
        return issues

    # Remote verification
    for alt_tag in non_self:
        alt_url = alt_tag["url"]
        time.sleep(0.5)  # polite crawl delay
        alt_html, _ = fetch_html(alt_url, timeout=timeout)
        if not alt_html:
            issues.append({
                "passed": None,
                "confidence": "Hypothesis",
                "severity": "Info",
                "finding": f"Could not fetch alternate URL to verify return tag: {alt_url}",
                "fix": "Manually verify that this page links back to the source page with hreflang.",
            })
            continue

        alt_soup = BeautifulSoup(alt_html, "html.parser")
        alt_tags = extract_hreflang_from_html(alt_soup, alt_url)
        returns_to_source = any(
            t["url"].rstrip("/") == page_url.rstrip("/") for t in alt_tags
        )

        if not returns_to_source:
            issues.append({
                "passed": False,
                "confidence": "Confirmed",
                "severity": "Critical",
                "lang_tag": alt_tag["lang"],
                "finding": f"Missing return tag on {alt_url} — no hreflang pointing back to {page_url}.",
                "fix": f"Add hreflang tag on {alt_url} that references {page_url}.",
            })
        else:
            issues.append({
                "passed": True,
                "confidence": "Confirmed",
                "lang_tag": alt_tag["lang"],
                "finding": f"Return tag confirmed on {alt_url}",
            })

    return issues


def check_canonical_alignment(soup: BeautifulSoup, tags: list[dict], page_url: str) -> dict:
    """
    Check 6: Hreflang tags should only appear on canonical URLs.
    Warns if a canonical tag points elsewhere, invalidating the hreflang set.
    """
    canonical_tag = soup.find("link", rel="canonical")
    if not canonical_tag:
        return {"passed": None, "confidence": "Hypothesis",
                "finding": "No canonical tag found — cannot verify hreflang/canonical alignment.",
                "fix": "Add a self-referencing canonical tag to confirm this is the canonical URL."}

    canonical_url = canonical_tag.get("href", "").strip()
    if canonical_url and canonical_url.rstrip("/") != page_url.rstrip("/"):
        return {
            "passed": False,
            "severity": "High",
            "confidence": "Confirmed",
            "finding": f"Canonical tag points to a different URL ({canonical_url}). Hreflang on non-canonical pages is ignored by Google.",
            "fix": "Remove hreflang tags from this page OR move them to the canonical URL.",
        }

    return {"passed": True, "detail": f"Canonical URL matches page URL: {canonical_url}"}


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_hreflang_check(url: str, verify_returns: bool = False) -> dict:
    """Run all 8 hreflang checks and return a structured report."""
    html, final_url = fetch_html(url)
    if not html:
        return {"error": f"Failed to fetch URL: {url}", "url": url}

    soup = BeautifulSoup(html, "html.parser")
    tags = extract_hreflang_from_html(soup, final_url)

    # Also check HTTP headers (Check 8 — alternative implementation method)
    http_header_tags = extract_hreflang_from_http_headers(final_url)
    implementation_method = "none"
    if tags:
        implementation_method = "html_link_tags"
    elif http_header_tags:
        tags = http_header_tags
        implementation_method = "http_headers"

    # Check sitemap hreflang (Check 8)
    sitemap_info = check_sitemap_hreflang(final_url)
    if sitemap_info["found"] and implementation_method == "none":
        implementation_method = "xml_sitemap"

    results = {
        "url": final_url,
        "implementation_method": implementation_method,
        "hreflang_tags_found": len(tags),
        "tags": tags,
        "sitemap": sitemap_info,
        "checks": {},
        "language_code_issues": [],
        "return_tag_checks": [],
        "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0, "passed": 0},
    }

    if not tags:
        results["checks"]["hreflang_present"] = {
            "passed": False,
            "severity": "Info",
            "finding": "No hreflang tags found (HTML, HTTP headers, or sitemap).",
            "fix": "If this is a single-language site, hreflang is not needed. For multi-language sites, implement hreflang via HTML link tags or sitemap.",
        }
        return results

    # Check 1 — Self-reference
    results["checks"]["self_reference"] = check_self_reference(tags, final_url)

    # Check 3 — x-default
    results["checks"]["x_default"] = check_x_default(tags)

    # Check 7 — Protocol consistency
    results["checks"]["protocol_consistency"] = check_protocol_consistency(tags)

    # Check 6 — Canonical alignment
    results["checks"]["canonical_alignment"] = check_canonical_alignment(soup, tags, final_url)

    # Checks 4 & 5 — Language/region code validation
    results["language_code_issues"] = check_lang_codes(tags)

    # Check 2 — Return tags (bidirectional)
    results["return_tag_checks"] = check_return_tags(tags, final_url, verify_remote=verify_returns)

    # Tally summary
    sev_map = {"Critical": "critical", "High": "high", "Medium": "medium", "Low": "low"}
    for check in results["checks"].values():
        if check.get("passed") is True:
            results["summary"]["passed"] += 1
        elif check.get("passed") is False:
            sev = check.get("severity", "low")
            results["summary"][sev_map.get(sev, "low")] += 1

    for issue in results["language_code_issues"] + results["return_tag_checks"]:
        if issue.get("passed") is False:
            sev = issue.get("severity", "low")
            results["summary"][sev_map.get(sev, "low")] += 1

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Hreflang Validator — checks all 8 rules from seo-hreflang.md"
    )
    parser.add_argument("url", help="Page URL to validate")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--verify-returns",
        action="store_true",
        help="Fetch each alternate URL to verify bidirectional return tags (slower, makes HTTP requests)",
    )
    args = parser.parse_args()

    report = run_hreflang_check(args.url, verify_returns=args.verify_returns)

    if args.json:
        print(json.dumps(report, indent=2))
        return

    if report.get("error"):
        print(f"Error: {report['error']}")
        sys.exit(1)

    print(f"\nHreflang Validation — {report['url']}")
    print("=" * 60)
    print(f"Implementation Method : {report['implementation_method']}")
    print(f"Tags Found            : {report['hreflang_tags_found']}")

    if report["tags"]:
        print("\nDetected Alternates:")
        for tag in report["tags"]:
            validation = validate_lang_code(tag["raw_lang"])
            status = "✅" if validation["valid"] or tag["lang"] == "x-default" else "❌"
            print(f"  {status} [{tag['raw_lang']:12}] {tag['url']}")

    print(f"\nSitemap Hreflang : {'Found' if report['sitemap']['found'] else 'Not found'}")
    if report["sitemap"]["found"]:
        print(f"  Variants: {', '.join(report['sitemap']['language_variants_found'])}")

    print("\nValidation Results:")
    sev_icon = {"Critical": "🔴", "High": "🟠", "Medium": "⚠️", "Low": "ℹ️", "Info": "ℹ️"}

    for name, check in report["checks"].items():
        if check.get("passed") is True:
            print(f"  ✅ {name.replace('_', ' ').title()}: {check.get('detail', 'Pass')}")
        elif check.get("passed") is False:
            icon = sev_icon.get(check.get("severity", "Low"), "⚠️")
            print(f"  {icon} {name.replace('_', ' ').title()}: {check.get('finding', '')}")
            print(f"       Fix: {check.get('fix', '')}")
        else:
            print(f"  ℹ️  {name.replace('_', ' ').title()}: {check.get('finding', '')} (Confidence: {check.get('confidence', 'Hypothesis')})")

    if report["language_code_issues"]:
        print("\nLanguage/Region Code Issues:")
        for issue in report["language_code_issues"]:
            icon = sev_icon.get(issue.get("severity", "High"), "🟠")
            print(f"  {icon} [{issue['lang_tag']}] {issue['finding']}")

    if report["return_tag_checks"]:
        print("\nReturn Tag Checks:")
        for check in report["return_tag_checks"]:
            if check.get("passed") is True:
                print(f"  ✅ [{check.get('lang_tag', '')}] {check['finding']}")
            elif check.get("passed") is False:
                icon = sev_icon.get(check.get("severity", "Critical"), "🔴")
                print(f"  {icon} [{check.get('lang_tag', '')}] {check['finding']}")
            else:
                print(f"  ℹ️  {check['finding']}")

    s = report["summary"]
    total_issues = s["critical"] + s["high"] + s["medium"] + s["low"]
    print(f"\nSummary: {s['passed']} passed, {total_issues} issues")
    print(f"  🔴 Critical: {s['critical']}  🟠 High: {s['high']}  ⚠️ Medium: {s['medium']}  ℹ️ Low: {s['low']}")

    if not args.verify_returns and report["hreflang_tags_found"] > 1:
        print("\nTip: Run with --verify-returns to fetch each alternate URL and confirm bidirectional return tags.")


if __name__ == "__main__":
    main()

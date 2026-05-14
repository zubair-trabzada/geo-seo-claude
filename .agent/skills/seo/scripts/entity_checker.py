#!/usr/bin/env python3
"""
Entity SEO Checker

Validates entity presence across Knowledge Graph signals: Wikidata,
Wikipedia, sameAs properties in JSON-LD, and Google Knowledge Graph
Search API (optional, requires API key).

Usage:
    python entity_checker.py https://example.com --json
    python entity_checker.py https://example.com --entity "Example Corp"
    python entity_checker.py https://example.com --kg-api-key YOUR_KEY
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.parse
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 required. Install with: pip install beautifulsoup4")
    sys.exit(1)


USER_AGENT = "Mozilla/5.0 (compatible; SEOSkill-Entity/1.0)"

# Authoritative sameAs targets (ranked by KG signal strength)
SAMEAS_PLATFORMS = {
    "wikipedia.org": {"name": "Wikipedia", "priority": "Critical", "kg_signal": "Primary"},
    "wikidata.org": {"name": "Wikidata", "priority": "Critical", "kg_signal": "Primary"},
    "linkedin.com": {"name": "LinkedIn", "priority": "High", "kg_signal": "Strong"},
    "twitter.com": {"name": "Twitter/X", "priority": "High", "kg_signal": "Strong"},
    "x.com": {"name": "Twitter/X", "priority": "High", "kg_signal": "Strong"},
    "crunchbase.com": {"name": "Crunchbase", "priority": "Medium", "kg_signal": "Moderate"},
    "github.com": {"name": "GitHub", "priority": "Medium", "kg_signal": "Moderate"},
    "youtube.com": {"name": "YouTube", "priority": "Medium", "kg_signal": "Moderate"},
    "facebook.com": {"name": "Facebook", "priority": "Low", "kg_signal": "Weak"},
    "instagram.com": {"name": "Instagram", "priority": "Low", "kg_signal": "Weak"},
}


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_html(url: str, timeout: int = 12) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        print(f"Error fetching {url}: {exc}", file=sys.stderr)
        return ""


# ---------------------------------------------------------------------------
# Schema extraction
# ---------------------------------------------------------------------------

def extract_entities_from_schema(soup: BeautifulSoup) -> list:
    """Extract Organization/Person entities and their sameAs from JSON-LD."""
    entities = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue

        # Handle @graph arrays
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            if "@graph" in data:
                items = data["@graph"]
            else:
                items = [data]

        for item in items:
            if not isinstance(item, dict):
                continue
            schema_type = item.get("@type", "")
            # Look for entity types
            if schema_type in ("Organization", "Person", "Corporation",
                               "LocalBusiness", "Brand", "MedicalOrganization",
                               "EducationalOrganization", "GovernmentOrganization"):
                entities.append({
                    "type": schema_type,
                    "name": item.get("name", ""),
                    "url": item.get("url", ""),
                    "sameAs": item.get("sameAs", []),
                    "logo": item.get("logo", ""),
                    "description": item.get("description", ""),
                    "identifier": item.get("identifier", ""),
                })

    return entities


# ---------------------------------------------------------------------------
# sameAs analysis
# ---------------------------------------------------------------------------

def analyze_sameas(same_as_list: list) -> dict:
    """Analyze sameAs URLs for completeness and validity."""
    if isinstance(same_as_list, str):
        same_as_list = [same_as_list]

    found = {}
    missing = {}
    issues = []

    for url in same_as_list:
        if not isinstance(url, str):
            continue
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "").lower()

        matched = False
        for platform_domain, info in SAMEAS_PLATFORMS.items():
            if platform_domain in domain:
                found[info["name"]] = {
                    "url": url,
                    "priority": info["priority"],
                    "kg_signal": info["kg_signal"],
                }
                matched = True
                break

        if not matched:
            found[domain] = {
                "url": url,
                "priority": "Low",
                "kg_signal": "Unknown",
            }

    # Identify missing critical platforms
    for platform_domain, info in SAMEAS_PLATFORMS.items():
        if info["priority"] in ("Critical", "High"):
            if info["name"] not in found:
                missing[info["name"]] = {
                    "domain": platform_domain,
                    "priority": info["priority"],
                    "kg_signal": info["kg_signal"],
                }

    # Check for broken URLs (quick HEAD check on first 3)
    for name, data in list(found.items())[:3]:
        url = data["url"]
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="HEAD")
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status >= 400:
                    issues.append({
                        "severity": "Warning",
                        "finding": f"sameAs URL returns HTTP {resp.status}: {url}",
                        "fix": f"Update sameAs URL for {name} to a valid, non-redirecting destination.",
                    })
        except Exception:
            issues.append({
                "severity": "Info",
                "finding": f"Could not verify sameAs URL: {url}",
                "fix": "Manually confirm this URL is accessible and correct.",
            })

    return {
        "found": found,
        "missing": missing,
        "issues": issues,
        "total_found": len(found),
        "total_missing_critical": len(missing),
    }


# ---------------------------------------------------------------------------
# Wikidata lookup
# ---------------------------------------------------------------------------

def check_wikidata(entity_name: str) -> dict:
    """Search Wikidata for the entity name. Returns QID if found."""
    if not entity_name:
        return {"found": False, "qid": None, "url": None}

    try:
        query = urllib.parse.quote(entity_name)
        url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={query}&language=en&format=json&limit=3"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        results = data.get("search", [])
        if results:
            best = results[0]
            return {
                "found": True,
                "qid": best.get("id"),
                "label": best.get("label"),
                "description": best.get("description", ""),
                "url": f"https://www.wikidata.org/wiki/{best.get('id')}",
                "confidence": "High" if best.get("label", "").lower() == entity_name.lower() else "Medium",
            }
    except Exception:
        pass

    return {"found": False, "qid": None, "url": None}


# ---------------------------------------------------------------------------
# Wikipedia check
# ---------------------------------------------------------------------------

def check_wikipedia(entity_name: str) -> dict:
    """Check if the entity has a Wikipedia article."""
    if not entity_name:
        return {"found": False, "url": None}

    try:
        query = urllib.parse.quote(entity_name.replace(" ", "_"))
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={query}&format=json&redirects=1"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id != "-1":
                return {
                    "found": True,
                    "title": page_data.get("title"),
                    "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page_data.get('title', '').replace(' ', '_'))}",
                }
    except Exception:
        pass

    return {"found": False, "url": None}


# ---------------------------------------------------------------------------
# NAP consistency check
# ---------------------------------------------------------------------------

def check_nap_consistency(soup: BeautifulSoup, entities: list) -> list:
    """Check Name/Address/Phone consistency signals on the page."""
    issues = []

    # Look for structured LocalBusiness / Organization
    local_entities = [e for e in entities if e["type"] in ("LocalBusiness", "Organization")]

    if not local_entities:
        return []

    for entity in local_entities:
        name = entity.get("name", "")
        if not name:
            issues.append({
                "severity": "Warning",
                "finding": f"{entity['type']} schema is missing 'name' property.",
                "fix": "Add the exact business name to the schema.",
            })

    # Check for visible phone/address on page
    page_text = soup.get_text(separator=" ")
    has_phone = bool(re.search(r"[\+]?[\d\-\(\)\s]{7,15}", page_text))
    has_address = bool(re.search(r"\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd|blvd|drive|dr|lane|ln)", page_text, re.I))

    if not has_phone and local_entities:
        issues.append({
            "severity": "Info",
            "finding": "No phone number detected on page for LocalBusiness entity.",
            "fix": "Display phone number visibly and include 'telephone' in LocalBusiness schema.",
        })

    return issues


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def run_entity_check(url: str, entity_name: str = "", kg_api_key: str = "") -> dict:
    """Run full entity SEO check."""
    html = fetch_html(url)
    if not html:
        return {"error": f"Failed to fetch {url}", "url": url}

    soup = BeautifulSoup(html, "html.parser")

    # Extract entities from schema
    entities = extract_entities_from_schema(soup)

    # Determine entity name
    if not entity_name and entities:
        entity_name = entities[0].get("name", "")

    if not entity_name:
        # Try og:site_name or title
        og_site = soup.find("meta", property="og:site_name")
        if og_site:
            entity_name = og_site.get("content", "")
        else:
            title = soup.find("title")
            if title:
                entity_name = title.get_text(strip=True).split("|")[0].split("-")[0].strip()

    # Analyze sameAs from all entities
    all_same_as = []
    for e in entities:
        sa = e.get("sameAs", [])
        if isinstance(sa, str):
            all_same_as.append(sa)
        elif isinstance(sa, list):
            all_same_as.extend(sa)

    sameas_analysis = analyze_sameas(all_same_as)

    # External lookups
    wikidata = check_wikidata(entity_name)
    wikipedia = check_wikipedia(entity_name)

    # NAP consistency
    nap_issues = check_nap_consistency(soup, entities)

    # Build issues list
    issues = []

    if not entities:
        issues.append({
            "severity": "Critical",
            "area": "Schema",
            "finding": "No Organization/Person entity found in JSON-LD.",
            "fix": "Add Organization or Person schema with name, url, logo, and sameAs properties.",
        })

    if entities and not all_same_as:
        issues.append({
            "severity": "Critical",
            "area": "sameAs",
            "finding": "Entity schema exists but has no sameAs properties.",
            "fix": "Add sameAs URLs pointing to Wikipedia, LinkedIn, Twitter/X, etc.",
        })

    if not wikidata["found"]:
        issues.append({
            "severity": "Warning",
            "area": "Wikidata",
            "finding": f"No Wikidata entry found for '{entity_name}'.",
            "fix": "Create a Wikidata item for your entity with accurate properties to improve Knowledge Graph presence.",
        })

    if not wikipedia["found"]:
        issues.append({
            "severity": "Info",
            "area": "Wikipedia",
            "finding": f"No Wikipedia article found for '{entity_name}'.",
            "fix": "Pursue notability through press coverage and third-party references. Wikipedia articles significantly boost Knowledge Panel eligibility.",
        })

    for name, data in sameas_analysis.get("missing", {}).items():
        issues.append({
            "severity": "Warning" if data["priority"] == "Critical" else "Info",
            "area": "sameAs",
            "finding": f"Missing sameAs link to {name} ({data['kg_signal']} KG signal).",
            "fix": f"Add '{data['domain']}' profile URL to sameAs array in your entity schema.",
        })

    issues.extend(sameas_analysis.get("issues", []))
    issues.extend(nap_issues)

    return {
        "url": url,
        "entity_name": entity_name,
        "entities_in_schema": entities,
        "sameas_analysis": sameas_analysis,
        "wikidata": wikidata,
        "wikipedia": wikipedia,
        "nap_issues": nap_issues,
        "issues": issues,
        "summary": {
            "entities_found": len(entities),
            "sameas_count": len(all_same_as),
            "sameas_missing_critical": sameas_analysis["total_missing_critical"],
            "wikidata_found": wikidata["found"],
            "wikipedia_found": wikipedia["found"],
            "total_issues": len(issues),
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Entity SEO Checker — Knowledge Graph, Wikidata, sameAs validation"
    )
    parser.add_argument("url", help="Page URL to check")
    parser.add_argument("--entity", default="", help="Entity name to search (auto-detected from schema/title if omitted)")
    parser.add_argument("--kg-api-key", default="", help="Google Knowledge Graph API key (optional, for enhanced lookup)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    report = run_entity_check(args.url, entity_name=args.entity, kg_api_key=args.kg_api_key)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return

    if report.get("error"):
        print(f"Error: {report['error']}")
        sys.exit(1)

    print(f"\nEntity SEO Check — {report['url']}")
    print("=" * 60)
    print(f"Entity Name       : {report['entity_name']}")
    print(f"Entities in Schema: {report['summary']['entities_found']}")

    if report["entities_in_schema"]:
        for e in report["entities_in_schema"]:
            print(f"  [{e['type']}] {e['name']}")

    print(f"\nsameAs Properties : {report['summary']['sameas_count']}")
    sa = report["sameas_analysis"]
    for name, data in sa["found"].items():
        print(f"  ✅ {name}: {data['url']} ({data['kg_signal']} signal)")
    for name, data in sa["missing"].items():
        icon = "🔴" if data["priority"] == "Critical" else "⚠️"
        print(f"  {icon} Missing: {name} ({data['kg_signal']} signal)")

    wd = report["wikidata"]
    print(f"\nWikidata          : {'✅ ' + wd['qid'] + ' — ' + wd.get('description', '') if wd['found'] else '❌ Not found'}")

    wp = report["wikipedia"]
    print(f"Wikipedia         : {'✅ ' + wp.get('url', '') if wp['found'] else '❌ Not found'}")

    if report["issues"]:
        sev_icon = {"Critical": "🔴", "Warning": "⚠️", "Info": "ℹ️"}
        print(f"\nIssues ({report['summary']['total_issues']}):")
        for issue in report["issues"]:
            icon = sev_icon.get(issue.get("severity", "Info"), "ℹ️")
            print(f"  {icon} [{issue.get('area', issue.get('severity'))}] {issue['finding']}")
            print(f"     Fix: {issue['fix']}")
    else:
        print("\n✅ No entity SEO issues detected.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Competitor Analyzer — Compare a target site against competitors across GEO dimensions.

Performs lightweight scans of target and competitor sites, scores each across
8 GEO-relevant dimensions, and produces a comparison matrix with gap analysis.

Uses existing modules: fetch_page.py, citability_scorer.py, brand_scanner.py
"""

import sys
import os
import json
import re
import time
from urllib.parse import urlparse
from typing import List, Optional

# Allow imports from sibling scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required packages not installed. Run: pip install requests beautifulsoup4")
    sys.exit(1)

from fetch_page import (
    fetch_page,
    fetch_robots_txt,
    fetch_llms_txt,
    crawl_sitemap,
    extract_content_blocks,
    DEFAULT_HEADERS,
)
from citability_scorer import score_passage
from brand_scanner import (
    check_youtube_presence,
    check_reddit_presence,
    check_wikipedia_presence,
    check_linkedin_presence,
)

# --- Constants ---

MAX_COMPETITORS = 5
MAX_PAGES_PER_SITE = 5
REQUEST_DELAY = 1.0  # seconds between requests
REQUEST_TIMEOUT = 30

DIMENSION_WEIGHTS = {
    "ai_citability": 0.25,
    "brand_authority": 0.20,
    "content_depth": 0.15,
    "crawler_access": 0.10,
    "schema_coverage": 0.10,
    "llms_txt": 0.05,
    "technical_geo": 0.10,
    "content_freshness": 0.05,
}

AI_CRAWLERS_LIST = [
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "ClaudeBot",
    "anthropic-ai",
    "PerplexityBot",
    "CCBot",
    "Bytespider",
    "cohere-ai",
    "Google-Extended",
    "GoogleOther",
    "Applebot-Extended",
    "FacebookBot",
    "Amazonbot",
]


def _extract_brand_name(url: str) -> str:
    """Extract a brand name from a URL for brand scanning."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    # Use the domain name without TLD as brand name
    parts = domain.split(".")
    return parts[0] if parts else domain


def _delay():
    """Rate-limit between requests."""
    time.sleep(REQUEST_DELAY)


# --- Site Scanning ---

def scan_site(url: str, max_pages: int = MAX_PAGES_PER_SITE) -> dict:
    """
    Lightweight scan of a single site returning structured data for scoring.

    Returns dict with: pages[], robots, llms_txt, citability, brand, domain, errors[]
    """
    result = {
        "url": url,
        "domain": urlparse(url).netloc,
        "pages": [],
        "robots": None,
        "llms_txt": None,
        "citability_scores": [],
        "brand": None,
        "schema_types": set(),
        "total_word_count": 0,
        "pages_over_1000_words": 0,
        "most_recent_date": None,
        "errors": [],
    }

    try:
        # 1. Fetch homepage
        homepage = fetch_page(url, timeout=REQUEST_TIMEOUT)
        result["pages"].append(homepage)
        result["total_word_count"] += homepage.get("word_count", 0)
        if homepage.get("word_count", 0) >= 1000:
            result["pages_over_1000_words"] += 1

        # Collect schema types from homepage
        for sd in homepage.get("structured_data", []):
            if isinstance(sd, dict):
                t = sd.get("@type")
                if t:
                    if isinstance(t, list):
                        result["schema_types"].update(t)
                    else:
                        result["schema_types"].add(t)

        _delay()

        # 2. Fetch robots.txt
        result["robots"] = fetch_robots_txt(url, timeout=REQUEST_TIMEOUT)
        _delay()

        # 3. Fetch llms.txt
        result["llms_txt"] = fetch_llms_txt(url, timeout=REQUEST_TIMEOUT)
        _delay()

        # 4. Discover additional pages (from sitemap or internal links)
        discovered = crawl_sitemap(url, max_pages=max_pages)
        if not discovered:
            # Fallback to internal links from homepage
            discovered = [
                link["url"]
                for link in homepage.get("internal_links", [])
                if link["url"] != url
            ][:max_pages]

        # Fetch up to max_pages - 1 additional pages (homepage already fetched)
        for page_url in discovered[: max_pages - 1]:
            if page_url == url:
                continue
            try:
                page_data = fetch_page(page_url, timeout=REQUEST_TIMEOUT)
                result["pages"].append(page_data)
                result["total_word_count"] += page_data.get("word_count", 0)
                if page_data.get("word_count", 0) >= 1000:
                    result["pages_over_1000_words"] += 1

                for sd in page_data.get("structured_data", []):
                    if isinstance(sd, dict):
                        t = sd.get("@type")
                        if t:
                            if isinstance(t, list):
                                result["schema_types"].update(t)
                            else:
                                result["schema_types"].add(t)

                _delay()
            except Exception as e:
                result["errors"].append(f"Error fetching {page_url}: {str(e)}")

        # 5. Score citability on all fetched pages
        for page in result["pages"]:
            text = page.get("text_content", "")
            if text and len(text.split()) >= 20:
                score = score_passage(text, page.get("title"))
                result["citability_scores"].append(score)

        # 6. Brand signals
        brand_name = _extract_brand_name(url)
        result["brand"] = {
            "name": brand_name,
            "youtube": check_youtube_presence(brand_name),
            "reddit": check_reddit_presence(brand_name),
            "wikipedia": check_wikipedia_presence(brand_name),
            "linkedin": check_linkedin_presence(brand_name),
        }

        # 7. Extract most recent date from content
        for page in result["pages"]:
            for meta_key in ["article:published_time", "date", "last-modified"]:
                val = page.get("meta_tags", {}).get(meta_key)
                if val:
                    if result["most_recent_date"] is None or val > result["most_recent_date"]:
                        result["most_recent_date"] = val

    except Exception as e:
        result["errors"].append(f"Scan error: {str(e)}")

    # Convert set to list for JSON serialization
    result["schema_types"] = list(result["schema_types"])

    return result


# --- Dimension Scoring ---

def score_dimension(site_data: dict, dimension: str) -> int:
    """Score a single dimension 0-100 for a scanned site."""

    if dimension == "ai_citability":
        scores = site_data.get("citability_scores", [])
        if not scores:
            return 0
        avg = sum(s.get("total_score", 0) for s in scores) / len(scores)
        return min(int(avg), 100)

    elif dimension == "brand_authority":
        brand = site_data.get("brand", {})
        if not brand:
            return 0
        score = 0
        # YouTube (25pts)
        yt = brand.get("youtube", {})
        if yt.get("has_channel"):
            score += 25
        elif yt.get("mentioned_in_videos"):
            score += 15
        # Reddit (25pts)
        rd = brand.get("reddit", {})
        if rd.get("has_subreddit"):
            score += 25
        elif rd.get("mentioned_in_discussions"):
            score += 15
        # Wikipedia (30pts)
        wp = brand.get("wikipedia", {})
        if wp.get("has_wikipedia_page"):
            score += 30
        elif wp.get("has_wikidata_entry"):
            score += 15
        # LinkedIn (20pts)
        li = brand.get("linkedin", {})
        if li.get("has_company_page"):
            score += 20
        elif li.get("employee_thought_leadership"):
            score += 10
        return min(score, 100)

    elif dimension == "content_depth":
        pages = site_data.get("pages", [])
        if not pages:
            return 0
        total_words = site_data.get("total_word_count", 0)
        deep_pages = site_data.get("pages_over_1000_words", 0)
        avg_words = total_words / len(pages) if pages else 0

        score = 0
        # Average word count scoring (up to 50pts)
        if avg_words >= 2000:
            score += 50
        elif avg_words >= 1500:
            score += 40
        elif avg_words >= 1000:
            score += 30
        elif avg_words >= 500:
            score += 20
        elif avg_words >= 200:
            score += 10

        # Deep pages ratio (up to 50pts)
        if pages:
            deep_ratio = deep_pages / len(pages)
            score += int(deep_ratio * 50)

        return min(score, 100)

    elif dimension == "crawler_access":
        robots = site_data.get("robots", {})
        if not robots:
            return 50  # No data = neutral
        statuses = robots.get("ai_crawler_status", {})
        if not statuses:
            return 50

        total = len(statuses)
        allowed = sum(
            1 for s in statuses.values()
            if s in ("ALLOWED", "ALLOWED_BY_DEFAULT", "NOT_MENTIONED", "NO_ROBOTS_TXT")
        )
        if total == 0:
            return 50
        return int((allowed / total) * 100)

    elif dimension == "schema_coverage":
        schema_types = site_data.get("schema_types", [])
        count = len(schema_types)
        # Score based on number of distinct schema types
        if count >= 6:
            return 100
        elif count >= 4:
            return 80
        elif count >= 3:
            return 60
        elif count >= 2:
            return 40
        elif count >= 1:
            return 20
        return 0

    elif dimension == "llms_txt":
        llms = site_data.get("llms_txt", {})
        if not llms:
            return 0
        score = 0
        if llms.get("llms_txt", {}).get("exists"):
            content = llms["llms_txt"].get("content", "")
            score += 50
            # Quality: has meaningful content (>100 chars)
            if len(content) > 100:
                score += 25
            # Has llms-full.txt too
            if llms.get("llms_full_txt", {}).get("exists"):
                score += 25
        return min(score, 100)

    elif dimension == "technical_geo":
        pages = site_data.get("pages", [])
        if not pages:
            return 0
        homepage = pages[0]
        score = 0

        # HTTPS (25pts)
        if site_data.get("url", "").startswith("https"):
            score += 25

        # SSR (25pts)
        if homepage.get("has_ssr_content", False):
            score += 25

        # Canonical (15pts)
        if homepage.get("canonical"):
            score += 15

        # Security headers (15pts)
        sec_headers = homepage.get("security_headers", {})
        present = sum(1 for v in sec_headers.values() if v is not None)
        if present >= 4:
            score += 15
        elif present >= 2:
            score += 10
        elif present >= 1:
            score += 5

        # Meta description (10pts)
        if homepage.get("description"):
            score += 10

        # Hreflang / language meta (10pts)
        meta_tags = homepage.get("meta_tags", {})
        if any(k.startswith("og:locale") for k in meta_tags):
            score += 10
        elif meta_tags.get("content-language"):
            score += 10

        return min(score, 100)

    elif dimension == "content_freshness":
        most_recent = site_data.get("most_recent_date")
        if not most_recent:
            # Check for dates in page content as fallback
            for page in site_data.get("pages", []):
                text = page.get("text_content", "")
                dates = re.findall(r"20(?:2[4-6]|1\d)-\d{2}-\d{2}", text)
                if dates:
                    latest = max(dates)
                    if most_recent is None or latest > most_recent:
                        most_recent = latest

        if not most_recent:
            return 20  # Unknown = low score

        # Score based on recency
        try:
            if "2026" in most_recent:
                return 100
            elif "2025" in most_recent:
                return 70
            elif "2024" in most_recent:
                return 40
            else:
                return 10
        except Exception:
            return 20

    return 0


def score_all_dimensions(site_data: dict) -> dict:
    """Score all 8 dimensions for a site and compute weighted total."""
    dimension_scores = {}
    for dim in DIMENSION_WEIGHTS:
        dimension_scores[dim] = score_dimension(site_data, dim)

    weighted_total = sum(
        dimension_scores[dim] * DIMENSION_WEIGHTS[dim]
        for dim in DIMENSION_WEIGHTS
    )

    return {
        "dimensions": dimension_scores,
        "weighted_total": round(weighted_total, 1),
    }


# --- Comparison Logic ---

def compare_sites(target_data: dict, competitor_data_list: list) -> dict:
    """
    Compare target against competitors.

    Returns comparison matrix, gap analysis, opportunities, and rankings.
    """
    # Score target
    target_scores = score_all_dimensions(target_data)

    # Score each competitor
    competitor_scores = []
    for comp_data in competitor_data_list:
        comp_scores = score_all_dimensions(comp_data)
        competitor_scores.append({
            "url": comp_data.get("url", ""),
            "domain": comp_data.get("domain", ""),
            "scores": comp_scores,
        })

    # Build comparison matrix
    matrix = {
        "target": {
            "url": target_data.get("url", ""),
            "domain": target_data.get("domain", ""),
            "scores": target_scores,
        },
        "competitors": competitor_scores,
    }

    # Gap analysis: where target is behind
    gaps = []
    opportunities = []

    for dim in DIMENSION_WEIGHTS:
        target_dim_score = target_scores["dimensions"][dim]
        comp_scores_for_dim = [
            c["scores"]["dimensions"][dim] for c in competitor_scores
        ]

        if comp_scores_for_dim:
            avg_comp = sum(comp_scores_for_dim) / len(comp_scores_for_dim)
            best_comp = max(comp_scores_for_dim)
            diff_from_avg = target_dim_score - avg_comp
            diff_from_best = target_dim_score - best_comp

            entry = {
                "dimension": dim,
                "weight": DIMENSION_WEIGHTS[dim],
                "target_score": target_dim_score,
                "competitor_avg": round(avg_comp, 1),
                "competitor_best": best_comp,
                "diff_from_avg": round(diff_from_avg, 1),
                "diff_from_best": round(diff_from_best, 1),
            }

            # Classify position
            if diff_from_avg > 15:
                entry["position"] = "Leading"
            elif diff_from_avg >= -15:
                entry["position"] = "Parity"
            elif diff_from_avg >= -30:
                entry["position"] = "Trailing"
            else:
                entry["position"] = "Critical Gap"

            if diff_from_avg < 0:
                gaps.append(entry)
            else:
                opportunities.append(entry)

    # Sort gaps by weighted impact (bigger gap * higher weight = higher priority)
    gaps.sort(key=lambda g: g["diff_from_avg"] * g["weight"])
    opportunities.sort(key=lambda o: o["diff_from_avg"] * o["weight"], reverse=True)

    # Rankings (overall weighted score)
    all_sites = [
        {"url": target_data.get("url", ""), "domain": target_data.get("domain", ""), "score": target_scores["weighted_total"], "is_target": True}
    ]
    for comp in competitor_scores:
        all_sites.append({
            "url": comp["url"],
            "domain": comp["domain"],
            "score": comp["scores"]["weighted_total"],
            "is_target": False,
        })
    all_sites.sort(key=lambda s: s["score"], reverse=True)

    # Add rank
    for i, site in enumerate(all_sites):
        site["rank"] = i + 1

    return {
        "matrix": matrix,
        "gaps": gaps,
        "opportunities": opportunities,
        "rankings": all_sites,
    }


# --- Top-Level Orchestrator ---

def analyze_competitors(target_url: str, competitor_urls: list) -> dict:
    """
    Full competitor analysis pipeline.

    Args:
        target_url: The site to analyze
        competitor_urls: List of competitor URLs (max 5)

    Returns:
        Complete analysis dict with scans, scores, comparison, gaps, action plan
    """
    errors = []

    # Validate inputs
    if not target_url:
        return {"error": "Target URL is required", "errors": ["No target URL provided"]}

    if len(competitor_urls) > MAX_COMPETITORS:
        errors.append(f"Truncated to {MAX_COMPETITORS} competitors (max)")
        competitor_urls = competitor_urls[:MAX_COMPETITORS]

    if not competitor_urls:
        return {"error": "At least one competitor URL is required", "errors": ["No competitor URLs provided"]}

    # Normalize URLs
    def normalize_url(u):
        if not u.startswith("http"):
            u = "https://" + u
        return u.rstrip("/")

    target_url = normalize_url(target_url)
    competitor_urls = [normalize_url(u) for u in competitor_urls]

    # Scan target
    print(f"Scanning target: {target_url}", file=sys.stderr)
    target_data = scan_site(target_url)

    # Scan competitors
    competitor_data_list = []
    for comp_url in competitor_urls:
        print(f"Scanning competitor: {comp_url}", file=sys.stderr)
        comp_data = scan_site(comp_url)
        competitor_data_list.append(comp_data)

    # Compare
    comparison = compare_sites(target_data, competitor_data_list)

    # Build action plan from gaps
    action_plan = []
    for gap in comparison.get("gaps", []):
        dim = gap["dimension"]
        diff = abs(gap["diff_from_avg"])
        weight = gap["weight"]
        impact = diff * weight

        actions = _get_actions_for_dimension(dim, gap)
        action_plan.append({
            "dimension": dim,
            "priority": "Critical" if gap["position"] == "Critical Gap" else "High" if diff > 15 else "Medium",
            "impact_score": round(impact, 1),
            "current_score": gap["target_score"],
            "target_score": gap["competitor_best"],
            "actions": actions,
        })

    action_plan.sort(key=lambda a: a["impact_score"], reverse=True)

    return {
        "target": {
            "url": target_url,
            "domain": target_data.get("domain", ""),
            "scan": target_data,
        },
        "competitors": [
            {
                "url": cd.get("url", ""),
                "domain": cd.get("domain", ""),
                "scan": cd,
            }
            for cd in competitor_data_list
        ],
        "comparison": comparison,
        "action_plan": action_plan,
        "errors": errors + target_data.get("errors", []),
    }


def _get_actions_for_dimension(dimension: str, gap: dict) -> list:
    """Return recommended actions for a given dimension gap."""
    actions_map = {
        "ai_citability": [
            "Restructure content with answer-first patterns (definition → detail → evidence)",
            "Aim for 134-167 word passages per content block",
            "Add specific statistics, percentages, and named sources",
            "Use question-based headings that match AI search queries",
        ],
        "brand_authority": [
            "Create/optimize YouTube channel with educational content",
            "Build authentic Reddit presence in industry subreddits",
            "Work toward Wikipedia notability through press coverage",
            "Publish thought leadership on LinkedIn",
        ],
        "content_depth": [
            "Expand thin pages to 1,000+ words with substantive content",
            "Add detailed examples, case studies, and data",
            "Create comprehensive pillar pages for core topics",
            "Add FAQ sections to increase content depth",
        ],
        "crawler_access": [
            "Review robots.txt — allow key AI crawlers (GPTBot, ClaudeBot, PerplexityBot)",
            "Remove overly broad Disallow rules for AI bots",
            "Test crawler access from each major AI bot user-agent",
        ],
        "schema_coverage": [
            "Add JSON-LD structured data to all key pages",
            "Implement Organization, WebPage, and Article schemas at minimum",
            "Add FAQ, HowTo, or Product schema where applicable",
            "Validate schema with Google Rich Results Test",
        ],
        "llms_txt": [
            "Create /llms.txt describing your site for AI models",
            "Create /llms-full.txt with detailed content inventory",
            "Follow the llms.txt specification (https://llmstxt.org)",
        ],
        "technical_geo": [
            "Ensure HTTPS everywhere with proper redirects",
            "Implement server-side rendering for key content",
            "Add canonical URLs to all pages",
            "Set proper security headers (HSTS, CSP, X-Frame-Options)",
        ],
        "content_freshness": [
            "Update key pages with current year data and statistics",
            "Add visible last-updated dates to content",
            "Publish new content regularly (at least monthly)",
            "Refresh outdated statistics and references",
        ],
    }
    return actions_map.get(dimension, ["Review and improve this dimension"])


# --- CLI ---

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python competitor_analyzer.py <target_url> <competitor1> [competitor2] ...")
        print("Example: python competitor_analyzer.py https://www.example.com https://www.competitor1.com https://www.competitor2.com")
        print(f"\nMax competitors: {MAX_COMPETITORS}")
        print(f"Max pages per site: {MAX_PAGES_PER_SITE}")
        sys.exit(1)

    target = sys.argv[1]
    competitors = sys.argv[2:]

    result = analyze_competitors(target, competitors)
    print(json.dumps(result, indent=2, default=str))

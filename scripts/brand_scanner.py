#!/usr/bin/env python3
"""
Brand Mention Scanner — Checks brand presence across AI-cited platforms.

Brand mentions correlate 3x more strongly with AI visibility than backlinks.
(Ahrefs December 2025 study of 75,000 brands)

Platform importance for AI citations:
1. YouTube mentions (~0.737 correlation - STRONGEST)
2. Reddit mentions (high)
3. Wikipedia presence (high)
4. LinkedIn presence (moderate)
5. Domain Rating/backlinks (~0.266 - weak)

Optional live checks: with a Scavio API key (https://scavio.dev) and
GEO_LIVE_PROVIDER=scavio (or --live), the YouTube and Reddit checks read real
search results, and each --prompt is asked to ChatGPT and Google AI Mode to see
whether the answer names the brand or cites its domain. Without the opt-in the
output is unchanged.
"""

import argparse
import os
import sys
import json
import re
from urllib.parse import quote_plus, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def check_youtube_presence(brand_name: str) -> dict:
    """Check brand presence on YouTube."""
    result = {
        "platform": "YouTube",
        "correlation": 0.737,
        "weight": "25%",
        "has_channel": False,
        "mentioned_in_videos": False,
        "search_url": f"https://www.youtube.com/results?search_query={quote_plus(brand_name)}",
        "recommendations": [],
    }

    # Note: Actual YouTube API would be used in production
    # This provides the framework for Claude Code to use WebFetch
    result["check_instructions"] = [
        f"Search YouTube for '{brand_name}' and check:",
        "1. Does the brand have an official YouTube channel?",
        "2. Are there videos FROM the brand (tutorials, demos, thought leadership)?",
        "3. Are there videos ABOUT the brand from other creators?",
        "4. What's the view count on brand-related videos?",
        "5. Are there positive reviews or demonstrations?",
    ]

    result["recommendations"] = [
        "Create a YouTube channel if none exists",
        "Publish educational/tutorial content related to your niche",
        "Encourage customers to create review/demo videos",
        "Optimize video titles and descriptions with brand name",
        "Add timestamps and chapters to improve AI parseability",
        "Include transcripts (YouTube auto-generates, but review for accuracy)",
    ]

    return result


def check_reddit_presence(brand_name: str) -> dict:
    """Check brand presence on Reddit."""
    result = {
        "platform": "Reddit",
        "correlation": "High",
        "weight": "25%",
        "has_subreddit": False,
        "mentioned_in_discussions": False,
        "search_url": f"https://www.reddit.com/search/?q={quote_plus(brand_name)}",
        "recommendations": [],
    }

    result["check_instructions"] = [
        f"Search Reddit for '{brand_name}' and check:",
        "1. Does the brand have its own subreddit (r/brandname)?",
        "2. Is the brand discussed in relevant industry subreddits?",
        "3. What's the sentiment (positive, negative, neutral)?",
        "4. Are there recommendation threads mentioning the brand?",
        "5. Does the brand have an official Reddit presence?",
        "6. Are mentions recent (within last 6 months)?",
    ]

    result["recommendations"] = [
        "Monitor relevant subreddits for brand mentions",
        "Participate authentically in industry discussions (no spam)",
        "Create an official Reddit account for customer support",
        "Share valuable content (not just self-promotion)",
        "Respond to questions about your product/service category",
        "Reddit authenticity matters — don't use marketing speak",
    ]

    return result


def check_wikipedia_presence(brand_name: str) -> dict:
    """Check brand/entity presence on Wikipedia and Wikidata."""
    result = {
        "platform": "Wikipedia",
        "correlation": "High",
        "weight": "20%",
        "has_wikipedia_page": False,
        "has_wikidata_entry": False,
        "cited_in_articles": False,
        "search_url": f"https://en.wikipedia.org/wiki/Special:Search?search={quote_plus(brand_name)}",
        "wikidata_url": f"https://www.wikidata.org/w/index.php?search={quote_plus(brand_name)}",
        "recommendations": [],
    }

    # Check Wikipedia API
    try:
        api_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote_plus(brand_name)}&format=json"
        response = requests.get(api_url, headers=DEFAULT_HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            search_results = data.get("query", {}).get("search", [])
            if search_results:
                # Check if top result is about the brand
                top_title = search_results[0].get("title", "").lower()
                if brand_name.lower() in top_title:
                    result["has_wikipedia_page"] = True
                result["wikipedia_search_results"] = len(search_results)
    except Exception:
        pass

    # Check Wikidata
    try:
        wikidata_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={quote_plus(brand_name)}&language=en&format=json"
        response = requests.get(wikidata_url, headers=DEFAULT_HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            entities = data.get("search", [])
            if entities:
                result["has_wikidata_entry"] = True
                result["wikidata_id"] = entities[0].get("id", "")
                result["wikidata_description"] = entities[0].get("description", "")
    except Exception:
        pass

    result["recommendations"] = [
        "If eligible, create a Wikipedia article (requires notability criteria)",
        "Ensure Wikidata entry exists with complete structured data",
        "Add sameAs links in schema markup pointing to Wikipedia/Wikidata",
        "Get cited in existing Wikipedia articles as a source",
        "Build notability through press coverage and independent reviews",
        "Note: Wikipedia has strict notability guidelines — PR coverage helps establish this",
    ]

    return result


def check_linkedin_presence(brand_name: str) -> dict:
    """Check brand presence on LinkedIn."""
    result = {
        "platform": "LinkedIn",
        "correlation": "Moderate",
        "weight": "15%",
        "has_company_page": False,
        "employee_thought_leadership": False,
        "search_url": f"https://www.linkedin.com/search/results/companies/?keywords={quote_plus(brand_name)}",
        "recommendations": [],
    }

    result["check_instructions"] = [
        f"Search LinkedIn for '{brand_name}' and check:",
        "1. Does the company have a LinkedIn page?",
        "2. How many followers?",
        "3. Is the page active with recent posts?",
        "4. Do employees post thought leadership content?",
        "5. Are there LinkedIn articles about the brand?",
        "6. Is there engagement on posts (likes, comments, shares)?",
    ]

    result["recommendations"] = [
        "Create/optimize LinkedIn company page",
        "Post regular thought leadership content",
        "Encourage employees to share company content",
        "Publish long-form LinkedIn articles",
        "Engage with industry discussions and comments",
        "Add company LinkedIn URL to schema sameAs property",
    ]

    return result


def check_other_platforms(brand_name: str) -> dict:
    """Check brand presence on additional platforms."""
    result = {
        "platform": "Other Platforms",
        "weight": "15%",
        "platforms_checked": {},
        "recommendations": [],
    }

    platforms = {
        "Quora": f"https://www.quora.com/search?q={quote_plus(brand_name)}",
        "Stack Overflow": f"https://stackoverflow.com/search?q={quote_plus(brand_name)}",
        "GitHub": f"https://github.com/search?q={quote_plus(brand_name)}",
        "Crunchbase": f"https://www.crunchbase.com/textsearch?q={quote_plus(brand_name)}",
        "Product Hunt": f"https://www.producthunt.com/search?q={quote_plus(brand_name)}",
        "G2": f"https://www.g2.com/search?utf8=&query={quote_plus(brand_name)}",
        "Trustpilot": f"https://www.trustpilot.com/search?query={quote_plus(brand_name)}",
    }

    result["platforms_checked"] = {
        name: {
            "search_url": url,
            "check_instruction": f"Search for '{brand_name}' on {name}",
        }
        for name, url in platforms.items()
    }

    result["recommendations"] = [
        "Maintain profiles on industry-relevant platforms",
        "Respond to questions on Quora and Stack Overflow",
        "Encourage customer reviews on G2 and Trustpilot",
        "Keep Crunchbase profile updated (important for B2B)",
        "Open-source contributions on GitHub boost developer brand authority",
        "Product Hunt launch can generate significant initial buzz",
    ]

    return result


# ---------------------------------------------------------------------------
# Optional live checks (Scavio API)
# ---------------------------------------------------------------------------

SCAVIO_BASE_URL = "https://api.scavio.dev"
MAX_PROMPTS = 10
# Credits per call, from https://scavio.dev/pricing
LIVE_CREDIT_COST = {"youtube": 2, "reddit": 1, "chatgpt": 2, "google_ai_mode": 1}


class LiveCheckError(Exception):
    """A live check failed. The message never contains the API key."""


def live_checks_enabled(cli_flag: bool = False) -> bool:
    """Live checks are opt-in: --live, or GEO_LIVE_PROVIDER=scavio."""
    return cli_flag or os.environ.get("GEO_LIVE_PROVIDER", "").strip().lower() == "scavio"


def _scavio_post(path: str, payload: dict, api_key: str, timeout: int = 60) -> dict:
    """POST to the Scavio API once. Paid calls are never retried."""
    try:
        response = requests.post(
            f"{SCAVIO_BASE_URL}{path}",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=timeout,
        )
    except requests.Timeout:
        raise LiveCheckError(f"Scavio timeout on {path}")
    except requests.RequestException as exc:
        raise LiveCheckError(f"Scavio request failed on {path}: {type(exc).__name__}")
    if response.status_code != 200:
        reasons = {401: "invalid API key", 402: "out of credits", 429: "rate limited"}
        reason = reasons.get(response.status_code, "error")
        raise LiveCheckError(f"Scavio HTTP {response.status_code} ({reason}) on {path}")
    try:
        return response.json()
    except ValueError:
        raise LiveCheckError(f"Scavio returned invalid JSON on {path}")


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _mentions(text: str, brand_name: str) -> bool:
    """Whole-word, case-insensitive brand match."""
    if not text or not brand_name.strip():
        return False
    pattern = r"(?<![A-Za-z0-9])" + re.escape(brand_name.strip()) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def _host(url: str) -> str:
    if "//" not in url:
        url = "//" + url
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _cites_domain(urls: list, domain: str) -> bool:
    target = _host(domain) if domain else ""
    if not target:
        return False
    for url in urls:
        host = _host(url or "")
        if host == target or host.endswith("." + target):
            return True
    return False


def live_youtube_presence(brand_name: str, api_key: str) -> dict:
    """Read real YouTube search results for the brand."""
    data = _scavio_post("/api/v1/youtube/search", {"search": brand_name}, api_key).get("data", {})
    videos = [r for r in data.get("results", []) if r.get("type", "video") == "video"]
    mentioning = [
        v for v in videos
        if _mentions(v.get("title", ""), brand_name) or _mentions((v.get("channel") or {}).get("name", ""), brand_name)
    ]
    brand_key = _normalize(brand_name)
    names = (brand_key, brand_key + "official", brand_key + "hq") if brand_key else ()
    brand_channel = None
    # Channel results carry the subscriber count; video channels are the fallback.
    for channel in data.get("channels", []) + [v.get("channel") or {} for v in videos]:
        if _normalize(channel.get("name", "")) in names:
            brand_channel = {
                "name": channel.get("name"),
                "url": channel.get("url"),
                "subscribers": channel.get("subscriber_count"),
            }
            break
    brand_videos = sum(
        1 for v in videos if brand_channel and (v.get("channel") or {}).get("name") == brand_channel["name"]
    )
    third_party = {
        (v.get("channel") or {}).get("name")
        for v in mentioning
        if not brand_channel or (v.get("channel") or {}).get("name") != brand_channel["name"]
    }
    third_party.discard(None)
    return {
        "source": "scavio",
        "videos_returned": len(videos),
        "videos_mentioning_brand": len(mentioning),
        "brand_channel": brand_channel,
        "videos_from_brand_channel": brand_videos,
        "third_party_channels": len(third_party),
        "top_videos": [
            {
                "title": v.get("title"),
                "url": v.get("url"),
                "channel": (v.get("channel") or {}).get("name"),
                "view_count": v.get("view_count"),
                "published": v.get("published_time"),
            }
            for v in mentioning[:5]
        ],
        "credits": LIVE_CREDIT_COST["youtube"],
    }


def live_reddit_presence(brand_name: str, api_key: str) -> dict:
    """Read real Reddit search results for the brand."""
    data = _scavio_post("/api/v1/reddit/search", {"query": brand_name}, api_key)
    posts = data.get("data", {}).get("results", [])
    mentioning = [p for p in posts if _mentions(p.get("title", ""), brand_name) or _mentions(p.get("text", ""), brand_name)]
    subreddits = {}
    for p in mentioning:
        name = p.get("subreddit")
        if name:
            subreddits[name] = subreddits.get(name, 0) + 1
    dates = sorted((p.get("created_at") or "")[:10] for p in mentioning if p.get("created_at"))
    brand_key = _normalize(brand_name)
    return {
        "source": "scavio",
        "posts_returned": len(posts),
        "posts_mentioning_brand": len(mentioning),
        "brand_subreddit": any(_normalize(name) == brand_key for name in subreddits) if brand_key else False,
        "subreddits": dict(sorted(subreddits.items(), key=lambda kv: -kv[1])),
        "newest_mention": dates[-1] if dates else None,
        "oldest_mention": dates[0] if dates else None,
        "total_comments": sum(p.get("num_comments") or 0 for p in mentioning),
        "top_posts": [
            {
                "title": p.get("title"),
                "url": p.get("url"),
                "subreddit": p.get("subreddit"),
                "score": p.get("score"),
                "comments": p.get("num_comments"),
                "created": (p.get("created_at") or "")[:10] or None,
            }
            for p in mentioning[:5]
        ],
        "credits": LIVE_CREDIT_COST["reddit"],
    }


def _ai_mode_text(data: dict) -> str:
    """Flatten Google AI Mode text blocks (paragraphs, headings, lists, tables)."""
    parts = []

    def walk(blocks):
        for block in blocks or []:
            if not isinstance(block, dict):
                continue
            if block.get("snippet"):
                parts.append(block["snippet"])
            walk(block.get("list"))
            for row in block.get("table_rows") or []:
                parts.append(" | ".join(str(cell) for cell in row))

    walk(data.get("text_blocks"))
    return "\n".join(parts)


def live_ai_answers(brand_name: str, domain: str, prompts: list, api_key: str) -> dict:
    """Ask each prompt to ChatGPT and Google AI Mode; record mentions and citations."""
    results = []
    for prompt in prompts[:MAX_PROMPTS]:
        entry = {"prompt": prompt}
        try:
            data = _scavio_post("/api/v1/chatgpt/prompt", {"prompt": prompt}, api_key, timeout=180).get("data", {})
            sources = [s.get("url", "") for s in data.get("sources", [])]
            entry["chatgpt"] = {
                "mentions_brand": _mentions((data.get("answer") or {}).get("markdown", ""), brand_name),
                "cites_domain": _cites_domain(sources, domain),
                "sources": len(sources),
            }
        except LiveCheckError as exc:
            entry["chatgpt"] = {"error": str(exc)}
        try:
            data = _scavio_post("/api/v2/google/ai-mode", {"query": prompt}, api_key, timeout=180)
            refs = [r.get("link", "") for r in data.get("references", [])]
            entry["google_ai_mode"] = {
                "mentions_brand": _mentions(_ai_mode_text(data), brand_name),
                "cites_domain": _cites_domain(refs, domain),
                "sources": len(refs),
            }
        except LiveCheckError as exc:
            entry["google_ai_mode"] = {"error": str(exc)}
        results.append(entry)

    summary = {}
    for engine in ("chatgpt", "google_ai_mode"):
        answered = [r[engine] for r in results if "error" not in r[engine]]
        summary[engine] = {
            "prompts_answered": len(answered),
            "brand_mentioned": sum(1 for a in answered if a["mentions_brand"]),
            "domain_cited": sum(1 for a in answered if a["cites_domain"]),
        }
    return {
        "source": "scavio",
        "prompts": results,
        "summary": summary,
        "skipped_prompts": max(0, len(prompts) - MAX_PROMPTS),
        # Failed calls are not charged, so only answered prompts count.
        "credits": sum(
            LIVE_CREDIT_COST[engine] for r in results for engine in ("chatgpt", "google_ai_mode")
            if "error" not in r[engine]
        ),
    }


def generate_brand_report(brand_name: str, domain: str = None, prompts: list = None, api_key: str = None) -> dict:
    """Generate a comprehensive brand mention report.

    With api_key, YouTube and Reddit get a "live" block from real search results
    and each prompt is checked in ChatGPT and Google AI Mode ("ai_answers").
    """
    report = {
        "brand_name": brand_name,
        "domain": domain,
        "analysis_date": "Generated by GEO-SEO Claude Tool",
        "key_insight": "Brand mentions correlate 3x more strongly with AI visibility than backlinks (Ahrefs Dec 2025, 75K brands)",
        "platforms": {},
        "overall_recommendations": [],
    }

    # Check all platforms
    report["platforms"]["youtube"] = check_youtube_presence(brand_name)
    report["platforms"]["reddit"] = check_reddit_presence(brand_name)
    report["platforms"]["wikipedia"] = check_wikipedia_presence(brand_name)
    report["platforms"]["linkedin"] = check_linkedin_presence(brand_name)
    report["platforms"]["other"] = check_other_platforms(brand_name)

    if api_key:
        live_credits = 0
        for key, check in (("youtube", live_youtube_presence), ("reddit", live_reddit_presence)):
            platform = report["platforms"][key]
            try:
                live = check(brand_name, api_key)
                platform["live"] = live
                live_credits += live["credits"]
                if key == "youtube":
                    platform["has_channel"] = live["brand_channel"] is not None
                    platform["mentioned_in_videos"] = live["videos_mentioning_brand"] > 0
                else:
                    platform["has_subreddit"] = live["brand_subreddit"]
                    platform["mentioned_in_discussions"] = live["posts_mentioning_brand"] > 0
            except LiveCheckError as exc:
                platform["live_error"] = str(exc)
        if prompts:
            report["ai_answers"] = live_ai_answers(brand_name, domain, prompts, api_key)
            live_credits += report["ai_answers"]["credits"]
        report["live_credits_used"] = live_credits
        report["live_note"] = (
            "Live matches are by name. If the brand name is a common word or shared with another "
            "company, check top_videos and top_posts, and rerun with the distinctive name."
        )

    # Overall recommendations
    report["overall_recommendations"] = [
        "Priority 1: YouTube — highest correlation (0.737) with AI citations. Create educational content.",
        "Priority 2: Reddit — build authentic presence in industry subreddits. No marketing speak.",
        "Priority 3: Wikipedia — establish notability through press coverage, then create/improve entry.",
        "Priority 4: LinkedIn — thought leadership content from founders and employees.",
        "Priority 5: Review platforms — G2, Trustpilot, Capterra for social proof signals.",
        "Cross-platform: Ensure consistent NAP (Name, Address, Phone) across all platforms.",
        "Schema markup: Add sameAs property linking to ALL platform profiles.",
        "Monitor: Set up brand mention alerts across all platforms.",
    ]

    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Check brand presence across AI-cited platforms.",
        epilog="Example: python brand_scanner.py 'Acme Corp' acmecorp.com --prompt 'best crm for agencies'",
    )
    parser.add_argument("brand", help="Brand name as it appears on the site")
    parser.add_argument("domain", nargs="?", default=None, help="Brand domain, used to detect citations")
    parser.add_argument(
        "--prompt", action="append", default=[],
        help="A buyer question to ask ChatGPT and Google AI Mode (live checks only; repeatable, max %d)" % MAX_PROMPTS,
    )
    parser.add_argument(
        "--live", action="store_true",
        help="Run live checks with SCAVIO_API_KEY (same as GEO_LIVE_PROVIDER=scavio)",
    )
    args = parser.parse_args(argv)

    api_key = None
    if live_checks_enabled(args.live):
        api_key = os.environ.get("SCAVIO_API_KEY", "").strip()
        if not api_key:
            print("ERROR: live checks need SCAVIO_API_KEY. Get a key at https://scavio.dev", file=sys.stderr)
            return 1

    result = generate_brand_report(args.brand, args.domain, prompts=args.prompt, api_key=api_key)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

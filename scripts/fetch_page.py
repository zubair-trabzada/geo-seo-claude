#!/usr/bin/env python3
"""
Fetch and parse web pages for GEO analysis.
Extracts HTML, text content, meta tags, headers, and structured data.
"""

import sys
import json
import re
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

# Common AI crawler user agents for testing
AI_CRAWLERS = {
    "GPTBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)",
    "ClaudeBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +https://www.anthropic.com/claude-bot)",
    "PerplexityBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
    "GoogleBot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "BingBot": "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}


def fetch_page(url: str, timeout: int = 30) -> dict:
    """Fetch a page and return structured analysis data."""
    result = {
        "url": url,
        "status_code": None,
        "redirect_chain": [],
        "headers": {},
        "meta_tags": {},
        "title": None,
        "description": None,
        "canonical": None,
        "h1_tags": [],
        "heading_structure": [],
        "word_count": 0,
        "text_content": "",
        "internal_links": [],
        "external_links": [],
        "images": [],
        "structured_data": [],
        "has_ssr_content": True,
        "security_headers": {},
        "errors": [],
    }

    parsed_url = urlparse(url)
    if parsed_url.scheme not in ("http", "https"):
        result["errors"].append(f"Unsupported URL scheme: {parsed_url.scheme!r}. Only http and https are allowed.")
        return result

    try:
        response = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )

        # Track redirects
        if response.history:
            result["redirect_chain"] = [
                {"url": r.url, "status": r.status_code} for r in response.history
            ]

        result["status_code"] = response.status_code
        result["headers"] = dict(response.headers)

        # Security headers check
        security_headers = [
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Referrer-Policy",
            "Permissions-Policy",
        ]
        for header in security_headers:
            result["security_headers"][header] = response.headers.get(header, None)

        # Parse HTML
        soup = BeautifulSoup(response.text, "lxml")

        # Title
        title_tag = soup.find("title")
        result["title"] = title_tag.get_text(strip=True) if title_tag else None

        # Meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name", meta.get("property", ""))
            content = meta.get("content", "")
            if name and content:
                result["meta_tags"][name.lower()] = content
                if name.lower() == "description":
                    result["description"] = content

        # Canonical
        canonical = soup.find("link", rel="canonical")
        result["canonical"] = canonical.get("href") if canonical else None

        # Headings
        for level in range(1, 7):
            for heading in soup.find_all(f"h{level}"):
                text = heading.get_text(strip=True)
                result["heading_structure"].append({"level": level, "text": text})
                if level == 1:
                    result["h1_tags"].append(text)

        # Structured data (JSON-LD) — extract before decompose() mutates the tree
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                result["structured_data"].append(data)
            except (json.JSONDecodeError, TypeError):
                result["errors"].append("Invalid JSON-LD detected")

        # SSR check — must run BEFORE decompose() mutates the tree
        js_app_roots = soup.find_all(
            id=re.compile(r"(app|root|__next|__nuxt)", re.I)
        )

        # Check SSR by measuring content inside framework root divs
        # before decompose() strips elements from the tree
        ssr_check_results = []
        for root_el in js_app_roots:
            inner_text = root_el.get_text(strip=True)
            ssr_check_results.append({
                "id": root_el.get("id", "unknown"),
                "text_length": len(inner_text),
            })

        # Text content — decompose non-content elements (destructive)
        for element in soup.find_all(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        text = soup.get_text(separator=" ", strip=True)
        result["text_content"] = text
        result["word_count"] = len(text.split())

        # Links
        parsed_url = urlparse(url)
        base_domain = parsed_url.netloc
        for link in soup.find_all("a", href=True):
            href = urljoin(url, link["href"])
            link_text = link.get_text(strip=True)
            parsed_href = urlparse(href)
            if parsed_href.netloc == base_domain:
                result["internal_links"].append({"url": href, "text": link_text})
            elif parsed_href.scheme in ("http", "https"):
                result["external_links"].append({"url": href, "text": link_text})

        # Images
        for img in soup.find_all("img"):
            img_data = {
                "src": img.get("src", ""),
                "alt": img.get("alt", ""),
                "width": img.get("width"),
                "height": img.get("height"),
                "loading": img.get("loading"),
            }
            result["images"].append(img_data)

        # SSR assessment — use pre-decompose measurements + overall content
        if js_app_roots:
            for check in ssr_check_results:
                # Only flag as client-rendered if both the root div has
                # minimal content AND the overall page has little text.
                # Sites using SSR/prerendering (WordPress, LiteSpeed Cache,
                # Prerender.io) will have substantial text despite having
                # framework-style root divs.
                if check["text_length"] < 50 and result["word_count"] < 200:
                    result["has_ssr_content"] = False
                    result["errors"].append(
                        f"Possible client-side only rendering detected: "
                        f"#{check['id']} has minimal server-rendered content "
                        f"({result['word_count']} words on page)"
                    )

    except requests.exceptions.Timeout:
        result["errors"].append(f"Timeout after {timeout} seconds")
    except requests.exceptions.ConnectionError as e:
        result["errors"].append(f"Connection error: {str(e)}")
    except Exception as e:
        result["errors"].append(f"Unexpected error: {str(e)}")

    return result


def fetch_robots_txt(url: str, timeout: int = 15) -> dict:
    """Fetch and parse robots.txt for AI crawler directives."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    ai_crawlers = [
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

    result = {
        "url": robots_url,
        "exists": False,
        "content": "",
        "ai_crawler_status": {},
        "sitemaps": [],
        "errors": [],
    }

    try:
        response = requests.get(robots_url, headers=DEFAULT_HEADERS, timeout=timeout)

        if response.status_code == 200:
            result["exists"] = True
            result["content"] = response.text

            # Parse for each AI crawler
            lines = response.text.split("\n")
            current_agent = None
            agent_rules = {}

            for line in lines:
                line = line.strip()
                if line.lower().startswith("user-agent:"):
                    current_agent = line.split(":", 1)[1].strip()
                    if current_agent not in agent_rules:
                        agent_rules[current_agent] = []
                elif line.lower().startswith("disallow:") and current_agent:
                    path = line.split(":", 1)[1].strip()
                    agent_rules[current_agent].append(
                        {"directive": "Disallow", "path": path}
                    )
                elif line.lower().startswith("allow:") and current_agent:
                    path = line.split(":", 1)[1].strip()
                    agent_rules[current_agent].append(
                        {"directive": "Allow", "path": path}
                    )
                elif line.lower().startswith("sitemap:"):
                    sitemap_url = line.split(":", 1)[1].strip()
                    # Handle case where "Sitemap:" splits off the "http"
                    if not sitemap_url.startswith("http"):
                        sitemap_url = "http" + sitemap_url
                    result["sitemaps"].append(sitemap_url)

            # Determine status for each AI crawler
            for crawler in ai_crawlers:
                if crawler in agent_rules:
                    rules = agent_rules[crawler]
                    if any(
                        r["directive"] == "Disallow" and r["path"] == "/"
                        for r in rules
                    ):
                        result["ai_crawler_status"][crawler] = "BLOCKED"
                    elif any(
                        r["directive"] == "Disallow" and r["path"] for r in rules
                    ):
                        result["ai_crawler_status"][crawler] = "PARTIALLY_BLOCKED"
                    else:
                        result["ai_crawler_status"][crawler] = "ALLOWED"
                elif "*" in agent_rules:
                    wildcard_rules = agent_rules["*"]
                    if any(
                        r["directive"] == "Disallow" and r["path"] == "/"
                        for r in wildcard_rules
                    ):
                        result["ai_crawler_status"][crawler] = "BLOCKED_BY_WILDCARD"
                    else:
                        result["ai_crawler_status"][crawler] = "ALLOWED_BY_DEFAULT"
                else:
                    result["ai_crawler_status"][crawler] = "NOT_MENTIONED"

        elif response.status_code == 404:
            result["errors"].append("No robots.txt found (404)")
            for crawler in ai_crawlers:
                result["ai_crawler_status"][crawler] = "NO_ROBOTS_TXT"
        else:
            result["errors"].append(
                f"Unexpected status code: {response.status_code}"
            )

    except Exception as e:
        result["errors"].append(f"Error fetching robots.txt: {str(e)}")

    return result


def fetch_llms_txt(url: str, timeout: int = 15) -> dict:
    """Check for llms.txt file."""
    parsed = urlparse(url)
    llms_url = f"{parsed.scheme}://{parsed.netloc}/llms.txt"
    llms_full_url = f"{parsed.scheme}://{parsed.netloc}/llms-full.txt"

    result = {
        "llms_txt": {"url": llms_url, "exists": False, "content": ""},
        "llms_full_txt": {"url": llms_full_url, "exists": False, "content": ""},
        "errors": [],
    }

    for key, check_url in [("llms_txt", llms_url), ("llms_full_txt", llms_full_url)]:
        try:
            response = requests.get(
                check_url, headers=DEFAULT_HEADERS, timeout=timeout
            )
            if response.status_code == 200:
                result[key]["exists"] = True
                result[key]["content"] = response.text
        except Exception as e:
            result["errors"].append(f"Error checking {check_url}: {str(e)}")

    return result


def extract_content_blocks(html: str) -> list:
    """Extract content blocks for citability analysis."""
    soup = BeautifulSoup(html, "lxml")

    # Remove non-content elements
    for element in soup.find_all(
        ["script", "style", "nav", "footer", "header", "aside"]
    ):
        element.decompose()

    blocks = []
    # Extract content sections (between headings)
    current_heading = None
    current_content = []

    for element in soup.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "table", "blockquote"]
    ):
        tag = element.name

        if tag.startswith("h"):
            # Save previous block
            if current_content:
                text = " ".join(current_content)
                word_count = len(text.split())
                blocks.append(
                    {
                        "heading": current_heading,
                        "content": text,
                        "word_count": word_count,
                        "tag_types": list(
                            set(
                                [
                                    e.name
                                    for e in element.find_all_previous(
                                        ["p", "ul", "ol", "table"]
                                    )
                                ]
                            )
                        ),
                    }
                )
            current_heading = element.get_text(strip=True)
            current_content = []
        else:
            text = element.get_text(strip=True)
            if text:
                current_content.append(text)

    # Don't forget the last block
    if current_content:
        text = " ".join(current_content)
        blocks.append(
            {
                "heading": current_heading,
                "content": text,
                "word_count": len(text.split()),
            }
        )

    return blocks


def crawl_sitemap(url: str, max_pages: int = 50, timeout: int = 15) -> list:
    """Crawl sitemap.xml to discover pages."""
    parsed = urlparse(url)
    sitemap_urls = [
        f"{parsed.scheme}://{parsed.netloc}/sitemap.xml",
        f"{parsed.scheme}://{parsed.netloc}/sitemap_index.xml",
        f"{parsed.scheme}://{parsed.netloc}/sitemap/",
    ]

    discovered_pages = set()

    for sitemap_url in sitemap_urls:
        try:
            response = requests.get(
                sitemap_url, headers=DEFAULT_HEADERS, timeout=timeout
            )
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")

                # Check for sitemap index
                for sitemap in soup.find_all("sitemap"):
                    loc = sitemap.find("loc")
                    if loc:
                        # Fetch child sitemap
                        try:
                            child_resp = requests.get(
                                loc.text.strip(),
                                headers=DEFAULT_HEADERS,
                                timeout=timeout,
                            )
                            if child_resp.status_code == 200:
                                child_soup = BeautifulSoup(child_resp.text, "lxml")
                                for url_tag in child_soup.find_all("url"):
                                    loc_tag = url_tag.find("loc")
                                    if loc_tag:
                                        discovered_pages.add(loc_tag.text.strip())
                                    if len(discovered_pages) >= max_pages:
                                        break
                        except Exception:
                            pass
                    if len(discovered_pages) >= max_pages:
                        break

                # Direct URL entries
                for url_tag in soup.find_all("url"):
                    loc = url_tag.find("loc")
                    if loc:
                        discovered_pages.add(loc.text.strip())
                    if len(discovered_pages) >= max_pages:
                        break

                if discovered_pages:
                    break

        except Exception:
            continue

    return list(discovered_pages)[:max_pages]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_page.py <url> [mode]")
        print("Modes: page (default), robots, llms, sitemap, blocks, full")
        sys.exit(1)

    target_url = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "page"

    if mode == "page":
        data = fetch_page(target_url)
    elif mode == "robots":
        data = fetch_robots_txt(target_url)
    elif mode == "llms":
        data = fetch_llms_txt(target_url)
    elif mode == "sitemap":
        pages = crawl_sitemap(target_url)
        data = {"pages": pages, "count": len(pages)}
    elif mode == "blocks":
        response = requests.get(target_url, headers=DEFAULT_HEADERS, timeout=30)
        data = extract_content_blocks(response.text)
    elif mode == "full":
        data = {
            "page": fetch_page(target_url),
            "robots": fetch_robots_txt(target_url),
            "llms": fetch_llms_txt(target_url),
            "sitemap": crawl_sitemap(target_url),
        }
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)

    print(json.dumps(data, indent=2, default=str))

#!/usr/bin/env python3
"""
Article SEO Optimizer & Keyword Researcher

Fetches an article, detects the CMS (Blogger, WordPress, Ghost, generic),
extracts structured content, performs keyword research, and collects
readability, JSON-LD, and meta signals for LLM-driven SEO analysis.

Supported platforms:
  - Blogger / Blogspot  (itemprop=articleBody, class=post-body)
  - WordPress            (class=entry-content, class=post-content)
  - Ghost               (class=post-content, class=gh-content)
  - Generic / fallback  (<article>, <main>, or all <p> tags)

Usage:
    python article_seo.py https://example.com/article
    python article_seo.py https://example.com/article --keyword "red team ops"
    python article_seo.py https://example.com/article --json
"""

import argparse
import json
import re
import sys
import math
import time
import urllib.request
import urllib.parse
from collections import Counter

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 required. Install with: pip install beautifulsoup4")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "with", "by", "of", "from", "as", "is", "are", "was", "were", "be",
    "been", "this", "that", "these", "those", "it", "he", "she", "they",
    "we", "you", "i", "your", "my", "their", "our", "its", "which", "who",
    "whom", "whose", "what", "where", "when", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can",
    "will", "just", "should", "have", "has", "had", "do", "does", "did",
    "get", "got", "make", "use", "used", "also", "its", "about", "into",
    "than", "then", "there", "their", "they", "would", "could", "here",
}

# Deprecated / restricted schema types (as of Feb 2026)
DEPRECATED_SCHEMA = {
    "HowTo", "SpecialAnnouncement", "CourseInfo", "EstimatedSalary",
    "LearningVideo", "ClaimReview", "VehicleListing", "PracticeProblems",
}
RESTRICTED_SCHEMA = {"FAQPage"}  # government / healthcare only


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_html(url: str) -> str:
    """Fetch raw HTML from a URL with a realistic browser user-agent."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        print(f"Error fetching {url}: {exc}", file=sys.stderr)
        return ""


# ---------------------------------------------------------------------------
# CMS detection
# ---------------------------------------------------------------------------

def detect_cms(soup: BeautifulSoup, url: str) -> str:
    """Detect the publishing platform from HTML signals."""
    # Blogger: generator meta OR blogspot.com in URL
    generator = soup.find("meta", attrs={"name": "generator"})
    if generator:
        gen_val = generator.get("content", "").lower()
        if "blogger" in gen_val:
            return "blogger"
        if "wordpress" in gen_val:
            return "wordpress"
        if "ghost" in gen_val:
            return "ghost"

    if "blogspot.com" in url or soup.find(attrs={"data-blog-id": True}):
        return "blogger"

    if soup.find("body", class_=re.compile(r"wp-")):
        return "wordpress"
    if soup.find(attrs={"class": re.compile(r"gh-content|ghost-")}):
        return "ghost"

    # WordPress theme signals
    if soup.find("link", attrs={"rel": "https://api.w.org/"}):
        return "wordpress"

    return "generic"


# ---------------------------------------------------------------------------
# Content extraction (CMS-aware)
# ---------------------------------------------------------------------------

def extract_content(soup: BeautifulSoup, cms: str) -> dict:
    """
    Extract structured content from the parsed page.

    Returns a dict with:
      title, meta_description, og_description, h1, h2s, h3s,
      paragraphs, images, labels/categories, word_count
    """
    result = {
        "title": "",
        "meta_description": "",
        "og_description": "",
        "h1": [],
        "h2s": [],
        "h3s": [],
        "paragraphs": [],
        "images": [],
        "labels": [],
        "publish_date": "",
        "author": "",
    }

    # ── Meta tags (common for all CMSes) ──────────────────────────────────
    title_tag = soup.find("title")
    if title_tag:
        result["title"] = title_tag.get_text(strip=True)

    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag:
        result["meta_description"] = desc_tag.get("content", "")

    og_desc = soup.find("meta", property="og:description")
    if not og_desc:
        og_desc = soup.find("meta", attrs={"property": "og:description"})
    if og_desc:
        result["og_description"] = og_desc.get("content", "")

    # ── Author ─────────────────────────────────────────────────────────────
    author_tag = (
        soup.find(attrs={"class": re.compile(r"author|byline", re.I)})
        or soup.find("span", itemprop="author")
        or soup.find("a", rel="author")
    )
    if author_tag:
        result["author"] = author_tag.get_text(strip=True)[:100]

    # ── Publish date ───────────────────────────────────────────────────────
    for sel in [
        {"itemprop": "datePublished"},
        {"class": re.compile(r"published|post-date|entry-date", re.I)},
        {"name": "article:published_time"},
    ]:
        date_tag = soup.find(attrs=sel) if isinstance(sel, dict) else None
        if date_tag:
            result["publish_date"] = (
                date_tag.get("content") or date_tag.get("datetime") or date_tag.get_text(strip=True)
            )[:50]
            break

    # ── CMS-specific body container ────────────────────────────────────────
    body_container = None

    if cms == "blogger":
        # Primary: itemprop=articleBody
        body_container = soup.find(attrs={"itemprop": "articleBody"})
        if not body_container:
            # Fallback: Blogger classic template
            body_container = soup.find(attrs={"class": re.compile(r"post-body|entry-content", re.I)})
        # Labels (Blogger categories)
        for label_a in soup.find_all("a", attrs={"class": re.compile(r"label-link|goog-label", re.I)}):
            label_text = label_a.get_text(strip=True)
            if label_text:
                result["labels"].append(label_text)
        # Post title override (Blogger uses h3.post-title in some templates)
        post_title = soup.find(attrs={"class": re.compile(r"post-title|entry-title", re.I)})
        if post_title and not result["title"]:
            result["title"] = post_title.get_text(strip=True)

    elif cms == "wordpress":
        body_container = (
            soup.find(attrs={"class": re.compile(r"entry-content|post-content|article-content", re.I)})
            or soup.find("article")
        )
        # WP categories/tags
        for cat in soup.find_all(attrs={"class": re.compile(r"cat-links|tags-links|post-categories", re.I)}):
            for a in cat.find_all("a"):
                t = a.get_text(strip=True)
                if t:
                    result["labels"].append(t)

    elif cms == "ghost":
        body_container = soup.find(attrs={"class": re.compile(r"gh-content|post-content|article-content", re.I)})

    else:  # generic
        body_container = (
            soup.find("article")
            or soup.find("main")
            or soup.find(attrs={"id": re.compile(r"content|main|article", re.I)})
            or soup.find(attrs={"class": re.compile(r"content|article|post|entry", re.I)})
        )

    # ── Headings ──────────────────────────────────────────────────────────
    search_scope = body_container if body_container else soup

    h1_tags = search_scope.find_all("h1")
    result["h1"] = [h.get_text(strip=True) for h in h1_tags if h.get_text(strip=True)]

    h2_tags = search_scope.find_all("h2")
    result["h2s"] = [h.get_text(strip=True) for h in h2_tags if h.get_text(strip=True)]

    h3_tags = search_scope.find_all("h3")
    result["h3s"] = [h.get_text(strip=True) for h in h3_tags if h.get_text(strip=True)]

    # ── Paragraphs ────────────────────────────────────────────────────────
    para_scope = body_container if body_container else soup
    for p in para_scope.find_all("p"):
        text = p.get_text(" ", strip=True)
        if len(text.split()) > 8:  # skip tiny fragments
            result["paragraphs"].append(text)

    # ── Images ────────────────────────────────────────────────────────────
    img_scope = body_container if body_container else soup
    for img in img_scope.find_all("img"):
        result["images"].append({
            "src": img.get("src", img.get("data-src", "")),
            "alt": img.get("alt", ""),
            "width": img.get("width", ""),
            "height": img.get("height", ""),
            "loading": img.get("loading", ""),
        })

    return result


# ---------------------------------------------------------------------------
# JSON-LD structured data extraction
# ---------------------------------------------------------------------------

def extract_structured_data(soup: BeautifulSoup) -> list:
    """
    Extract and parse all <script type="application/ld+json"> blocks.
    Flags deprecated / restricted types.
    """
    blocks = []
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or ""
        try:
            data = json.loads(raw.strip())
        except json.JSONDecodeError:
            blocks.append({"error": "invalid_json", "raw_snippet": raw[:120]})
            continue

        schema_type = data.get("@type", "Unknown")
        status = "active"
        note = ""

        if schema_type in DEPRECATED_SCHEMA:
            status = "deprecated"
            note = f"{schema_type} was deprecated/removed from rich results. Remove or replace."
        elif schema_type in RESTRICTED_SCHEMA:
            status = "restricted"
            note = f"{schema_type} is restricted to government/healthcare authority sites only."

        blocks.append({
            "@type": schema_type,
            "@context": data.get("@context", ""),
            "status": status,
            "note": note,
            "has_context": bool(data.get("@context")),
            "has_type": bool(data.get("@type")),
            "raw": data,
        })

    return blocks


# ---------------------------------------------------------------------------
# Readability scoring (Flesch-Kincaid)
# ---------------------------------------------------------------------------

def _count_syllables(word: str) -> int:
    """Approximate syllable count for a word."""
    word = word.lower().strip(".,!?;:")
    if len(word) <= 3:
        return 1
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e"):
        count -= 1
    return max(1, count)


def compute_readability(text: str) -> dict:
    """
    Compute Flesch Reading Ease and Flesch-Kincaid Grade Level.

    Flesch Reading Ease: 206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)
    FK Grade Level:       0.39*(words/sentences) + 11.8*(syllables/words) - 15.59
    """
    if not text.strip():
        return {"flesch_reading_ease": None, "fkgl": None, "grade_label": "N/A"}

    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = max(1, len(sentences))

    words = re.findall(r"\b[a-zA-Z'-]+\b", text)
    word_count = max(1, len(words))

    syllable_count = sum(_count_syllables(w) for w in words)

    avg_sentence_len = word_count / sentence_count
    avg_syllables_per_word = syllable_count / word_count

    fre = 206.835 - 1.015 * avg_sentence_len - 84.6 * avg_syllables_per_word
    fkgl = 0.39 * avg_sentence_len + 11.8 * avg_syllables_per_word - 15.59

    fre = round(max(0, min(100, fre)), 1)
    fkgl = round(max(0, fkgl), 1)

    if fre >= 70:
        grade_label = "Easy (suitable for general audience)"
    elif fre >= 50:
        grade_label = "Medium (suitable for high school / college)"
    else:
        grade_label = "Difficult (technical / specialist audience)"

    return {
        "flesch_reading_ease": fre,
        "fkgl": fkgl,
        "grade_label": grade_label,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_len, 1),
        "avg_syllables_per_word": round(avg_syllables_per_word, 2),
    }


# ---------------------------------------------------------------------------
# Keyword extraction (frequency-weighted n-grams — honest naming)
# ---------------------------------------------------------------------------

def extract_keywords_frequency(text: str, top_n: int = 12) -> list:
    """
    Extract high-frequency unigrams, bigrams, and trigrams as keyword candidates.
    Uses frequency counting (not TF-IDF — no corpus reference available).
    Favors multi-word phrases over single terms.
    """
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    filtered = [w for w in words if w not in STOP_WORDS]

    unigrams = Counter(filtered)
    bigrams = Counter(
        f"{filtered[i]} {filtered[i+1]}"
        for i in range(len(filtered) - 1)
    )
    trigrams = Counter(
        f"{filtered[i]} {filtered[i+1]} {filtered[i+2]}"
        for i in range(len(filtered) - 2)
    )

    scored: list[tuple[str, float]] = []
    for term, cnt in unigrams.items():
        if cnt > 3:
            scored.append((term, float(cnt)))
    for term, cnt in bigrams.items():
        if cnt > 1:
            scored.append((term, cnt * 3.0))
    for term, cnt in trigrams.items():
        if cnt > 1:
            scored.append((term, cnt * 5.0))

    scored.sort(key=lambda x: x[1], reverse=True)

    # Deduplicate: if a shorter term is a substring of a longer one, prefer longer
    final: list[str] = []
    all_terms = [t for t, _ in scored]
    for term, _ in scored:
        if not any(term in other and term != other for other in all_terms[:top_n * 3]):
            final.append(term)
        if len(final) >= top_n:
            break

    return final


# ---------------------------------------------------------------------------
# Google Autocomplete (related keyword suggestions)
# ---------------------------------------------------------------------------

def get_google_autocomplete(query: str) -> list:
    """Fetch Google Autocomplete suggestions (free, no API key required)."""
    try:
        url = (
            "https://suggestqueries.google.com/complete/search"
            f"?client=chrome&q={urllib.parse.quote(query)}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if len(data) >= 2 and isinstance(data[1], list):
                return data[1]
    except Exception:
        pass
    return []


# ---------------------------------------------------------------------------
# SEO issue detection
# ---------------------------------------------------------------------------

def detect_seo_issues(content: dict, structured_data: list, readability: dict) -> list:
    """
    Lightweight rule-based SEO issue flags for the article.
    Returns list of {severity, finding, fix} dicts.
    """
    issues = []

    title = content.get("title", "")
    meta = content.get("meta_description", "")
    h1s = content.get("h1", [])
    word_count = readability.get("word_count", 0)
    images = content.get("images", [])

    # Title checks
    if not title:
        issues.append({"severity": "Critical", "area": "Title", "finding": "No <title> tag found.", "fix": "Add a descriptive title tag (50-60 chars)."})
    elif len(title) < 30:
        issues.append({"severity": "Warning", "area": "Title", "finding": f"Title too short ({len(title)} chars).", "fix": "Expand title to 50-60 characters with primary keyword near the start."})
    elif len(title) > 65:
        issues.append({"severity": "Warning", "area": "Title", "finding": f"Title may be truncated in SERPs ({len(title)} chars).", "fix": "Keep title under 60 characters."})

    # Meta description
    if not meta:
        issues.append({"severity": "Warning", "area": "Meta Description", "finding": "No meta description found.", "fix": "Add a compelling 120-155 character meta description with a CTA."})
    elif len(meta) < 100:
        issues.append({"severity": "Warning", "area": "Meta Description", "finding": f"Meta description too short ({len(meta)} chars).", "fix": "Expand to 120-155 characters."})
    elif len(meta) > 165:
        issues.append({"severity": "Warning", "area": "Meta Description", "finding": f"Meta description may be truncated ({len(meta)} chars).", "fix": "Keep under 155 characters."})

    # H1
    if not h1s:
        issues.append({"severity": "Critical", "area": "H1", "finding": "No H1 tag detected.", "fix": "Add a single, descriptive H1 containing the primary keyword."})
    elif len(h1s) > 1:
        issues.append({"severity": "Warning", "area": "H1", "finding": f"Multiple H1 tags found ({len(h1s)}).", "fix": "Use exactly one H1 per page."})

    # Word count (blog post minimum = 1,500)
    if word_count < 300:
        issues.append({"severity": "Critical", "area": "Content", "finding": f"Very thin content ({word_count} words).", "fix": "Expand content to at least 1,500 words for blog posts."})
    elif word_count < 1000:
        issues.append({"severity": "Warning", "area": "Content", "finding": f"Content may be thin for a blog post ({word_count} words).", "fix": "Aim for 1,500+ words of substantive, unique content."})

    # Author attribution (E-E-A-T)
    if not content.get("author"):
        issues.append({"severity": "Warning", "area": "E-E-A-T", "finding": "No author attribution detected.", "fix": "Add a visible author byline with credentials. Critical post-Dec 2025 E-E-A-T update."})

    # Publish date
    if not content.get("publish_date"):
        issues.append({"severity": "Info", "area": "Freshness", "finding": "No publish date detected in markup.", "fix": "Add visible publish/update date and datePublished in Article schema."})

    # Images: alt text
    missing_alt = [img for img in images if not img.get("alt")]
    if missing_alt:
        issues.append({"severity": "Warning", "area": "Images", "finding": f"{len(missing_alt)} image(s) missing alt text.", "fix": "Add descriptive alt text (10-125 chars) to all non-decorative images."})

    # Images: lazy loading
    no_lazy = [img for img in images if img.get("loading") != "lazy" and img.get("src")]
    if len(no_lazy) > 3:
        issues.append({"severity": "Info", "area": "Images", "finding": f"{len(no_lazy)} image(s) without loading='lazy'.", "fix": "Add loading='lazy' to below-the-fold images to improve LCP."})

    # Structured data
    if not structured_data:
        issues.append({"severity": "Warning", "area": "Schema", "finding": "No JSON-LD structured data found.", "fix": "Add Article/BlogPosting schema with author, datePublished, image, and publisher."})
    else:
        for sd in structured_data:
            if sd.get("status") == "deprecated":
                issues.append({"severity": "Critical", "area": "Schema", "finding": sd["note"], "fix": "Remove deprecated schema type immediately."})
            elif sd.get("status") == "restricted":
                issues.append({"severity": "Warning", "area": "Schema", "finding": sd["note"], "fix": "Remove FAQPage schema unless you are a government or healthcare authority site."})

    # Readability
    fre = readability.get("flesch_reading_ease")
    if fre is not None and fre < 30:
        issues.append({"severity": "Info", "area": "Readability", "finding": f"Content is very difficult to read (Flesch score: {fre}).", "fix": "Simplify sentences. Aim for Flesch score ≥ 50 for broader audience reach."})

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Article SEO Extractor & Keyword Researcher (BS4 + Blogger/WP/Ghost support)"
    )
    parser.add_argument("url", help="URL of the article to analyze")
    parser.add_argument("--keyword", help="Target primary keyword (optional — extracted automatically if omitted)")
    parser.add_argument("--json", action="store_true", help="Output full JSON result")
    parser.add_argument("--no-autocomplete", action="store_true", help="Skip Google Autocomplete lookup")
    args = parser.parse_args()

    html = fetch_html(args.url)
    if not html:
        out = {"error": "Failed to fetch URL", "url": args.url}
        print(json.dumps(out) if args.json else f"Error: Failed to fetch {args.url}")
        sys.exit(1)

    soup = BeautifulSoup(html, "html.parser")

    # ── CMS detection ──────────────────────────────────────────────────────
    cms = detect_cms(soup, args.url)

    # ── Content extraction ─────────────────────────────────────────────────
    content = extract_content(soup, cms)

    # ── Structured data ────────────────────────────────────────────────────
    structured_data = extract_structured_data(soup)

    # ── Full text for keyword extraction + readability ─────────────────────
    all_text_parts = content["h1"] + content["h2s"] + content["h3s"] + content["paragraphs"]
    full_text = " ".join(all_text_parts)

    # ── Readability ────────────────────────────────────────────────────────
    readability = compute_readability(full_text)

    # ── Keyword research ───────────────────────────────────────────────────
    extracted_kws = extract_keywords_frequency(full_text)
    target_kw = (args.keyword.lower() if args.keyword else "") or (extracted_kws[0] if extracted_kws else "")

    related_kws: list[str] = []
    if target_kw and not args.no_autocomplete:
        related_kws = get_google_autocomplete(target_kw)
        # Remove exact match
        related_kws = [k for k in related_kws if k.lower() != target_kw.lower()]

    # Pad with extracted keywords if autocomplete returned few results
    if len(related_kws) < 5:
        extras = [k for k in extracted_kws if k not in related_kws and k != target_kw]
        related_kws.extend(extras)

    # ── SEO issue detection ─────────────────────────────────────────────────
    seo_issues = detect_seo_issues(content, structured_data, readability)

    # ── Build result ───────────────────────────────────────────────────────
    result = {
        "url": args.url,
        "cms_detected": cms,
        "title": content["title"],
        "meta_description": content["meta_description"],
        "og_description": content["og_description"],
        "author": content["author"],
        "publish_date": content["publish_date"],
        "labels": content["labels"],
        "headings": {
            "h1": content["h1"],
            "h2": content["h2s"],
            "h3": content["h3s"],
        },
        "paragraphs": content["paragraphs"],
        "images": content["images"],
        "structured_data": structured_data,
        "readability": readability,
        "target_keyword": target_kw,
        "extracted_keywords": extracted_kws,
        "related_keywords": related_kws[:15],
        "seo_issues": seo_issues,
    }

    if args.json:
        print(json.dumps(result, indent=2))
        return

    # ── Human-readable output ──────────────────────────────────────────────
    issues_by_sev = {"Critical": [], "Warning": [], "Info": []}
    for issue in seo_issues:
        issues_by_sev.get(issue["severity"], issues_by_sev["Info"]).append(issue)

    print(f"\nArticle SEO Analysis — {args.url}")
    print("=" * 60)
    print(f"CMS Detected      : {cms.capitalize()}")
    print(f"Title             : {result['title'][:80]}")
    print(f"Meta Description  : {result['meta_description'][:100]}")
    print(f"Author            : {result['author'] or '⚠️ Not detected'}")
    print(f"Publish Date      : {result['publish_date'] or 'Not detected'}")
    print(f"Labels/Categories : {', '.join(result['labels']) or 'None'}")
    print(f"\nHeadings → H1: {len(content['h1'])}  H2: {len(content['h2s'])}  H3: {len(content['h3s'])}")
    print(f"Word Count        : {readability.get('word_count', 0):,} words")
    print(f"Sentences         : {readability.get('sentence_count', 0)}")
    print(f"Images            : {len(content['images'])}")

    fre = readability.get('flesch_reading_ease')
    fkgl = readability.get('fkgl')
    print(f"\nReadability")
    print(f"  Flesch Reading Ease : {fre}  ({readability.get('grade_label', '')})")
    print(f"  FK Grade Level      : {fkgl}")

    print(f"\nStructured Data ({len(structured_data)} block(s))")
    for sd in structured_data:
        flag = "✅" if sd.get("status") == "active" else "🔴" if sd.get("status") == "deprecated" else "⚠️"
        print(f"  {flag} @type: {sd.get('@type', 'Unknown')}  ({sd.get('status', 'unknown')})")
        if sd.get("note"):
            print(f"     → {sd['note']}")

    print(f"\nTarget Keyword    : '{target_kw}'")
    print(f"Related Keywords  : {', '.join(result['related_keywords'][:8])}")

    print(f"\nSEO Issues Found: {len(seo_issues)}")
    for sev, label in [("Critical", "🔴"), ("Warning", "⚠️"), ("Info", "ℹ️")]:
        for iss in issues_by_sev[sev]:
            print(f"  {label} [{iss['area']}] {iss['finding']}")
            print(f"       Fix: {iss['fix']}")

    print("\nNote: Use --json flag to pipe full output into an LLM for deeper analysis.")


if __name__ == "__main__":
    main()

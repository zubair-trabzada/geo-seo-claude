#!/usr/bin/env python3
"""
Generate an interactive HTML SEO report.

Runs all analysis scripts and aggregates results into a single,
self-contained interactive HTML file with a premium dashboard UI.

Usage:
    python generate_report.py https://example.com
    python generate_report.py https://example.com --output my-report.html
"""

import argparse
import html as html_lib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from urllib.parse import urlparse

import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_script(script_name: str, args: list, timeout: int = 120) -> dict:
    """Run an analysis script and capture JSON output."""
    script_path = os.path.join(SCRIPT_DIR, script_name)
    if not os.path.exists(script_path):
        return {"error": f"Script {script_name} not found"}

    cmd = [sys.executable, script_path] + args + ["--json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        err_msg = result.stderr.strip() or f"Exit code {result.returncode}"
        return {"error": f"[{script_name}] {err_msg}"}
    except subprocess.TimeoutExpired:
        return {"error": f"Script timed out after {timeout}s"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON output from script"}
    except Exception as e:
        return {"error": str(e)}


def fetch_page(url: str) -> str:
    """Fetch page HTML to a temp file, return path."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; SEOBot/1.0)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
        tmp.write(html)
        tmp.close()
        return tmp.name
    except Exception:
        return ""


def detect_environment(html_text: str, url: str) -> dict:
    """Infer site environment/CMS/framework from source signals."""
    lower = (html_text or "").lower()
    domain = urlparse(url).netloc.lower()
    scores = {}
    reasons = {}

    def hit(name: str, points: int, reason: str):
        scores[name] = scores.get(name, 0) + points
        reasons.setdefault(name, []).append(reason)

    # Managed CMS signals
    if any(s in lower for s in ("bloggerusercontent.com", "www.blogger.com", "data:blog.", "b:skin")):
        hit("Blogger", 6, "Blogger template/assets detected")
    if domain.endswith("blogspot.com"):
        hit("Blogger", 4, "Blogspot domain detected")

    if any(s in lower for s in ("wp-content/", "wp-includes/", "wp-json")):
        hit("WordPress", 6, "WordPress core paths detected")
    if re.search(r'generator[^>]+wordpress', lower):
        hit("WordPress", 3, "WordPress generator meta detected")

    if any(s in lower for s in ("cdn.shopify.com", "shopify.theme", "shopify-section")):
        hit("Shopify", 6, "Shopify assets/theme markers detected")

    if any(s in lower for s in ("wixstatic.com", "wix.com", "wixsite")):
        hit("Wix", 6, "Wix assets detected")

    if any(s in lower for s in ("webflow", "w-webflow")):
        hit("Webflow", 5, "Webflow markers detected")

    if any(s in lower for s in ("squarespace.com", "static1.squarespace")):
        hit("Squarespace", 6, "Squarespace assets detected")

    if re.search(r'generator[^>]+ghost', lower) or "ghost/" in lower:
        hit("Ghost", 5, "Ghost generator/assets detected")

    # Framework signals
    if any(s in lower for s in ("/_next/", "__next_data__")):
        hit("Next.js", 6, "Next.js runtime/build markers detected")
    if any(s in lower for s in ("/_nuxt/", "__nuxt")):
        hit("Nuxt", 6, "Nuxt runtime/build markers detected")

    if not scores:
        return {
            "primary": "Unknown",
            "runtime": "Unknown",
            "confidence": "low",
            "signals": ["No strong CMS/framework markers were found in HTML source."],
            "alternatives": [],
        }

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary, top_score = ranked[0]
    confidence = "high" if top_score >= 8 else "medium" if top_score >= 5 else "low"
    runtime_map = {
        "Blogger": "Managed CMS",
        "WordPress": "Managed CMS",
        "Shopify": "Managed CMS / Commerce",
        "Wix": "Managed CMS",
        "Webflow": "Managed CMS",
        "Squarespace": "Managed CMS",
        "Ghost": "Managed CMS",
        "Next.js": "JavaScript Framework",
        "Nuxt": "JavaScript Framework",
    }
    return {
        "primary": primary,
        "runtime": runtime_map.get(primary, "Unknown"),
        "confidence": confidence,
        "signals": reasons.get(primary, [])[:5],
        "alternatives": [name for name, _ in ranked[1:3]],
    }


def _platform_hint(primary: str, area: str) -> str:
    """Provide platform-specific implementation guidance."""
    blogger = {
        "metadata": "In Blogger, update Theme -> Edit HTML and add tags in the <head> section (title template, meta description, OG/Twitter tags).",
        "heading": "In Blogger templates, keep exactly one content H1 per page (post title on posts, site headline on homepage).",
        "headers": "Blogger cannot set most response headers directly. Add Cloudflare in front and configure Response Header Transform Rules.",
        "llms": "Blogger cannot natively serve arbitrary root files. Serve /llms.txt via Cloudflare Workers/Pages or reverse-proxy route.",
        "links": "Fix broken internal links in post content and navigation widgets; update outdated post URLs and labels.",
        "performance": "Optimize Blogger theme widgets/scripts, compress hero/media assets, and defer non-critical third-party scripts.",
    }
    wordpress = {
        "metadata": "Use your SEO plugin (Yoast/RankMath/AIOSEO) or theme templates to set title/meta and OG/Twitter tags.",
        "heading": "Ensure one H1 in theme templates and avoid duplicate H1 in builders/widgets.",
        "headers": "Set headers via server config (Nginx/Apache) or CDN edge rules.",
        "llms": "Create /llms.txt at web root or route it through your web server.",
        "links": "Fix links in menus, content blocks, and internal link plugin data.",
        "performance": "Use caching, image optimization, script deferral, and CWV-focused plugin settings.",
    }
    nextjs = {
        "metadata": "Use the Next.js Metadata API (`app/`) or `next/head` (`pages/`) for title/meta/OG/Twitter tags.",
        "heading": "Set a single semantic H1 in each route component.",
        "headers": "Set security headers in `next.config.js` `headers()` or at your edge/CDN.",
        "llms": "Serve `/llms.txt` from `/public/llms.txt`.",
        "links": "Fix links in route components and content source files; validate with link checks in CI.",
        "performance": "Use `next/image`, dynamic imports, script strategy controls, and reduce main-thread JS.",
    }
    fallback = {
        "metadata": "Update page templates to set complete title/meta/OG/Twitter tags.",
        "heading": "Ensure each page has exactly one descriptive H1 aligned to intent.",
        "headers": "Set missing security headers at web server or CDN layer.",
        "llms": "Add `/llms.txt` at site root with concise site description and key URLs.",
        "links": "Repair or remove broken internal links and refresh outdated navigation targets.",
        "performance": "Compress critical assets, reduce render-blocking scripts, and optimize CWV bottlenecks.",
    }

    platform_map = {
        "Blogger": blogger,
        "WordPress": wordpress,
        "Shopify": fallback,
        "Wix": fallback,
        "Webflow": fallback,
        "Squarespace": fallback,
        "Ghost": fallback,
        "Next.js": nextjs,
        "Nuxt": nextjs,
    }
    return platform_map.get(primary, fallback).get(area, fallback.get(area, ""))


def build_environment_fixes(data: dict) -> list:
    """Build actionable issue fixes tailored to detected environment."""
    env = data.get("environment", {})
    platform = env.get("primary", "Unknown")
    fixes = []

    def add(severity: str, title: str, reason: str, fix: str):
        fixes.append({
            "severity": severity,
            "title": title,
            "reason": reason,
            "fix": fix,
        })

    op = data["sections"].get("onpage", {})
    sec = data["sections"].get("security", {})
    soc = data["sections"].get("social", {})
    llm = data["sections"].get("llms_txt", {})
    bl = data["sections"].get("broken_links", {})
    rd = data["sections"].get("readability", {})
    psi = data["sections"].get("pagespeed", {})

    title = (op.get("title") or "").strip()
    meta = (op.get("meta_description") or "").strip()
    h1s = op.get("h1", []) if isinstance(op.get("h1"), list) else []

    if not h1s:
        add(
            "critical",
            "Missing H1 on page",
            "No primary content heading was detected, which weakens topical clarity.",
            _platform_hint(platform, "heading"),
        )

    if not meta or len(meta) < 110 or len(meta) > 170:
        add(
            "warning",
            "Meta description is missing or out of range",
            "This can reduce SERP CTR and snippet quality.",
            _platform_hint(platform, "metadata"),
        )

    if not title or len(title) < 30 or len(title) > 65:
        add(
            "warning",
            "Title tag needs optimization",
            "Title length/content is likely suboptimal for rankings and click-through.",
            _platform_hint(platform, "metadata"),
        )

    missing_headers = sec.get("headers_missing", {})
    if missing_headers:
        add(
            "critical" if len(missing_headers) >= 4 else "warning",
            f"{len(missing_headers)} security headers missing",
            "Missing headers reduce trust and can expose the site to browser/security risks.",
            _platform_hint(platform, "headers"),
        )

    if not llm.get("exists"):
        add(
            "warning",
            "No llms.txt found",
            "AI crawlers and assistants have no curated machine-readable guidance for key pages.",
            _platform_hint(platform, "llms"),
        )

    broken_count = bl.get("summary", {}).get("broken", 0)
    if broken_count > 0:
        add(
            "critical" if broken_count >= 5 else "warning",
            f"{broken_count} broken links detected",
            "Broken internal links hurt crawl flow and user trust.",
            _platform_hint(platform, "links"),
        )

    og_missing = soc.get("og_missing", [])
    tw_missing = soc.get("twitter_missing", [])
    if og_missing or tw_missing:
        add(
            "warning",
            "Social meta tags are incomplete",
            "Missing OG/Twitter tags weakens social previews and share quality.",
            _platform_hint(platform, "metadata"),
        )

    if psi.get("error"):
        add(
            "info",
            "Performance measurement incomplete",
            "PageSpeed API returned an error, so CWV recommendations are less reliable.",
            "Rerun `pagespeed.py` with `--api-key` and then prioritize LCP/INP/CLS fixes from that output.",
        )

    if rd.get("flesch_reading_ease", 100) < 40 or rd.get("avg_sentence_length", 0) > 25:
        add(
            "warning",
            "Content readability is difficult",
            "Long, complex text can reduce engagement and comprehension.",
            "Rewrite key sections with shorter sentences (15-20 words), shorter paragraphs (2-4 sentences), and clearer subheadings.",
        )

    if not fixes:
        add(
            "pass",
            "No major implementation blockers detected",
            "Core checks look healthy for current scope.",
            "Continue monitoring with regular crawls and keep metadata/security/performance baselines in CI.",
        )

    return fixes


def render_environment_fixes(fixes: list) -> str:
    """Render environment-specific fixes for HTML output."""
    if not fixes:
        return '<p style="color:var(--green)">✅ No environment-specific fixes needed.</p>'

    severity_order = {"critical": 0, "warning": 1, "info": 2, "pass": 3}
    html = ""
    for item in sorted(fixes, key=lambda x: severity_order.get(x.get("severity", "info"), 9)):
        sev = item.get("severity", "info")
        badge = sev.upper()
        title = html_lib.escape(item.get("title", ""), quote=True)
        reason = html_lib.escape(item.get("reason", ""), quote=True)
        fix = html_lib.escape(item.get("fix", ""), quote=True)
        html += (
            f'<div class="issue-item {sev if sev in ("critical","warning","info") else "info"}">'
            f'<span class="issue-badge">{badge}</span>'
            f'<div><strong>{title}</strong><br>'
            f'<span style="color:var(--text-muted)">{reason}</span><br>'
            f'<span><strong>Fix:</strong> {fix}</span></div></div>'
        )
    return html


def collect_data(url: str) -> dict:
    """Run all analysis scripts and collect results."""
    print(f"🔍 Analyzing {url}...")
    data = {
        "url": url,
        "domain": urlparse(url).netloc,
        "timestamp": datetime.now().isoformat(),
        "sections": {},
    }

    # Fetch page for parse_html and readability
    print("  ⏳ Fetching page HTML...")
    html_path = fetch_page(url)
    page_html = ""
    if html_path and os.path.exists(html_path):
        try:
            with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
                page_html = f.read()
        except OSError:
            page_html = ""
    data["environment"] = detect_environment(page_html, url)

    analyses = [
        ("robots", "robots_checker.py", [url]),
        ("security", "security_headers.py", [url]),
        ("social", "social_meta.py", [url]),
        ("redirects", "redirect_checker.py", [url]),
        ("llms_txt", "llms_txt_checker.py", [url]),
        ("broken_links", "broken_links.py", [url, "--workers", "5", "--timeout", "8"]),
        ("internal_links", "internal_links.py", [url, "--depth", "1", "--max-pages", "15"]),
        ("pagespeed", "pagespeed.py", [url, "--strategy", "mobile"]),
        # New analysis scripts (supplementary — failures don't block report)
        ("entity", "entity_checker.py", [url]),
        ("link_profile", "link_profile.py", [url, "--max-pages", "20"]),
        ("hreflang", "hreflang_checker.py", [url]),
        ("duplicate_content", "duplicate_content.py", [url]),
    ]

    # Add parse_html and readability if page was fetched
    if html_path:
        analyses.append(("onpage", "parse_html.py", [html_path, "--url", url]))
        analyses.append(("readability", "readability.py", [html_path]))
        analyses.append(("article", "article_seo.py", [url]))

    for name, script, args in analyses:
        print(f"  ⏳ Running {script}...")
        start = time.time()
        result = run_script(script, args)
        elapsed = round(time.time() - start, 1)
        data["sections"][name] = result
        status = "⚠️ error" if "error" in result and result.get("error") else "✅"
        print(f"  {status} {script} ({elapsed}s)")

    # Cleanup temp file
    if html_path and os.path.exists(html_path):
        os.unlink(html_path)

    data["environment_fixes"] = build_environment_fixes(data)

    return data


def calculate_overall_score(data: dict) -> dict:
    """Calculate overall SEO score from all analyses."""
    scores = {}
    weights = {
        "security": 8,
        "social": 5,
        "robots": 8,
        "broken_links": 10,
        "internal_links": 8,
        "redirects": 3,
        "llms_txt": 5,
        "pagespeed": 13,
        "onpage": 10,
        "readability": 8,
        "entity": 5,
        "link_profile": 7,
        "hreflang": 5,
        "duplicate_content": 5,
    }

    # Security score
    sec = data["sections"].get("security", {})
    scores["security"] = sec.get("score", 0)

    # Social meta score
    soc = data["sections"].get("social", {})
    scores["social"] = soc.get("score", 0)

    # Robots score
    rob = data["sections"].get("robots", {})
    if rob.get("status") == 200:
        base = 60
        if rob.get("sitemaps"):
            base += 20
        ai_managed = sum(1 for s in rob.get("ai_crawler_status", {}).values()
                         if "not managed" not in s)
        base += min(20, ai_managed * 2)
        scores["robots"] = min(100, base)
    elif rob.get("status") == 404:
        scores["robots"] = 20
    else:
        scores["robots"] = 0

    # Article score (informational, not weighted heavily)
    art = data["sections"].get("article", {})
    if art and not art.get("error"):
        art_score = 50
        if art.get("target_keyword"): art_score += 25
        if art.get("lsi_keywords"): art_score += 25
        scores["article"] = min(100, art_score)
    else:
        scores["article"] = 0

    # Broken links score
    bl = data["sections"].get("broken_links", {})
    summary = bl.get("summary", {})
    total = summary.get("total", 1) or 1
    broken = summary.get("broken", 0)
    scores["broken_links"] = max(0, 100 - int((broken / total) * 300))

    # Internal links score
    il = data["sections"].get("internal_links", {})
    il_issues = len(il.get("issues", []))
    scores["internal_links"] = max(0, 100 - il_issues * 20)

    # Redirects score
    red = data["sections"].get("redirects", {})
    red_issues = len(red.get("issues", []))
    scores["redirects"] = max(0, 100 - red_issues * 25)

    # llms.txt score
    llm = data["sections"].get("llms_txt", {})
    if llm.get("exists"):
        scores["llms_txt"] = llm.get("quality", {}).get("score", 0)
    else:
        scores["llms_txt"] = 0

    # PageSpeed score
    psi = data["sections"].get("pagespeed", {})
    scores["pagespeed"] = psi.get("performance_score", 0)

    # On-page score
    op = data["sections"].get("onpage", {})
    if op and not op.get("error"):
        op_score = 50
        if op.get("title"): op_score += 15
        if op.get("meta_description"): op_score += 15
        if op.get("h1"): op_score += 10
        if op.get("canonical"): op_score += 10
        scores["onpage"] = min(100, op_score)
    else:
        scores["onpage"] = 0

    # Readability score
    rd = data["sections"].get("readability", {})
    flesch = rd.get("flesch_reading_ease", 0)
    if flesch >= 60:
        scores["readability"] = 100
    elif flesch >= 30:
        scores["readability"] = 50 + int((flesch - 30) * (50 / 30))
    else:
        scores["readability"] = max(0, int(flesch * (50 / 30)))

    # Entity SEO score
    ent = data["sections"].get("entity", {})
    if ent and not ent.get("error"):
        sameas = ent.get("sameas_analysis", {})
        found = sameas.get("total_found", 0)
        missing = sameas.get("total_missing_critical", 4)
        has_wikidata = 1 if ent.get("wikidata", {}).get("found") else 0
        has_wikipedia = 1 if ent.get("wikipedia", {}).get("found") else 0
        ent_score = min(100, found * 15 + has_wikidata * 25 + has_wikipedia * 25)
        issues_count = len(ent.get("issues", []))
        ent_score = max(0, ent_score - issues_count * 10)
        scores["entity"] = ent_score
    else:
        scores["entity"] = 0

    # Link profile score
    lp = data["sections"].get("link_profile", {})
    if lp and not lp.get("error"):
        avg_links = lp.get("avg_internal_links_per_page", 0)
        orphans = lp.get("orphan_pages", {}).get("count", 0)
        dead_ends = lp.get("dead_end_pages", {}).get("count", 0)
        lp_score = 70
        if avg_links >= 5: lp_score += 15
        elif avg_links >= 3: lp_score += 5
        else: lp_score -= 15
        lp_score -= min(30, orphans * 5)
        lp_score -= min(20, dead_ends * 3)
        scores["link_profile"] = max(0, min(100, lp_score))
    else:
        scores["link_profile"] = 0

    # Hreflang score (skip weight if not applicable)
    hf = data["sections"].get("hreflang", {})
    if hf and not hf.get("error"):
        if hf.get("hreflang_tags_found", 0) > 0:
            summary = hf.get("summary", {})
            hf_score = 100 - summary.get("critical", 0) * 30 - summary.get("high", 0) * 15 - summary.get("medium", 0) * 5
            scores["hreflang"] = max(0, min(100, hf_score))
        else:
            # No hreflang = single language site, skip from weighting
            scores["hreflang"] = None
    else:
        scores["hreflang"] = None

    # Duplicate content score
    dc = data["sections"].get("duplicate_content", {})
    if dc and not dc.get("error"):
        dupes = len(dc.get("near_duplicates", []))
        thin = len(dc.get("thin_pages", []))
        dc_score = 100 - dupes * 20 - thin * 10
        scores["duplicate_content"] = max(0, min(100, dc_score))
    else:
        scores["duplicate_content"] = 0

    # Weighted average (only scored categories)
    total_weight = 0
    weighted_sum = 0
    for k, w in weights.items():
        if k in scores:
            val = scores.get(k)
            if val is not None:
                total_weight += w
                weighted_sum += val * w
    
    overall = round(weighted_sum / total_weight) if total_weight else 0

    # Coerce any None scores to 0 to prevent UI crashes
    for k in list(scores.keys()):
        if scores[k] is None:
            scores[k] = 0

    return {
        "overall": overall,
        "categories": scores,
        "weights": weights,
    }


def render_recommendations(section_data: dict) -> str:
    """Render recommendations from a section's JSON data."""
    recs = section_data.get("recommendations", section_data.get("suggestions", []))
    if isinstance(recs, dict):
        items = [f"{k}: {v}" for k, v in recs.items()]
    elif isinstance(recs, list):
        items = recs
    else:
        items = []
    # Also check opportunities from pagespeed
    opps = section_data.get("opportunities", [])
    if isinstance(opps, list):
        items.extend(opps)

    # Render structured issues (used by entity_checker, hreflang_checker, etc.)
    issues = section_data.get("issues", [])
    issues_html = ""
    if isinstance(issues, list) and issues:
        severity_map = {"critical": "critical", "high": "critical", "warning": "warning", "medium": "warning", "info": "info", "low": "info"}
        for issue in issues[:15]:
            if isinstance(issue, dict):
                sev = severity_map.get(issue.get("severity", "info").lower(), "info")
                badge = html_lib.escape(issue.get("severity", "INFO").upper(), quote=True)
                finding = html_lib.escape(str(issue.get("finding", "")), quote=True)
                fix = html_lib.escape(str(issue.get("fix", "")), quote=True)
                issues_html += (
                    f'<div class="issue-item {sev}">'
                    f'<span class="issue-badge">{badge}</span>'
                    f'<div><strong>{finding}</strong>'
                    f'{f"<br><span style=&quot;color:var(--text-muted)&quot;>Fix: {fix}</span>" if fix else ""}'
                    f'</div></div>'
                )
            elif isinstance(issue, str):
                items.append(issue)

    html = ""
    if issues_html:
        html += f'<div style="margin-top:16px"><h3 style="font-size:0.95rem;margin-bottom:8px;">🔍 Issues Found</h3>{issues_html}</div>'
    if items:
        html += '<div style="margin-top:16px"><h3 style="font-size:0.95rem;margin-bottom:8px;">💡 Recommendations</h3>'
        for item in items[:15]:
            item_str = str(item) if not isinstance(item, str) else item
            html += f'<div class="issue-item info"><span class="issue-badge">FIX</span> {item_str}</div>'
        html += '</div>'
    return html


def render_readability_rewrites(readability_data: dict) -> str:
    """Render concrete sentence replacements for readability fixes."""
    rewrites = readability_data.get("sentence_rewrites", [])
    if not rewrites:
        return ""

    html = (
        '<div style="margin-top:16px">'
        '<h3 style="font-size:0.95rem;margin-bottom:8px;">✍️ What To Replace (Before/After)</h3>'
    )
    for item in rewrites[:5]:
        current = html_lib.escape(str(item.get("current", "")), quote=True)
        suggested = html_lib.escape(str(item.get("suggested", "")), quote=True)
        wc_raw = item.get("current_word_count", "")
        wc_label = f"{wc_raw}w" if isinstance(wc_raw, (int, float)) else str(wc_raw)
        wc = html_lib.escape(wc_label, quote=True)
        html += (
            '<div class="issue-item warning">'
            f'<span class="issue-badge">SENTENCE ({wc})</span>'
            '<div>'
            f'<div><strong>Current:</strong> {current}</div>'
            f'<div style="margin-top:6px;"><strong>Replace with:</strong> {suggested}</div>'
            '</div>'
            '</div>'
        )
    html += "</div>"
    return html


def render_all_recommendations(data: dict) -> str:
    """Render all recommendations from all sections."""
    section_names = {
        "security": "🔒 Security", "social": "📱 Social Meta", "robots": "🤖 Robots",
        "broken_links": "🔗 Links", "internal_links": "🕸️ Internal Links",
        "redirects": "↪️ Redirects", "llms_txt": "🧠 AI Search",
        "pagespeed": "⚡ Performance", "onpage": "📝 On-Page", "readability": "📖 Readability",
        "article": "📄 Article SEO", "entity": "🏛️ Entity SEO",
        "link_profile": "🔗 Link Profile", "hreflang": "🌍 Hreflang",
        "duplicate_content": "📋 Content Uniqueness",
    }
    html = ""
    env_fixes = data.get("environment_fixes", [])
    if env_fixes:
        html += '<h3 style="font-size:0.95rem;margin:16px 0 8px;">🛠️ Environment-Specific Fixes</h3>'
        for item in env_fixes[:8]:
            title = html_lib.escape(item.get("title", ""), quote=True)
            fix = html_lib.escape(item.get("fix", ""), quote=True)
            html += f'<div class="issue-item info"><span class="issue-badge">FIX</span> <strong>{title}</strong>: {fix}</div>'

    for key, label in section_names.items():
        section = data["sections"].get(key, {})
        recs = section.get("recommendations", section.get("suggestions", []))
        if isinstance(recs, dict):
            items = [f"{k}: {v}" for k, v in recs.items()]
        elif isinstance(recs, list):
            items = recs
        else:
            items = []
        opps = section.get("opportunities", [])
        if isinstance(opps, list):
            items.extend(opps)
        if key == "readability":
            for rw in section.get("sentence_rewrites", [])[:3]:
                cur = html_lib.escape(str(rw.get("current", ""))[:180], quote=True)
                sug = html_lib.escape(str(rw.get("suggested", ""))[:180], quote=True)
                items.append(f"Rewrite: {cur} → {sug}")
        if items:
            html += f'<h3 style="font-size:0.95rem;margin:16px 0 8px;">{label}</h3>'
            for item in items[:10]:
                html += f'<div class="issue-item info"><span class="issue-badge">FIX</span> {item}</div>'
    return html if html else '<p style="color:var(--green)">✅ No recommendations — everything looks good!</p>'


def generate_html(data: dict, scores: dict) -> str:
    """Generate the interactive HTML report."""
    domain = data["domain"]
    url = data["url"]
    timestamp = data["timestamp"]
    overall = scores["overall"]

    # Determine overall grade
    if overall >= 90:
        grade, grade_color = "A+", "#22c55e"
    elif overall >= 80:
        grade, grade_color = "A", "#22c55e"
    elif overall >= 70:
        grade, grade_color = "B", "#eab308"
    elif overall >= 60:
        grade, grade_color = "C", "#f97316"
    elif overall >= 50:
        grade, grade_color = "D", "#ef4444"
    else:
        grade, grade_color = "F", "#dc2626"

    # Collect all issues
    all_issues = []
    for section_name, section_data in data["sections"].items():
        issues = section_data.get("issues", [])
        for issue in issues:
            if isinstance(issue, dict):
                # Structured issue from entity_checker, hreflang_checker, etc.
                sev_raw = issue.get("severity", "info").lower()
                severity_map = {"critical": "critical", "high": "critical", "warning": "warning", "medium": "warning", "info": "info", "low": "info"}
                severity = severity_map.get(sev_raw, "info")
                text = f"{issue.get('finding', '')} — Fix: {issue.get('fix', '')}" if issue.get('fix') else issue.get('finding', str(issue))
                all_issues.append({"text": text, "severity": severity, "section": section_name})
            elif isinstance(issue, str):
                severity = "critical" if "🔴" in issue else "warning" if "⚠️" in issue else "info"
                all_issues.append({"text": issue, "severity": severity, "section": section_name})

    critical_count = sum(1 for i in all_issues if i["severity"] == "critical")
    warning_count = sum(1 for i in all_issues if i["severity"] == "warning")
    pass_count = sum(1 for i in all_issues if i["severity"] == "info")

    # Section data extraction
    sec = data["sections"].get("security", {})
    soc = data["sections"].get("social", {})
    rob = data["sections"].get("robots", {})
    bl = data["sections"].get("broken_links", {})
    il = data["sections"].get("internal_links", {})
    red = data["sections"].get("redirects", {})
    llm = data["sections"].get("llms_txt", {})
    psi = data["sections"].get("pagespeed", {})
    op = data["sections"].get("onpage", {})
    rd = data["sections"].get("readability", {})
    art = data["sections"].get("article", {})
    ent = data["sections"].get("entity", {})
    lp = data["sections"].get("link_profile", {})
    hf = data["sections"].get("hreflang", {})
    dc = data["sections"].get("duplicate_content", {})
    env = data.get("environment", {})
    env_fixes = data.get("environment_fixes", [])

    env_primary = html_lib.escape(env.get("primary", "Unknown"), quote=True)
    env_runtime = html_lib.escape(env.get("runtime", "Unknown"), quote=True)
    env_confidence = html_lib.escape(env.get("confidence", "low").upper(), quote=True)
    env_alts = [html_lib.escape(x, quote=True) for x in env.get("alternatives", [])]
    env_signals_html = "".join(
        f'<li class="mono" style="margin:4px 0;">{html_lib.escape(sig, quote=True)}</li>'
        for sig in env.get("signals", [])
    ) or '<li style="color:var(--text-muted)">No strong platform markers found.</li>'
    env_fixes_html = render_environment_fixes(env_fixes)

    # Build issues HTML
    issues_html = ""
    for issue in sorted(all_issues, key=lambda x: {"critical": 0, "warning": 1, "info": 2}[x["severity"]]):
        badge_class = issue["severity"]
        issues_html += f'<div class="issue-item {badge_class}"><span class="issue-badge">{badge_class.upper()}</span> {issue["text"]}</div>\n'

    # Build category cards
    category_labels = {
        "security": ("🔒", "Security Headers"),
        "social": ("📱", "Social Meta"),
        "robots": ("🤖", "Robots & Crawlers"),
        "broken_links": ("🔗", "Broken Links"),
        "internal_links": ("🕸️", "Internal Links"),
        "redirects": ("↪️", "Redirects"),
        "llms_txt": ("🧠", "AI Search (llms.txt)"),
        "pagespeed": ("⚡", "Performance (CWV)"),
        "onpage": ("📝", "On-Page SEO"),
        "readability": ("📖", "Readability"),
        "article": ("📄", "Article Extractor"),
        "entity": ("🏛️", "Entity SEO"),
        "link_profile": ("🔗", "Link Profile"),
        "hreflang": ("🌍", "Hreflang"),
        "duplicate_content": ("📋", "Content Uniqueness"),
    }

    category_cards = ""
    for key, (icon, label) in category_labels.items():
        score = scores["categories"].get(key, 0)
        if score is None:
            score = 0
        if score >= 80:
            ring_color = "#22c55e"
        elif score >= 50:
            ring_color = "#eab308"
        else:
            ring_color = "#ef4444"
        dash = round(score * 2.51327, 1)  # circumference = 251.327
        category_cards += f'''
        <div class="category-card" onclick="scrollToSection('{key}')">
            <svg class="ring" viewBox="0 0 90 90">
                <circle cx="45" cy="45" r="40" fill="none" stroke="var(--card-border)" stroke-width="6"/>
                <circle cx="45" cy="45" r="40" fill="none" stroke="{ring_color}" stroke-width="6"
                    stroke-dasharray="{dash} 251.327" stroke-linecap="round"
                    transform="rotate(-90 45 45)" class="ring-progress"/>
            </svg>
            <div class="ring-label">{score}</div>
            <div class="category-icon">{icon}</div>
            <div class="category-name">{label}</div>
        </div>'''

    # Security details
    security_rows = ""
    for header, value in sec.get("headers_present", {}).items():
        security_rows += f'<tr><td>{header}</td><td><span class="badge pass">Present</span></td><td class="mono">{value[:60]}</td></tr>'
    for header, desc in sec.get("headers_missing", {}).items():
        security_rows += f'<tr><td>{header}</td><td><span class="badge critical">Missing</span></td><td>{desc}</td></tr>'

    # Social meta details
    social_rows = ""
    og = soc.get("og_tags", {})
    tw = soc.get("twitter_tags", {})
    for tag in ["og:title", "og:description", "og:image", "og:url", "og:type", "og:site_name"]:
        val = og.get(tag, "")
        status = '<span class="badge pass">✅</span>' if val else '<span class="badge critical">Missing</span>'
        social_rows += f'<tr><td>{tag}</td><td>{status}</td><td>{val[:60] if val else "—"}</td></tr>'
    for tag in ["twitter:card", "twitter:title", "twitter:description", "twitter:image", "twitter:site"]:
        val = tw.get(tag, "")
        status = '<span class="badge pass">✅</span>' if val else '<span class="badge warning">Missing</span>'
        social_rows += f'<tr><td>{tag}</td><td>{status}</td><td>{val[:60] if val else "—"}</td></tr>'

    # AI Crawlers details
    ai_rows = ""
    for crawler, status in rob.get("ai_crawler_status", {}).items():
        if "blocked" in status:
            badge = '<span class="badge pass">Blocked</span>'
        elif "not managed" in status:
            badge = '<span class="badge warning">Unmanaged</span>'
        else:
            badge = '<span class="badge info">Info</span>'
        ai_rows += f'<tr><td>{crawler}</td><td>{badge}</td><td>{status}</td></tr>'

    # Broken links details
    broken_rows = ""
    for link in bl.get("broken", [])[:20]:
        status = link.get("status") or link.get("error", "?")
        loc = "Internal" if link.get("is_internal") else "External"
        broken_rows += f'<tr><td><span class="badge {"critical" if link.get("is_internal") else "warning"}">{loc}</span></td><td class="mono">{status}</td><td class="link-url">{link["url"][:80]}</td><td>{link.get("anchor_text", "")[:40]}</td></tr>'

    bl_summary = bl.get("summary", {})
    bl_total = bl_summary.get("total", 0)
    bl_healthy = bl_summary.get("healthy", 0)
    bl_broken = bl_summary.get("broken", 0)

    # Internal links details
    orphan_rows = ""
    for orphan in il.get("orphan_candidates", [])[:15]:
        orphan_rows += f'<tr><td class="link-url">{orphan["url"][:80]}</td><td>{orphan["incoming_links"]}</td></tr>'

    il_pages = il.get("pages_crawled", 0)
    il_total = il.get("total_internal_links", 0)
    il_dist = il.get("link_distribution", {})

    # Redirect details
    redirect_rows = ""
    for hop in red.get("chain", []):
        status = hop.get("status", "?")
        time_ms = hop.get("time_ms", 0)
        if hop.get("final"):
            icon_c = "pass" if 200 <= status < 300 else "critical"
            redirect_rows += f'<tr><td>{hop["step"]}</td><td><span class="badge {icon_c}">{status}</span></td><td class="link-url">{hop["url"][:80]}</td><td>{time_ms}ms</td><td>FINAL</td></tr>'
        else:
            redirect_rows += f'<tr><td>{hop["step"]}</td><td><span class="badge warning">{status}</span></td><td class="link-url">{hop["url"][:80]}</td><td>{time_ms}ms</td><td>{hop.get("redirect_type", "")}</td></tr>'

    # Anchor text chart data
    anchor_data = il.get("anchor_texts", {})
    anchor_items = list(anchor_data.items())[:10]
    anchor_bars = ""
    if anchor_items:
        max_val = max(v for _, v in anchor_items) if anchor_items else 1
        for text, count in anchor_items:
            pct = round(count / max_val * 100)
            anchor_bars += f'<div class="bar-row"><span class="bar-label">{text[:25]}</span><div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div><span class="bar-value">{count}</span></div>'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SEO Report — {domain}</title>
<style>
:root {{
    --bg: #0f172a;
    --surface: #1e293b;
    --card: #1e293b;
    --card-border: #334155;
    --text: #f1f5f9;
    --text-muted: #94a3b8;
    --accent: #6366f1;
    --accent-glow: rgba(99, 102, 241, 0.3);
    --green: #22c55e;
    --yellow: #eab308;
    --red: #ef4444;
    --orange: #f97316;
    --radius: 12px;
}}
[data-theme="light"] {{
    --bg: #f8fafc;
    --surface: #ffffff;
    --card: #ffffff;
    --card-border: #e2e8f0;
    --text: #1e293b;
    --text-muted: #64748b;
    --accent-glow: rgba(99, 102, 241, 0.15);
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
}}
.container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}

/* Header */
.header {{
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
    padding: 48px 0 60px;
    text-align: center;
    position: relative;
    overflow: hidden;
}}
.header::before {{
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at center, rgba(99,102,241,0.15) 0%, transparent 70%);
    animation: pulse 4s ease-in-out infinite;
}}
@keyframes pulse {{ 0%,100% {{ opacity: 0.5; }} 50% {{ opacity: 1; }} }}
.header h1 {{ font-size: 2rem; font-weight: 700; color: white; position: relative; }}
.header .domain {{ font-size: 1.1rem; color: #a5b4fc; margin-top: 8px; position: relative; }}
.header .timestamp {{ font-size: 0.85rem; color: #818cf8; margin-top: 4px; position: relative; }}

/* Theme Toggle */
.theme-toggle {{
    position: fixed; top: 16px; right: 16px; z-index: 100;
    background: var(--surface); border: 1px solid var(--card-border);
    border-radius: 50%; width: 44px; height: 44px;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; font-size: 1.2rem; transition: all 0.3s;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}}
.theme-toggle:hover {{ transform: scale(1.1); }}

/* Overall Score */
.score-hero {{
    display: flex; justify-content: center; align-items: center;
    gap: 48px; padding: 40px 0; flex-wrap: wrap;
}}
.score-gauge {{ position: relative; width: 180px; height: 180px; }}
.score-gauge svg {{ width: 100%; height: 100%; }}
.score-gauge .gauge-value {{
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
    text-align: center;
}}
.score-gauge .gauge-number {{ font-size: 3rem; font-weight: 800; color: {grade_color}; }}
.score-gauge .gauge-grade {{ font-size: 1rem; color: var(--text-muted); }}
.score-stats {{ display: flex; gap: 24px; }}
.stat-card {{
    background: var(--card); border: 1px solid var(--card-border);
    border-radius: var(--radius); padding: 20px 28px; text-align: center;
    min-width: 100px;
}}
.stat-value {{ font-size: 2rem; font-weight: 700; }}
.stat-label {{ font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }}
.stat-critical .stat-value {{ color: var(--red); }}
.stat-warning .stat-value {{ color: var(--yellow); }}
.stat-pass .stat-value {{ color: var(--green); }}

/* Category Cards Grid */
.categories {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin: 32px 0; }}
.category-card {{
    background: var(--card); border: 1px solid var(--card-border);
    border-radius: var(--radius); padding: 20px; text-align: center;
    cursor: pointer; transition: all 0.3s;
    position: relative;
}}
.category-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 24px var(--accent-glow); border-color: var(--accent); }}
.category-card .ring {{ width: 70px; height: 70px; margin: 0 auto 8px; }}
.category-card .ring-label {{
    position: absolute; top: 52px; left: 50%; transform: translate(-50%, -50%);
    font-size: 1.1rem; font-weight: 700;
}}
.ring-progress {{ transition: stroke-dasharray 1s ease; }}
.category-icon {{ font-size: 1.3rem; margin: 4px 0; }}
.category-name {{ font-size: 0.8rem; color: var(--text-muted); font-weight: 500; }}

/* Sections */
.section {{
    background: var(--card); border: 1px solid var(--card-border);
    border-radius: var(--radius); margin: 24px 0; overflow: hidden;
}}
.section-header {{
    padding: 20px 24px; cursor: pointer; display: flex;
    align-items: center; justify-content: space-between;
    transition: background 0.2s;
}}
.section-header:hover {{ background: rgba(99,102,241,0.05); }}
.section-header h2 {{ font-size: 1.15rem; font-weight: 600; display: flex; align-items: center; gap: 10px; }}
.section-header .chevron {{ transition: transform 0.3s; font-size: 1.2rem; color: var(--text-muted); }}
.section-header .chevron.open {{ transform: rotate(180deg); }}
.section-body {{ padding: 0 24px 24px; display: none; }}
.section-body.open {{ display: block; animation: fadeIn 0.3s; }}
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-8px); }} to {{ opacity: 1; transform: translateY(0); }} }}

/* Tables */
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 0.9rem; }}
th {{ text-align: left; padding: 10px 12px; border-bottom: 2px solid var(--card-border); color: var(--text-muted); font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; }}
td {{ padding: 10px 12px; border-bottom: 1px solid var(--card-border); vertical-align: top; }}
tr:last-child td {{ border-bottom: none; }}
tr:hover td {{ background: rgba(99,102,241,0.03); }}
.mono {{ font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 0.85rem; }}
.link-url {{ word-break: break-all; max-width: 400px; color: var(--accent); }}

/* Badges */
.badge {{
    display: inline-block; padding: 2px 10px; border-radius: 100px;
    font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
}}
.badge.critical {{ background: rgba(239,68,68,0.15); color: var(--red); }}
.badge.warning {{ background: rgba(234,179,8,0.15); color: var(--yellow); }}
.badge.pass {{ background: rgba(34,197,94,0.15); color: var(--green); }}
.badge.info {{ background: rgba(99,102,241,0.15); color: var(--accent); }}

/* Issues */
.issue-item {{
    padding: 12px 16px; border-radius: 8px; margin: 6px 0;
    font-size: 0.9rem; display: flex; align-items: flex-start; gap: 10px;
}}
.issue-item.critical {{ background: rgba(239,68,68,0.08); border-left: 3px solid var(--red); }}
.issue-item.warning {{ background: rgba(234,179,8,0.08); border-left: 3px solid var(--yellow); }}
.issue-item.info {{ background: rgba(99,102,241,0.08); border-left: 3px solid var(--accent); }}
.issue-badge {{ flex-shrink: 0; }}

/* Bar Chart */
.bar-row {{ display: flex; align-items: center; gap: 10px; margin: 6px 0; }}
.bar-label {{ width: 150px; font-size: 0.85rem; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-muted); }}
.bar-track {{ flex: 1; height: 22px; background: var(--card-border); border-radius: 4px; overflow: hidden; }}
.bar-fill {{ height: 100%; background: linear-gradient(90deg, var(--accent), #818cf8); border-radius: 4px; transition: width 1s ease; }}
.bar-value {{ width: 30px; font-size: 0.85rem; font-weight: 600; }}

/* Summary cards row */
.summary-row {{ display: flex; gap: 16px; margin: 16px 0; flex-wrap: wrap; }}
.summary-item {{
    flex: 1; min-width: 120px; background: var(--bg); border-radius: 8px;
    padding: 16px; text-align: center;
}}
.summary-item .val {{ font-size: 1.5rem; font-weight: 700; }}
.summary-item .lbl {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }}

/* Footer */
.footer {{ text-align: center; padding: 32px 0; color: var(--text-muted); font-size: 0.8rem; }}

@media (max-width: 768px) {{
    .score-hero {{ flex-direction: column; gap: 24px; }}
    .score-stats {{ flex-wrap: wrap; justify-content: center; }}
    .categories {{ grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); }}
    .container {{ padding: 16px; }}
}}
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body>

<div class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">🌙</div>

<div class="header">
    <div class="container">
        <h1>SEO Analysis Report</h1>
        <div class="domain">{domain}</div>
        <div class="timestamp">Generated: {datetime.fromisoformat(timestamp).strftime("%B %d, %Y at %I:%M %p")}</div>
    </div>
</div>

<div class="container">

    <!-- Overall Score -->
    <div class="score-hero">
        <div class="score-gauge">
            <svg viewBox="0 0 200 200">
                <circle cx="100" cy="100" r="85" fill="none" stroke="var(--card-border)" stroke-width="12"/>
                <circle cx="100" cy="100" r="85" fill="none" stroke="{grade_color}" stroke-width="12"
                    stroke-dasharray="{round(overall * 5.341, 1)} 534.07" stroke-linecap="round"
                    transform="rotate(-90 100 100)"/>
            </svg>
            <div class="gauge-value">
                <div class="gauge-number">{overall}</div>
                <div class="gauge-grade">Grade: {grade}</div>
            </div>
        </div>
        <div class="score-stats">
            <div class="stat-card stat-critical">
                <div class="stat-value">{critical_count}</div>
                <div class="stat-label">Critical</div>
            </div>
            <div class="stat-card stat-warning">
                <div class="stat-value">{warning_count}</div>
                <div class="stat-label">Warnings</div>
            </div>
            <div class="stat-card stat-pass">
                <div class="stat-value">{pass_count}</div>
                <div class="stat-label">Info</div>
            </div>
        </div>
    </div>

    <!-- Category Cards -->
    <div class="categories">
        {category_cards}
    </div>

    <!-- Environment Detection -->
    <div class="section" id="section-environment">
        <div class="section-header" onclick="toggleSection('environment')">
            <h2>🧭 Environment Detection (LLM-Inferred)</h2>
            <span class="chevron" id="chevron-environment">▼</span>
        </div>
        <div class="section-body" id="body-environment">
            <div class="summary-row">
                <div class="summary-item"><div class="val">{env_primary}</div><div class="lbl">Primary Platform</div></div>
                <div class="summary-item"><div class="val">{env_runtime}</div><div class="lbl">Runtime Type</div></div>
                <div class="summary-item"><div class="val">{env_confidence}</div><div class="lbl">Confidence</div></div>
                <div class="summary-item"><div class="val">{len(env.get("signals", []))}</div><div class="lbl">Matched Signals</div></div>
            </div>
            <h3 style="margin: 16px 0 8px; font-size: 0.95rem;">Detection Signals</h3>
            <ul style="padding-left:20px;">{env_signals_html}</ul>
            {f'<p style="margin-top:10px;color:var(--text-muted)"><strong>Alternative matches:</strong> {", ".join(env_alts)}</p>' if env_alts else ''}
        </div>
    </div>

    <!-- Environment-specific Fix Plan -->
    <div class="section" id="section-env_fixes">
        <div class="section-header" onclick="toggleSection('env_fixes')">
            <h2>🛠️ Environment-Specific Fix Plan</h2>
            <span class="chevron" id="chevron-env_fixes">▼</span>
        </div>
        <div class="section-body" id="body-env_fixes">
            {env_fixes_html}
        </div>
    </div>

    <!-- Issues Summary -->
    <div class="section" id="section-issues">
        <div class="section-header" onclick="toggleSection('issues')">
            <h2>🚨 All Issues ({len(all_issues)})</h2>
            <span class="chevron" id="chevron-issues">▼</span>
        </div>
        <div class="section-body" id="body-issues">
            {issues_html if issues_html else '<p style="color:var(--text-muted)">No issues found — excellent!</p>'}
        </div>
    </div>

    <!-- Security Headers -->
    <div class="section" id="section-security">
        <div class="section-header" onclick="toggleSection('security')">
            <h2>🔒 Security Headers <span class="badge {"pass" if scores["categories"].get("security",0) >= 80 else "warning" if scores["categories"].get("security",0) >= 50 else "critical"}">{scores["categories"].get("security",0)}/100</span></h2>
            <span class="chevron" id="chevron-security">▼</span>
        </div>
        <div class="section-body" id="body-security">
            <div class="summary-row">
                <div class="summary-item"><div class="val">{"✅" if sec.get("https") else "❌"}</div><div class="lbl">HTTPS</div></div>
                <div class="summary-item"><div class="val">{len(sec.get("headers_present", {}))}</div><div class="lbl">Present</div></div>
                <div class="summary-item"><div class="val">{len(sec.get("headers_missing", {}))}</div><div class="lbl">Missing</div></div>
            </div>
            <table>
                <thead><tr><th>Header</th><th>Status</th><th>Value / Description</th></tr></thead>
                <tbody>{security_rows}</tbody>
            </table>
        </div>
    </div>

    <!-- Social Meta -->
    <div class="section" id="section-social">
        <div class="section-header" onclick="toggleSection('social')">
            <h2>📱 Social Meta Tags <span class="badge {"pass" if scores["categories"].get("social",0) >= 80 else "warning" if scores["categories"].get("social",0) >= 50 else "critical"}">{scores["categories"].get("social",0)}/100</span></h2>
            <span class="chevron" id="chevron-social">▼</span>
        </div>
        <div class="section-body" id="body-social">
            <table>
                <thead><tr><th>Tag</th><th>Status</th><th>Value</th></tr></thead>
                <tbody>{social_rows}</tbody>
            </table>
        </div>
    </div>

    <!-- AI Crawlers -->
    <div class="section" id="section-robots">
        <div class="section-header" onclick="toggleSection('robots')">
            <h2>🤖 Robots & AI Crawlers <span class="badge {"pass" if scores["categories"].get("robots",0) >= 80 else "warning" if scores["categories"].get("robots",0) >= 50 else "critical"}">{scores["categories"].get("robots",0)}/100</span></h2>
            <span class="chevron" id="chevron-robots">▼</span>
        </div>
        <div class="section-body" id="body-robots">
            <div class="summary-row">
                <div class="summary-item"><div class="val">{rob.get("status", "?")}</div><div class="lbl">robots.txt</div></div>
                <div class="summary-item"><div class="val">{len(rob.get("sitemaps", []))}</div><div class="lbl">Sitemaps</div></div>
                <div class="summary-item"><div class="val">{len(rob.get("user_agents", {}))}</div><div class="lbl">User-Agents</div></div>
            </div>
            <h3 style="margin: 16px 0 8px; font-size: 0.95rem;">AI Crawler Management</h3>
            <table>
                <thead><tr><th>Crawler</th><th>Status</th><th>Details</th></tr></thead>
                <tbody>{ai_rows}</tbody>
            </table>
        </div>
    </div>

    <!-- Broken Links -->
    <div class="section" id="section-broken_links">
        <div class="section-header" onclick="toggleSection('broken_links')">
            <h2>🔗 Broken Links <span class="badge {"pass" if bl_broken == 0 else "critical"}">{bl_broken} broken / {bl_total} total</span></h2>
            <span class="chevron" id="chevron-broken_links">▼</span>
        </div>
        <div class="section-body" id="body-broken_links">
            <div class="summary-row">
                <div class="summary-item"><div class="val" style="color:var(--green)">{bl_healthy}</div><div class="lbl">Healthy</div></div>
                <div class="summary-item"><div class="val" style="color:var(--red)">{bl_broken}</div><div class="lbl">Broken</div></div>
                <div class="summary-item"><div class="val" style="color:var(--yellow)">{bl_summary.get("redirected", 0)}</div><div class="lbl">Redirected</div></div>
                <div class="summary-item"><div class="val" style="color:var(--orange)">{bl_summary.get("timeout", 0)}</div><div class="lbl">Timeout</div></div>
            </div>
            {"<table><thead><tr><th>Type</th><th>Status</th><th>URL</th><th>Anchor</th></tr></thead><tbody>" + broken_rows + "</tbody></table>" if broken_rows else '<p style="color:var(--green);margin-top:12px">✅ No broken links found</p>'}
        </div>
    </div>

    <!-- Internal Links -->
    <div class="section" id="section-internal_links">
        <div class="section-header" onclick="toggleSection('internal_links')">
            <h2>🕸️ Internal Link Structure <span class="badge {"pass" if scores["categories"].get("internal_links",0) >= 80 else "warning" if scores["categories"].get("internal_links",0) >= 50 else "critical"}">{scores["categories"].get("internal_links",0)}/100</span></h2>
            <span class="chevron" id="chevron-internal_links">▼</span>
        </div>
        <div class="section-body" id="body-internal_links">
            <div class="summary-row">
                <div class="summary-item"><div class="val">{il_pages}</div><div class="lbl">Pages Crawled</div></div>
                <div class="summary-item"><div class="val">{il_total}</div><div class="lbl">Internal Links</div></div>
                <div class="summary-item"><div class="val">{il_dist.get("avg", 0)}</div><div class="lbl">Avg Links/Page</div></div>
                <div class="summary-item"><div class="val">{len(il.get("orphan_candidates", []))}</div><div class="lbl">Orphan Pages</div></div>
            </div>
            {f'<h3 style="margin:16px 0 8px;font-size:0.95rem;">Top Anchor Texts</h3>' + anchor_bars if anchor_bars else ''}
            {f'<h3 style="margin:16px 0 8px;font-size:0.95rem;">Potential Orphan Pages</h3><table><thead><tr><th>URL</th><th>Incoming Links</th></tr></thead><tbody>{orphan_rows}</tbody></table>' if orphan_rows else ''}
        </div>
    </div>

    <!-- Redirects -->
    <div class="section" id="section-redirects">
        <div class="section-header" onclick="toggleSection('redirects')">
            <h2>↪️ Redirect Chain <span class="badge {"pass" if red.get("total_hops", 0) <= 1 else "warning"}">{red.get("total_hops", 0)} hops</span></h2>
            <span class="chevron" id="chevron-redirects">▼</span>
        </div>
        <div class="section-body" id="body-redirects">
            {f'<table><thead><tr><th>#</th><th>Status</th><th>URL</th><th>Time</th><th>Type</th></tr></thead><tbody>{redirect_rows}</tbody></table>' if redirect_rows else '<p style="color:var(--green)">✅ No redirects — direct access</p>'}
        </div>
    </div>

    <!-- llms.txt -->
    <div class="section" id="section-llms_txt">
        <div class="section-header" onclick="toggleSection('llms_txt')">
            <h2>🧠 AI Search Readiness (llms.txt) <span class="badge {"pass" if llm.get("exists") else "critical"}">{"Found" if llm.get("exists") else "Not Found"}</span></h2>
            <span class="chevron" id="chevron-llms_txt">▼</span>
        </div>
        <div class="section-body" id="body-llms_txt">
            <div class="summary-row">
                <div class="summary-item"><div class="val">{"✅" if llm.get("exists") else "❌"}</div><div class="lbl">llms.txt</div></div>
                <div class="summary-item"><div class="val">{"✅" if llm.get("full_exists") else "❌"}</div><div class="lbl">llms-full.txt</div></div>
                <div class="summary-item"><div class="val">{llm.get("quality", {}).get("score", 0)}</div><div class="lbl">Quality Score</div></div>
            </div>
            {"".join(f'<div class="issue-item warning"><span class="issue-badge">TIP</span> {s}</div>' for s in llm.get("quality", {}).get("suggestions", []))}
        </div>
    </div>

    <!-- PageSpeed / Core Web Vitals -->
    <div class="section" id="section-pagespeed">
        <div class="section-header" onclick="toggleSection('pagespeed')">
            <h2>⚡ Performance & Core Web Vitals <span class="badge {"pass" if scores["categories"].get("pagespeed",0) >= 80 else "warning" if scores["categories"].get("pagespeed",0) >= 50 else "critical"}">{scores["categories"].get("pagespeed",0)}/100</span></h2>
            <span class="chevron" id="chevron-pagespeed">▼</span>
        </div>
        <div class="section-body" id="body-pagespeed">
            <div class="summary-row">
                <div class="summary-item"><div class="val">{psi.get("performance_score", "?")}</div><div class="lbl">Performance</div></div>
                <div class="summary-item"><div class="val">{psi.get("field_data", psi.get("lab_data", {})).get("LCP", "?")}</div><div class="lbl">LCP</div></div>
                <div class="summary-item"><div class="val">{psi.get("field_data", psi.get("lab_data", {})).get("INP", psi.get("field_data", psi.get("lab_data", {})).get("TBT", "?"))}</div><div class="lbl">INP/TBT</div></div>
                <div class="summary-item"><div class="val">{psi.get("field_data", psi.get("lab_data", {})).get("CLS", "?")}</div><div class="lbl">CLS</div></div>
            </div>
            {'<div class="issue-item warning"><span class="issue-badge">NOTE</span> <div><strong>PageSpeed API returned an error or was rate-limited.</strong><br><span style="color:var(--text-muted)">Try running <code>python3 scripts/pagespeed.py URL --api-key YOUR_KEY</code> manually, or rerun the report later. The LLM can still analyze Core Web Vitals by reading the page directly.</span></div></div>' if psi.get('error') or psi.get('performance_score', 0) == 0 else ''}
            {render_recommendations(psi)}
        </div>
    </div>

    <!-- On-Page SEO -->
    <div class="section" id="section-onpage">
        <div class="section-header" onclick="toggleSection('onpage')">
            <h2>📝 On-Page SEO <span class="badge {"pass" if scores["categories"].get("onpage",0) >= 80 else "warning" if scores["categories"].get("onpage",0) >= 50 else "critical"}">{scores["categories"].get("onpage",0)}/100</span></h2>
            <span class="chevron" id="chevron-onpage">▼</span>
        </div>
        <div class="section-body" id="body-onpage">
            <div class="summary-row">
                <div class="summary-item"><div class="val">{'✅' if op.get('title') else '❌'}</div><div class="lbl">Title Tag</div></div>
                <div class="summary-item"><div class="val">{'✅' if op.get('meta_description') else '❌'}</div><div class="lbl">Meta Desc</div></div>
                <div class="summary-item"><div class="val">{'✅' if op.get('h1') else '❌'}</div><div class="lbl">H1</div></div>
                <div class="summary-item"><div class="val">{'✅' if op.get('canonical') else '❌'}</div><div class="lbl">Canonical</div></div>
            </div>
            <table>
                <thead><tr><th>Element</th><th>Value</th><th>Length</th></tr></thead>
                <tbody>
                    <tr><td>Title</td><td>{(op.get('title','') or '—')[:70]}</td><td>{len(op.get('title','') or '')}</td></tr>
                    <tr><td>Meta Description</td><td>{(op.get('meta_description','') or '—')[:100]}</td><td>{len(op.get('meta_description','') or '')}</td></tr>
                    <tr><td>H1</td><td>{(op.get('h1',[''])[0] if isinstance(op.get('h1'), list) and op.get('h1') else op.get('h1','') or '—')[:70]}</td><td>—</td></tr>
                    <tr><td>Canonical</td><td class="link-url">{op.get('canonical','—')[:80]}</td><td>—</td></tr>
                </tbody>
            </table>
            {render_recommendations(op)}
        </div>
    </div>

    <!-- Readability -->
    <div class="section" id="section-readability">
        <div class="section-header" onclick="toggleSection('readability')">
            <h2>📖 Readability <span class="badge {"pass" if scores["categories"].get("readability",0) >= 80 else "warning" if scores["categories"].get("readability",0) >= 50 else "critical"}">{scores["categories"].get("readability",0)}/100</span></h2>
            <span class="chevron" id="chevron-readability">▼</span>
        </div>
        <div class="section-body" id="body-readability">
            <div class="summary-row">
                <div class="summary-item"><div class="val">{rd.get('flesch_reading_ease', '?')}</div><div class="lbl">Flesch Score</div></div>
                <div class="summary-item"><div class="val">{rd.get('flesch_kincaid_grade', '?')}</div><div class="lbl">Grade Level</div></div>
                <div class="summary-item"><div class="val">{rd.get('word_count', '?')}</div><div class="lbl">Words</div></div>
                <div class="summary-item"><div class="val">{rd.get('estimated_reading_time_min', '?')} min</div><div class="lbl">Read Time</div></div>
            </div>
            {render_recommendations(rd)}
            {render_readability_rewrites(rd)}
        </div>
    </div>

    <!-- Article SEO Extractor -->
    <div class="section" id="section-article">
        <div class="section-header" onclick="toggleSection('article')">
            <h2>📄 Article Info & Keywords <span class="badge {"pass" if scores["categories"].get("article",0) >= 80 else "warning" if scores["categories"].get("article",0) >= 50 else "critical"}">{scores["categories"].get("article",0)}/100</span></h2>
            <span class="chevron" id="chevron-article">▼</span>
        </div>
        <div class="section-body" id="body-article">
            <div class="summary-row">
                <div class="summary-item"><div class="val">{art.get('word_count', '?')}</div><div class="lbl">Words</div></div>
                <div class="summary-item"><div class="val">{len(art.get('headings', dict()).get('h2', []))}</div><div class="lbl">H2 Headings</div></div>
                <div class="summary-item"><div class="val">{len(art.get('images', []))}</div><div class="lbl">Images</div></div>
            </div>
            <h3 style="margin: 16px 0 8px; font-size: 0.95rem;">Extracted Keywords</h3>
            <table>
                <thead><tr><th>Target Keyword</th><th>LSI / Related Keywords</th></tr></thead>
                <tbody>
                    <tr>
                        <td style="font-weight: 600; color: var(--accent);">{art.get('target_keyword', '—')}</td>
                        <td>{', '.join(art.get('lsi_keywords', [])) if art.get('lsi_keywords') else '—'}</td>
                    </tr>
                </tbody>
            </table>
            {render_recommendations(art)}
        </div>
    </div>

    <!-- Entity SEO -->
    <div class="section" id="section-entity">
        <div class="section-header" onclick="toggleSection('entity')">
            <h2>🏛️ Entity SEO <span class="badge {"pass" if scores["categories"].get("entity",0) >= 50 else "warning" if scores["categories"].get("entity",0) >= 20 else "critical"}">{scores["categories"].get("entity",0)}/100</span></h2>
            <span class="chevron" id="chevron-entity">▼</span>
        </div>
        <div class="section-body" id="body-entity">
            <div class="summary-row">
                <div class="summary-item"><div class="val">{'✅' if ent.get('wikidata', {}).get('found') else '❌'}</div><div class="lbl">Wikidata</div></div>
                <div class="summary-item"><div class="val">{'✅' if ent.get('wikipedia', {}).get('found') else '❌'}</div><div class="lbl">Wikipedia</div></div>
                <div class="summary-item"><div class="val">{ent.get('sameas_analysis', {}).get('total_found', 0)}</div><div class="lbl">sameAs Links</div></div>
                <div class="summary-item"><div class="val">{len(ent.get('issues', []))}</div><div class="lbl">Issues</div></div>
            </div>
            {render_recommendations(ent)}
        </div>
    </div>

    <!-- Link Profile -->
    <div class="section" id="section-link_profile">
        <div class="section-header" onclick="toggleSection('link_profile')">
            <h2>🔗 Link Profile <span class="badge {"pass" if scores["categories"].get("link_profile",0) >= 70 else "warning" if scores["categories"].get("link_profile",0) >= 40 else "critical"}">{scores["categories"].get("link_profile",0)}/100</span></h2>
            <span class="chevron" id="chevron-link_profile">▼</span>
        </div>
        <div class="section-body" id="body-link_profile">
            <div class="summary-row">
                <div class="summary-item"><div class="val">{lp.get('pages_crawled', '?')}</div><div class="lbl">Pages Crawled</div></div>
                <div class="summary-item"><div class="val">{lp.get('avg_internal_links_per_page', '?')}</div><div class="lbl">Avg Links/Page</div></div>
                <div class="summary-item"><div class="val">{lp.get('orphan_pages', {}).get('count', 0)}</div><div class="lbl">Orphan Pages</div></div>
                <div class="summary-item"><div class="val">{lp.get('dead_end_pages', {}).get('count', 0)}</div><div class="lbl">Dead Ends</div></div>
            </div>
            {render_recommendations(lp)}
        </div>
    </div>

    <!-- Hreflang -->
    <div class="section" id="section-hreflang">
        <div class="section-header" onclick="toggleSection('hreflang')">
            <h2>🌍 Hreflang / International SEO <span class="badge {"pass" if hf.get('hreflang_tags_found', 0) > 0 else "info"}">{hf.get('hreflang_tags_found', 0)} tags</span></h2>
            <span class="chevron" id="chevron-hreflang">▼</span>
        </div>
        <div class="section-body" id="body-hreflang">
            <div class="summary-row">
                <div class="summary-item"><div class="val">{hf.get('implementation_method', 'none')}</div><div class="lbl">Method</div></div>
                <div class="summary-item"><div class="val">{hf.get('hreflang_tags_found', 0)}</div><div class="lbl">Tags Found</div></div>
            </div>
            {'<p style="color:var(--text-muted);margin-top:12px">No hreflang tags found — this is expected for single-language sites.</p>' if hf.get('hreflang_tags_found', 0) == 0 else render_recommendations(hf)}
        </div>
    </div>

    <!-- Duplicate Content -->
    <div class="section" id="section-duplicate_content">
        <div class="section-header" onclick="toggleSection('duplicate_content')">
            <h2>📋 Content Uniqueness <span class="badge {"pass" if len(dc.get('near_duplicates', [])) == 0 else "warning"}">{len(dc.get('near_duplicates', []))} dupes / {len(dc.get('thin_pages', []))} thin</span></h2>
            <span class="chevron" id="chevron-duplicate_content">▼</span>
        </div>
        <div class="section-body" id="body-duplicate_content">
            <div class="summary-row">
                <div class="summary-item"><div class="val">{dc.get('pages_analyzed', '?')}</div><div class="lbl">Pages Analyzed</div></div>
                <div class="summary-item"><div class="val">{len(dc.get('near_duplicates', []))}</div><div class="lbl">Near Duplicates</div></div>
                <div class="summary-item"><div class="val">{len(dc.get('thin_pages', []))}</div><div class="lbl">Thin Pages</div></div>
            </div>
            {render_recommendations(dc)}
        </div>
    </div>

    <!-- Recommendations Summary -->
    <div class="section" id="section-recs">
        <div class="section-header" onclick="toggleSection('recs')">
            <h2>💡 All Recommendations</h2>
            <span class="chevron" id="chevron-recs">▼</span>
        </div>
        <div class="section-body" id="body-recs">
            {render_all_recommendations(data)}
        </div>
    </div>

</div>

<div class="footer">
    <p>Generated by SEO Skill · {datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")}</p>
</div>

<script>
function toggleSection(id) {{
    const body = document.getElementById('body-' + id);
    const chevron = document.getElementById('chevron-' + id);
    body.classList.toggle('open');
    chevron.classList.toggle('open');
}}
function scrollToSection(id) {{
    const el = document.getElementById('section-' + id);
    if (el) {{
        el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        // Auto-open
        const body = document.getElementById('body-' + id);
        const chevron = document.getElementById('chevron-' + id);
        if (!body.classList.contains('open')) {{
            body.classList.add('open');
            chevron.classList.add('open');
        }}
    }}
}}
function toggleTheme() {{
    const html = document.documentElement;
    const btn = document.querySelector('.theme-toggle');
    if (html.getAttribute('data-theme') === 'light') {{
        html.removeAttribute('data-theme');
        btn.textContent = '🌙';
    }} else {{
        html.setAttribute('data-theme', 'light');
        btn.textContent = '☀️';
    }}
}}
// Auto-open issues section
document.getElementById('body-issues').classList.add('open');
document.getElementById('chevron-issues').classList.add('open');
</script>

</body>
</html>'''

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate interactive SEO HTML report")
    parser.add_argument("url", help="Website URL to analyze")
    parser.add_argument("--output", "-o", help="Output filename (default: seo-report-<domain>.html)")

    args = parser.parse_args()

    # Collect all data
    data = collect_data(args.url)

    # Calculate scores
    scores = calculate_overall_score(data)

    # Generate HTML
    html = generate_html(data, scores)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        domain = urlparse(args.url).netloc.replace(".", "_")
        output_path = f"seo-report-{domain}.html"

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ Report saved to: {os.path.abspath(output_path)}")
    print(f"   Overall Score: {scores['overall']}/100")
    print(f"   Open in browser to view the interactive report")


if __name__ == "__main__":
    main()

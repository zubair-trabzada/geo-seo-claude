#!/usr/bin/env python3
"""
Brand-from-URL extractor.

Given a website URL, fetches the homepage and extracts:
  - Company name (og:site_name / <title> / hostname)
  - Tagline + description (og:title / og:description / meta description)
  - Logo URL (og:image / apple-touch-icon / <img> tags / favicon)
  - Brand primary + accent colors (theme-color / CSS vars / logo image)
  - Contact email + phone (regex over page text, domain-preferred)
  - Postal address (schema.org JSON-LD)
  - Social links (LinkedIn, X/Twitter, Facebook, Instagram, YouTube, TikTok)

Writes a JSON file every downstream skill (.imm_brand.json) can reuse.

Usage:
    python brand_extractor.py https://example.com /mnt/user-data/uploads/.imm_brand.json
    python brand_extractor.py https://example.com   # prints to stdout
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; BrandFromURL/1.0; "
        "+brand-extractor; respecting robots.txt)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
TIMEOUT = 15

SOCIAL_DOMAINS = {
    "linkedin": ["linkedin.com"],
    "twitter":  ["twitter.com", "x.com"],
    "facebook": ["facebook.com", "fb.com"],
    "instagram":["instagram.com"],
    "youtube":  ["youtube.com", "youtu.be"],
    "tiktok":   ["tiktok.com"],
}


def _safe_get(url: str) -> requests.Response | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code == 200:
            return r
    except Exception as e:
        sys.stderr.write(f"  ! Could not fetch {url}: {e}\n")
    return None


def _abs(base: str, link: str | None) -> str | None:
    if not link or link.startswith("data:"):
        return None
    return urljoin(base, link)


def _rgb_to_hex(rgb): return "#{:02X}{:02X}{:02X}".format(*rgb)


def _hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _luminance(rgb):
    r, g, b = (c / 255 for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _is_neutral(rgb, tol=18):
    r, g, b = rgb
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < tol and (mx > 230 or mn < 25):
        return True
    if mx - mn < tol:
        return True
    return False


def colors_from_image_bytes(img_bytes: bytes) -> list[str]:
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    except Exception:
        return []
    img.thumbnail((200, 200))
    counts: dict = {}
    for px in img.getdata():
        if len(px) == 4:
            r, g, b, a = px
            if a < 200:
                continue
        else:
            r, g, b = px[:3]
        q = (r // 16 * 16, g // 16 * 16, b // 16 * 16)
        if _is_neutral(q):
            continue
        counts[q] = counts.get(q, 0) + 1
    if not counts:
        return []
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    return [_rgb_to_hex(rgb) for rgb, _ in ranked[:4]]


def _extract_jsonld(soup) -> list[dict]:
    """Pull all JSON-LD blocks from a page."""
    blocks = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        if isinstance(data, list):
            blocks.extend(data)
        elif isinstance(data, dict):
            if "@graph" in data and isinstance(data["@graph"], list):
                blocks.extend(data["@graph"])
            else:
                blocks.append(data)
    return blocks


def _address_from_jsonld(blocks: list[dict]) -> str | None:
    for b in blocks:
        addr = b.get("address") if isinstance(b, dict) else None
        if not addr:
            continue
        if isinstance(addr, str):
            return addr
        if isinstance(addr, dict):
            parts = [
                addr.get("streetAddress"),
                addr.get("addressLocality"),
                addr.get("addressRegion"),
                addr.get("postalCode"),
                addr.get("addressCountry"),
            ]
            joined = ", ".join(p for p in parts if p)
            if joined:
                return joined
    return None


def _social_from_links(soup, base) -> dict[str, str | None]:
    out = {k: None for k in SOCIAL_DOMAINS}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
            continue
        abs_href = _abs(base, href)
        if not abs_href:
            continue
        low = abs_href.lower()
        for platform, domains in SOCIAL_DOMAINS.items():
            if out[platform]:
                continue
            if any(d in low for d in domains):
                out[platform] = abs_href
                break
    return out


def extract_brand(url: str) -> dict:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    result = {
        "source_url": url,
        "company_name": None,
        "tagline": None,
        "description": None,
        "logo_url": None,
        "favicon_url": None,
        "primary_color": None,
        "accent_color": None,
        "all_extracted_colors": [],
        "contact_email": None,
        "contact_phone": None,
        "address": None,
        "social_links": {k: None for k in SOCIAL_DOMAINS},
        "warnings": [],
    }

    resp = _safe_get(url)
    if not resp:
        result["warnings"].append("Could not fetch site (network error or blocked).")
        return result

    soup = BeautifulSoup(resp.text, "html.parser")
    base = resp.url
    jsonld = _extract_jsonld(soup)

    # ── Company name ────────────────────────────────────────────────────────
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        result["company_name"] = og_site["content"].strip()

    if not result["company_name"]:
        for b in jsonld:
            if isinstance(b, dict) and b.get("@type") in ("Organization", "LocalBusiness") and b.get("name"):
                result["company_name"] = b["name"].strip()
                break

    if not result["company_name"]:
        title = soup.find("title")
        if title and title.string:
            t = title.string.strip()
            for sep in [" | ", " — ", " - ", " · ", " :: "]:
                if sep in t:
                    t = t.split(sep, 1)[0].strip()
                    break
            result["company_name"] = t

    if not result["company_name"]:
        host = urlparse(base).hostname or ""
        result["company_name"] = host.replace("www.", "").split(".")[0].title()

    # ── Tagline / description ───────────────────────────────────────────────
    og_desc = (soup.find("meta", property="og:description") or
               soup.find("meta", attrs={"name": "description"}))
    if og_desc and og_desc.get("content"):
        result["description"] = og_desc["content"].strip()[:300]

    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        ogt = og_title["content"].strip()
        if result["company_name"] and ogt.lower() != result["company_name"].lower():
            for sep in [" | ", " — ", " - "]:
                if sep in ogt:
                    parts = ogt.split(sep, 1)
                    if parts[0].strip().lower() == result["company_name"].lower():
                        result["tagline"] = parts[1].strip()
                    break

    # ── Logo ────────────────────────────────────────────────────────────────
    candidates: list[str] = []
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        candidates.append(og_img["content"])
    for link in soup.find_all("link", rel=lambda r: r and "apple-touch-icon" in r):
        if link.get("href"):
            candidates.append(link["href"])
    for img in soup.find_all("img"):
        attrs = " ".join([
            str(img.get("src", "")), str(img.get("alt", "")),
            " ".join(img.get("class", [])), str(img.get("id", "")),
        ]).lower()
        if "logo" in attrs and img.get("src"):
            candidates.append(img["src"])
    icon = (soup.find("link", rel="icon") or
            soup.find("link", rel="shortcut icon") or
            soup.find("link", rel="Shortcut Icon"))
    if icon and icon.get("href"):
        result["favicon_url"] = _abs(base, icon["href"])
        candidates.append(icon["href"])

    for c in candidates:
        abs_url = _abs(base, c)
        if abs_url:
            result["logo_url"] = abs_url
            break

    # ── Colors ──────────────────────────────────────────────────────────────
    extracted: list[str] = []
    theme = soup.find("meta", attrs={"name": "theme-color"})
    if theme and theme.get("content"):
        c = theme["content"].strip()
        if c.startswith("#") and 4 <= len(c) <= 9:
            extracted.append(c.upper())

    for style in soup.find_all("style"):
        css = style.string or ""
        for m in re.finditer(
            r"--(?:brand|primary|accent|theme|main|color-?primary|"
            r"color-?accent|color-?brand)[^:]*:\s*(#[0-9a-fA-F]{3,8})", css
        ):
            extracted.append(m.group(1).upper())

    logo_colors: list[str] = []
    if result["logo_url"]:
        logo_resp = _safe_get(result["logo_url"])
        if logo_resp and logo_resp.content:
            ctype = logo_resp.headers.get("Content-Type", "").lower()
            if "svg" in ctype or result["logo_url"].lower().endswith(".svg"):
                try:
                    import cairosvg
                    png_bytes = cairosvg.svg2png(bytestring=logo_resp.content, output_width=400)
                    logo_colors = colors_from_image_bytes(png_bytes)
                except Exception as e:
                    result["warnings"].append(f"SVG logo found but cairosvg failed: {e}")
            else:
                logo_colors = colors_from_image_bytes(logo_resp.content)

    seen, merged = set(), []
    for c in extracted + logo_colors:
        c = c.upper()
        if c not in seen:
            seen.add(c)
            merged.append(c)
    result["all_extracted_colors"] = merged

    if merged:
        ranked = sorted(merged, key=lambda h: _luminance(_hex_to_rgb(h)))
        result["primary_color"] = ranked[0]
        if len(ranked) > 1:
            primary_lum = _luminance(_hex_to_rgb(ranked[0]))
            accent = max(ranked[1:],
                         key=lambda h: abs(_luminance(_hex_to_rgb(h)) - primary_lum))
            result["accent_color"] = accent
        else:
            result["accent_color"] = ranked[0]

    # ── Contact ─────────────────────────────────────────────────────────────
    text = soup.get_text(" ", strip=True)

    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    emails = [e for e in emails if not any(s in e.lower() for s in
              ("example.com", "sentry.io", "wixpress", "godaddy", "noreply"))]
    if emails:
        domain = (urlparse(base).hostname or "").replace("www.", "")
        domain_emails = [e for e in emails if domain and e.lower().endswith("@" + domain)]
        result["contact_email"] = (domain_emails or emails)[0]

    phones = re.findall(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", text)
    if phones:
        result["contact_phone"] = phones[0]

    # ── Address (schema.org first, then a footer-text fallback) ─────────────
    result["address"] = _address_from_jsonld(jsonld)

    # ── Social links ────────────────────────────────────────────────────────
    result["social_links"] = _social_from_links(soup, base)

    return result


def _lighten(hex_color: str, amount: float = 0.18) -> str:
    """Lighten a hex color by mixing toward white. amount = 0..1."""
    r, g, b = _hex_to_rgb(hex_color)
    r = int(r + (255 - r) * amount)
    g = int(g + (255 - g) * amount)
    b = int(b + (255 - b) * amount)
    return _rgb_to_hex((r, g, b))


def to_whitelabel_schema(brand: dict) -> dict:
    """Map the rich extracted brand dict to the white-label brand.json schema
    that brand_config.load_brand() understands. Detected detail that doesn't
    fit the schema is preserved under _extracted so nothing is lost.
    """
    host = (urlparse(brand["source_url"]).hostname or "").replace("www.", "")
    primary = brand.get("primary_color") or "#19C3B2"
    accent = brand.get("accent_color") or primary
    return {
        "_comment": (
            f"Auto-generated by brand-from-url from {brand['source_url']}. "
            "Edit any field by hand; brand_config.load_brand() deep-merges "
            "this over the defaults. Detected detail is preserved under "
            "_extracted (ignored by load_brand because the key starts with _)."
        ),
        "name":         brand.get("company_name") or "Your Agency",
        "cover_tag":    "Generative Engine Optimization Audit",
        "website":      host or brand["source_url"],
        "phone":        brand.get("contact_phone") or "",
        "contact_name": "",
        "colors": {
            "primary":        primary,
            "primary_bright": _lighten(primary, 0.18),
            "secondary":      accent,
            "text_accent":    primary,
        },
        "_extracted": {
            "source_url":           brand["source_url"],
            "tagline":              brand.get("tagline"),
            "description":          brand.get("description"),
            "logo_url":             brand.get("logo_url"),
            "favicon_url":          brand.get("favicon_url"),
            "all_extracted_colors": brand.get("all_extracted_colors", []),
            "contact_email":        brand.get("contact_email"),
            "address":              brand.get("address"),
            "social_links":         brand.get("social_links", {}),
            "warnings":             brand.get("warnings", []),
        },
    }


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python brand_extractor.py <URL> [output.json] [--raw]\n"
            "  Default output matches the white-label brand.json schema and is\n"
            "  loadable by brand_config.load_brand(). Pass --raw to emit the\n"
            "  full extraction dict instead.",
            file=sys.stderr,
        )
        sys.exit(2)

    raw = "--raw" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--raw"]
    url = args[0]
    out_path = args[1] if len(args) > 1 else None

    sys.stderr.write(f"Extracting brand from {url}...\n")
    brand = extract_brand(url)
    payload = brand if raw else to_whitelabel_schema(brand)

    text = json.dumps(payload, indent=2)
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(text)
        sys.stderr.write(f"Wrote: {out_path}\n")
        print("\n--- Brand summary ---")
        print(f"  Company:  {brand['company_name']}")
        print(f"  Tagline:  {brand['tagline'] or '(none)'}")
        print(f"  Logo URL: {brand['logo_url'] or '(not found)'}")
        print(f"  Primary:  {brand['primary_color'] or '(not found)'}")
        print(f"  Accent:   {brand['accent_color'] or '(not found)'}")
        print(f"  Email:    {brand['contact_email'] or '(not found)'}")
        print(f"  Phone:    {brand['contact_phone'] or '(not found)'}")
        print(f"  Address:  {brand['address'] or '(not found)'}")
        socials = {k: v for k, v in brand["social_links"].items() if v}
        if socials:
            print("  Socials:")
            for k, v in socials.items():
                print(f"    {k}: {v}")
        if brand["warnings"]:
            print(f"  Warnings: {brand['warnings']}")
    else:
        print(text)


if __name__ == "__main__":
    main()

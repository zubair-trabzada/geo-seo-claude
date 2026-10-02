"""
Tests for the brand-from-url extractor (white-label/brand-from-url).

All network access is mocked. The cases cover markup that is valid in the wild
but used to crash the extractor, hostname-based social matching, and colour
handling.
"""

import io
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("PIL")  # brand_extractor imports Pillow at module level

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "white-label", "brand-from-url", "scripts"))
sys.path.insert(0, os.path.join(ROOT, "white-label"))

import brand_config  # noqa: E402
import brand_extractor as be  # noqa: E402
from PIL import Image  # noqa: E402

HOME = "https://example-agency.com"
LOGO_URL = HOME + "/assets/logo.png"
SITE_NAME = '<meta property="og:site_name" content="Example Agency">'


def _response(url, text="", content=None, ctype="text/html; charset=utf-8"):
    resp = MagicMock()
    resp.status_code = 200
    resp.url = url
    resp.text = text
    resp.content = content if content is not None else text.encode()
    resp.headers = {"Content-Type": ctype}
    return resp


def _page(head="", body=""):
    return f"<!doctype html><html><head>{head}</head><body>{body}</body></html>"


def _ld(data):
    return f'<script type="application/ld+json">{json.dumps(data)}</script>'


def _logo_png(left, right):
    """A flat two-colour logo: the left two thirds in one RGB colour, the rest in another."""
    img = Image.new("RGBA", (120, 60), left + (255,))
    for x in range(80, 120):
        for y in range(60):
            img.putpixel((x, y), right + (255,))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _extract(html, extra=None):
    """Run extract_brand against a mocked site. Returns (result, requested_urls)."""
    pages = {HOME: _response(HOME + "/", html)}
    pages.update(extra or {})
    requested = []

    def fake_get(url, **kwargs):
        requested.append(url)
        if url not in pages:
            raise ConnectionError(f"unexpected outbound request: {url}")
        return pages[url]

    with patch.object(be.requests, "get", fake_get):
        return be.extract_brand("example-agency.com"), requested


FULL_PAGE = _page(
    head=SITE_NAME + """
<title>Example Agency | Practical growth tools</title>
<meta property="og:title" content="Example Agency | Practical growth tools for local businesses">
<meta property="og:description" content="We help local businesses grow.">
<meta property="og:image" content="/assets/logo.png">
<meta name="theme-color" content="#0A1E3F">
<style>:root{--primary:#0A1E3F;--accent:#D4AF37;--bg:#ffffff}</style>
""" + _ld({
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Example Agency",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "123 Main Street",
            "addressLocality": "Exampletown",
            "addressRegion": "CA",
            "postalCode": "90210",
            "addressCountry": "US",
        },
    }),
    body="""<p>Email hello@example-agency.com or call (555) 010-1234.</p>
<a href="https://www.linkedin.com/company/example-agency">LinkedIn</a>
<a href="https://x.com/exampleagency">X</a>""",
)


def _full_site():
    # The logo's colours sit a few points off the declared ones, as they would
    # after image resampling.
    logo = _response(LOGO_URL, content=_logo_png((12, 28, 66), (214, 172, 58)), ctype="image/png")
    return _extract(FULL_PAGE, {LOGO_URL: logo})


class TestFullPage:
    def test_core_fields(self):
        result, _ = _full_site()
        assert result["company_name"] == "Example Agency"
        assert result["tagline"] == "Practical growth tools for local businesses"
        assert result["logo_url"] == LOGO_URL
        assert result["contact_email"] == "hello@example-agency.com"
        assert result["contact_phone"] == "(555) 010-1234"
        assert result["address"] == "123 Main Street, Exampletown, CA, 90210, US"
        assert result["social_links"]["linkedin"] == "https://www.linkedin.com/company/example-agency"
        assert result["social_links"]["twitter"] == "https://x.com/exampleagency"
        assert result["warnings"] == []

    def test_declared_colours_win_over_logo_approximations(self):
        result, _ = _full_site()
        assert result["primary_color"] == "#0A1E3F"
        assert result["accent_color"] == "#D4AF37"
        assert result["all_extracted_colors"] == ["#0A1E3F", "#D4AF37"]

    def test_only_the_homepage_and_logo_are_fetched(self):
        _, requested = _full_site()
        assert requested == [HOME, LOGO_URL]

    def test_output_loads_through_brand_config(self, tmp_path):
        result, _ = _full_site()
        path = tmp_path / "brand.json"
        path.write_text(json.dumps(be.to_whitelabel_schema(result)))
        brand = brand_config.load_brand(str(path))
        assert brand["name"] == "Example Agency"
        assert brand["website"] == "example-agency.com"
        assert brand["colors"]["primary"] == "#0A1E3F"
        assert brand["colors"]["secondary"] == "#D4AF37"
        assert "bg_deep" in brand["colors"]  # defaults survive the merge
        assert not any(key.startswith("_") for key in brand)


class TestColours:
    def test_four_digit_hex_variable(self):
        result, _ = _extract(_page(head=SITE_NAME + "<style>:root{--primary:#abcd}</style>"))
        assert result["primary_color"] == "#AABBCC"

    def test_eight_digit_hex_is_reduced_to_six(self):
        result, _ = _extract(_page(head=SITE_NAME + '<meta name="theme-color" content="#0A1E3FFF">'))
        assert result["primary_color"] == "#0A1E3F"

    def test_invalid_hex_is_ignored(self):
        result, _ = _extract(_page(head=SITE_NAME + "<style>:root{--primary:#abcde}</style>"))
        assert result["all_extracted_colors"] == []
        assert result["primary_color"] is None

    def test_flat_logo_reports_its_exact_colours(self):
        html = _page(head=SITE_NAME + '<meta property="og:image" content="/assets/logo.png">')
        logo = _response(LOGO_URL, content=_logo_png((10, 30, 63), (212, 175, 55)), ctype="image/png")
        result, _ = _extract(html, {LOGO_URL: logo})
        assert result["all_extracted_colors"] == ["#0A1E3F", "#D4AF37"]
        assert result["primary_color"] == "#0A1E3F"


class TestJsonLdShapes:
    def test_address_country_as_an_object(self):
        data = {
            "@type": "LocalBusiness",
            "name": "X",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "1 High St",
                "addressLocality": "Leeds",
                "addressCountry": {"@type": "Country", "name": "GB"},
            },
        }
        result, _ = _extract(_page(head=SITE_NAME + _ld(data)))
        assert result["address"] == "1 High St, Leeds, GB"

    def test_numeric_postal_code(self):
        data = {"@type": "Organization", "name": "X", "address": {"streetAddress": "1 Main St", "postalCode": 90210}}
        result, _ = _extract(_page(head=SITE_NAME + _ld(data)))
        assert result["address"] == "1 Main St, 90210"

    def test_list_valued_name_and_type(self):
        data = {"@type": ["Organization", "Corporation"], "name": ["X Ltd", "X"]}
        result, _ = _extract(_page(head=_ld(data)))
        assert result["company_name"] == "X Ltd"


class TestSocialLinks:
    def test_lookalike_domains_are_not_x(self):
        body = (
            '<a href="https://www.dropbox.com/s/abc/brochure.pdf">Brochure</a>'
            '<a href="https://www.wix.com/">Made with Wix</a>'
            '<a href="https://www.fedex.com/track">Track</a>'
        )
        result, _ = _extract(_page(head=SITE_NAME, body=body))
        assert result["social_links"]["twitter"] is None

    def test_profiles_on_subdomains_are_found(self):
        body = (
            '<a href="https://www.x.com/acme">X</a>'
            '<a href="https://m.facebook.com/acme">Facebook</a>'
            '<a href="https://youtu.be/abc123">Video</a>'
        )
        result, _ = _extract(_page(head=SITE_NAME, body=body))
        assert result["social_links"]["twitter"] == "https://www.x.com/acme"
        assert result["social_links"]["facebook"] == "https://m.facebook.com/acme"
        assert result["social_links"]["youtube"] == "https://youtu.be/abc123"


class TestFailureModes:
    def test_unreachable_homepage_returns_a_warning(self):
        def boom(url, **kwargs):
            raise ConnectionError("dns failure")

        with patch.object(be.requests, "get", boom):
            result = be.extract_brand("example-agency.com")
        assert result["warnings"]
        assert be.to_whitelabel_schema(result)["name"] == "Your Agency"

    def test_malformed_link_does_not_crash(self):
        result, _ = _extract(_page(head=SITE_NAME, body='<a href="http://[broken">x</a>'))
        assert result["company_name"] == "Example Agency"

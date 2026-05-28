"""
Tests for SSR (server-side rendering) detection heuristics in fetch_page.py.

Covers the fix for GitHub Issue #19: false positives where sites using
framework-style root divs (id="app", id="root") but serving full HTML via
SSR/prerendering were incorrectly flagged as client-side-only.
"""

import sys
import os
from unittest.mock import patch, MagicMock

# Ensure scripts/ is importable from the worktree
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from fetch_page import fetch_page  # noqa: E402


def _make_response(html: str, status_code: int = 200):
    """Build a minimal mock requests.Response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = html
    mock_resp.history = []
    mock_resp.headers = {}
    mock_resp.url = "http://example.com/"
    return mock_resp


def _fetch_with_html(html: str) -> dict:
    """Call fetch_page with a mocked HTTP response returning the given HTML."""
    with patch("fetch_page.requests.get", return_value=_make_response(html)):
        return fetch_page("http://example.com/")


# ---------------------------------------------------------------------------
# Fixtures — representative HTML pages
# ---------------------------------------------------------------------------

WORDPRESS_BRICKS_HTML = """<!DOCTYPE html>
<html>
<head><title>Bricks Builder Site</title></head>
<body>
  <div id="app">
    <header><nav>Home About Contact</nav></header>
    <main>
      <h1>Welcome to our WordPress site</h1>
      <p>This is a fully server-rendered page built with Bricks Builder on
      WordPress. All the content below is rendered by PHP on the server and
      delivered as complete HTML to the browser and to any crawler or AI bot
      that requests it without running JavaScript.</p>
      <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do
      eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad
      minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip
      ex ea commodo consequat. Duis aute irure dolor in reprehenderit in
      voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
      <p>Excepteur sint occaecat cupidatat non proident, sunt in culpa qui
      officia deserunt mollit anim id est laborum. Additional content here to
      ensure we exceed the two-hundred word threshold used by the heuristic
      so that this page is correctly recognised as server-rendered content
      rather than a blank client-side shell waiting for JavaScript to hydrate
      it.</p>
    </main>
    <footer>Footer content here</footer>
  </div>
</body>
</html>"""

LITESPEED_CACHE_HTML = """<!DOCTYPE html>
<html>
<head><title>LiteSpeed Cache Site</title></head>
<body>
  <div id="root">
    <h1>Product catalogue</h1>
    <p>Our products are fully rendered server-side with LiteSpeed Cache
    providing HTML caching so that every request receives a complete HTML
    document without any client-side JavaScript rendering required. This
    means AI crawlers, search engines, and other bots all get the same rich
    content that a browser with JavaScript disabled would see.</p>
    <p>Product one: A great item that costs twenty dollars and is very
    popular with our customers who appreciate quality and value. Product two:
    Another excellent item at thirty dollars providing outstanding value for
    money. Product three: Premium option at fifty dollars for discerning
    buyers who want the very best quality available on the market today.</p>
    <p>Contact us for bulk pricing on orders of ten units or more. We offer
    free shipping on orders over one hundred dollars within the continental
    United States. International shipping is available at competitive rates
    calculated at checkout.</p>
  </div>
</body>
</html>"""

PRERENDER_SERVICE_HTML = """<!DOCTYPE html>
<html>
<head><title>Pre-rendered React App</title></head>
<body>
  <div id="__next">
    <h1>Server pre-rendered page</h1>
    <p>This Next.js application uses server-side rendering so that the page
    is always delivered as complete HTML. The content here represents the
    kind of rich, indexable text that a pre-rendering service would serve to
    crawlers and AI bots visiting the site. The JavaScript framework hydrates
    on the client but the initial payload is full HTML.</p>
    <p>We have extensive documentation, articles, and guides covering a wide
    range of topics relevant to our users. Our content team publishes new
    material every week ensuring the site remains fresh and authoritative in
    our subject area. This makes us an ideal citation source for AI language
    models seeking reliable, up-to-date information.</p>
    <p>Our technology stack includes modern tools chosen for performance and
    developer experience. We measure core web vitals regularly and optimise
    continuously to ensure fast load times for all visitors regardless of
    their device or network connection speed.</p>
  </div>
</body>
</html>"""

TRUE_CSR_SHELL_HTML = """<!DOCTYPE html>
<html>
<head><title>Client Side App</title></head>
<body>
  <div id="app"></div>
  <script src="/bundle.js"></script>
</body>
</html>"""

TRUE_CSR_ROOT_HTML = """<!DOCTYPE html>
<html>
<head><title>React App</title></head>
<body>
  <div id="root">Loading...</div>
  <script src="/main.js"></script>
</body>
</html>"""

NO_FRAMEWORK_HTML = """<!DOCTYPE html>
<html>
<head><title>Plain HTML Site</title></head>
<body>
  <h1>A standard HTML page</h1>
  <p>This page uses no JavaScript framework at all. It is plain HTML served
  directly by the web server. It should never be flagged as client-rendered
  because it has no framework-style root divs and contains plenty of text
  content for any crawler or AI model to index and use as a citation source.
  The page covers many topics in depth and provides reliable information.</p>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSSRDetectionNonFrameworkSites:
    """Pages with no framework root divs should never be flagged."""

    def test_plain_html_has_ssr_content_true(self):
        result = _fetch_with_html(NO_FRAMEWORK_HTML)
        assert result["has_ssr_content"] is True

    def test_plain_html_has_no_csr_error(self):
        result = _fetch_with_html(NO_FRAMEWORK_HTML)
        csr_errors = [e for e in result["errors"] if "client-side" in e.lower()]
        assert csr_errors == []


class TestSSRDetectionFalsePositives:
    """
    Sites that use framework-style root divs but serve full server-rendered
    HTML must NOT be flagged as client-side rendered (the false-positive case
    described in Issue #19).
    """

    def test_wordpress_bricks_not_flagged(self):
        result = _fetch_with_html(WORDPRESS_BRICKS_HTML)
        assert result["has_ssr_content"] is True, (
            "WordPress/Bricks Builder site should not be flagged as CSR"
        )

    def test_wordpress_bricks_no_csr_error(self):
        result = _fetch_with_html(WORDPRESS_BRICKS_HTML)
        csr_errors = [e for e in result["errors"] if "client-side" in e.lower()]
        assert csr_errors == [], (
            f"Unexpected CSR errors for WordPress site: {csr_errors}"
        )

    def test_litespeed_cache_not_flagged(self):
        result = _fetch_with_html(LITESPEED_CACHE_HTML)
        assert result["has_ssr_content"] is True, (
            "LiteSpeed Cache site (id=root) should not be flagged as CSR"
        )

    def test_litespeed_cache_no_csr_error(self):
        result = _fetch_with_html(LITESPEED_CACHE_HTML)
        csr_errors = [e for e in result["errors"] if "client-side" in e.lower()]
        assert csr_errors == []

    def test_prerender_service_not_flagged(self):
        result = _fetch_with_html(PRERENDER_SERVICE_HTML)
        assert result["has_ssr_content"] is True, (
            "Pre-rendered Next.js site (id=__next) should not be flagged as CSR"
        )

    def test_prerender_service_no_csr_error(self):
        result = _fetch_with_html(PRERENDER_SERVICE_HTML)
        csr_errors = [e for e in result["errors"] if "client-side" in e.lower()]
        assert csr_errors == []


class TestSSRDetectionTruePositives:
    """
    Real client-side shells (minimal/empty root divs, low word count) must
    still be flagged correctly.
    """

    def test_empty_app_div_flagged(self):
        result = _fetch_with_html(TRUE_CSR_SHELL_HTML)
        assert result["has_ssr_content"] is False, (
            "Empty <div id='app'> shell should be flagged as CSR"
        )

    def test_empty_app_div_has_error(self):
        result = _fetch_with_html(TRUE_CSR_SHELL_HTML)
        csr_errors = [e for e in result["errors"] if "client-side" in e.lower()]
        assert len(csr_errors) >= 1

    def test_loading_root_div_flagged(self):
        result = _fetch_with_html(TRUE_CSR_ROOT_HTML)
        assert result["has_ssr_content"] is False, (
            "<div id='root'>Loading...</div> shell should be flagged as CSR"
        )

    def test_loading_root_div_has_error(self):
        result = _fetch_with_html(TRUE_CSR_ROOT_HTML)
        csr_errors = [e for e in result["errors"] if "client-side" in e.lower()]
        assert len(csr_errors) >= 1


class TestSSRWordCountReported:
    """CSR error messages should include the page word count."""

    def test_csr_error_includes_word_count(self):
        result = _fetch_with_html(TRUE_CSR_SHELL_HTML)
        csr_errors = [e for e in result["errors"] if "client-side" in e.lower()]
        assert any("word" in e for e in csr_errors), (
            "CSR error should mention word count"
        )


class TestSSRDecomposeOrderIndependence:
    """
    The SSR check must measure root div content BEFORE decompose() strips
    elements, so that nested script/style tags inside the root don't cause
    the measurement to read zero characters on a real SSR page.
    """

    def test_root_with_nested_scripts_and_rich_text_not_flagged(self):
        html = """<!DOCTYPE html>
<html><head><title>T</title></head>
<body>
  <div id="app">
    <script>window.__STATE__={};</script>
    <style>.x{color:red}</style>
    <h1>Main heading</h1>
    <p>Rich server-rendered paragraph one with many words to ensure the page
    exceeds the minimum threshold for the improved heuristic to correctly
    classify this page as server-rendered rather than a CSR shell waiting for
    JavaScript to populate it with content fetched from an API endpoint.</p>
    <p>Rich server-rendered paragraph two with additional words providing more
    context and information that would be valuable to AI models and search
    engines crawling this fully server-rendered page built with a framework
    that happens to use a div with id app as its mount point.</p>
  </div>
</body></html>"""
        result = _fetch_with_html(html)
        assert result["has_ssr_content"] is True

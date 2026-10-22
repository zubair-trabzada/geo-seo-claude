"""
Tests for decoding non-Latin pages and counting CJK words.

Covers pages served as `Content-Type: text/html` with no charset, which
`requests` decodes as ISO-8859-1 and turns Chinese into mojibake, and
Chinese text that `str.split()` counts as a single word.
"""

import sys
import os
from unittest.mock import patch

import requests
import pytest

# Ensure scripts/ is importable from the worktree
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from text_utils import count_words, detect_encoding, leading_words, response_text  # noqa: E402
from citability_scorer import analyze_page_citability, score_passage  # noqa: E402
from fetch_page import fetch_page, fetch_robots_txt  # noqa: E402
from llmstxt_generator import generate_llmstxt  # noqa: E402


def _response(body: bytes, content_type: str = "text/html", url: str = "https://example.cn/"):
    """Build a real requests.Response with the given raw body."""
    resp = requests.models.Response()
    resp._content = body
    resp.status_code = 200
    resp.headers["Content-Type"] = content_type
    resp.url = url
    # What requests' HTTP adapter does: ISO-8859-1 for text/* without a charset.
    resp.encoding = requests.utils.get_encoding_from_headers(resp.headers)
    return resp


ZH_TITLE = "绿茶入门-示例茶叶网"
ZH_PARAGRAPH = (
    "绿茶是一种不经过发酵的茶，保留了鲜叶中较多的茶多酚和叶绿素，所以茶汤颜色偏绿。"
    "按加工工艺，绿茶通常分为炒青、烘青、晒青和蒸青四类，其中炒青最常见。"
    "例如，冲泡一杯绿茶一般用80 ℃左右的水，3 克茶叶配150毫升水，浸泡2到3分钟即可。"
)
ZH_PAGE = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{ZH_TITLE}</title>
<meta name="description" content="介绍绿茶的种类、冲泡方法和保存技巧。"></head>
<body>
  <h1>什么是绿茶？</h1>
  <p>{ZH_PARAGRAPH}</p>
  <a href="/tea.html">绿茶种类</a>
  <a href="/about.html">关于我们</a>
</body></html>"""


# ---------------------------------------------------------------------------
# Decoding
# ---------------------------------------------------------------------------

class TestResponseText:

    def test_utf8_page_without_header_charset_uses_meta_charset(self):
        resp = _response(ZH_PAGE.encode("utf-8"))
        assert resp.text != ZH_PAGE  # requests alone produces mojibake
        assert response_text(resp) == ZH_PAGE

    def test_gb2312_label_decodes_gbk_only_characters(self):
        # "囧" is in GBK/GB18030 but not in GB2312.
        html = '<meta http-equiv="Content-Type" content="text/html; charset=gb2312"><p>囧字</p>'
        resp = _response(html.encode("gb18030"))
        assert "囧字" in response_text(resp)

    def test_header_charset_wins_over_meta(self):
        html = '<meta charset="utf-8"><p>你好</p>'
        resp = _response(html.encode("gb18030"), "text/html; charset=GBK")
        assert "你好" in response_text(resp)

    def test_shift_jis_meta_decodes_japanese(self):
        html = '<meta charset="Shift_JIS"><p>日本語の文章を正しく読み取ります。</p>'
        assert response_text(_response(html.encode("shift_jis"))) == html

    def test_utf8_bom(self):
        resp = _response(b"\xef\xbb\xbf" + "你好".encode("utf-8"), "text/plain")
        assert response_text(resp) == "你好"

    def test_xml_declaration(self):
        xml = '<?xml version="1.0" encoding="utf-8"?><urlset><url><loc>https://example.cn/帮助</loc></url></urlset>'
        assert detect_encoding(xml.encode("utf-8")) == "utf-8"
        assert "帮助" in response_text(_response(xml.encode("utf-8"), "text/xml"))

    def test_undeclared_charset_falls_back_to_detection(self):
        resp = _response(("<p>" + ZH_PARAGRAPH + "</p>").encode("utf-8"), "text/plain")
        assert ZH_PARAGRAPH in response_text(resp)

    def test_unknown_charset_label_is_ignored(self):
        resp = _response('<meta charset="no-such-charset"><p>你好</p>'.encode("utf-8"))
        assert "你好" in response_text(resp)

    @pytest.mark.parametrize("label", ["base64", "rot13", "hex"])
    @pytest.mark.parametrize("declaration", ["header", "meta"])
    def test_non_text_charset_labels_are_ignored(self, label, declaration):
        html = f'<meta charset="{label}"><p>你好</p>'
        content_type = (
            f"text/html; charset={label}" if declaration == "header" else "text/html"
        )
        assert response_text(_response(html.encode("utf-8"), content_type)) == html

    def test_mock_without_bytes_uses_text(self):
        class Mock:
            text = "plain text"
            content = None
        assert response_text(Mock()) == "plain text"


# ---------------------------------------------------------------------------
# Word counting
# ---------------------------------------------------------------------------

class TestCountWords:

    def test_english_matches_split(self):
        text = "Generative Engine Optimization — is a set of practices (GEO), 2026."
        assert count_words(text) == len(text.split())

    def test_chinese_is_not_one_word(self):
        assert len(ZH_PARAGRAPH.split()) < 10  # whitespace only splits around "80 ℃" etc.
        assert count_words(ZH_PARAGRAPH) > 50

    def test_mixed_text_counts_latin_terms(self):
        # 2 Han characters ≈ 1 word, plus "Python", "Web" and "2.0"; the comma is not a word.
        assert count_words("Python教程，Web 2.0") == 4

    def test_korean_uses_spaces(self):
        assert count_words("안녕하세요 반갑습니다") == 2

    def test_japanese_without_spaces_has_multiple_words(self):
        text = "日本語の文章を正しく数えます。"
        assert len(text.split()) == 1
        assert count_words(text) >= 5

    def test_leading_words_english_unchanged(self):
        text = " ".join(f"w{i}" for i in range(100))
        assert leading_words(text, 30) == " ".join(text.split()[:30])

    def test_leading_words_chinese_is_shorter(self):
        head = leading_words(ZH_PARAGRAPH, 20)
        assert 0 < len(head) < len(ZH_PARAGRAPH)
        assert ZH_PARAGRAPH.startswith(head)

    def test_leading_words_does_not_include_late_answer_in_mixed_text(self):
        prefix = "内容优化需要清晰描述产品功能并提供可靠的数据来源。" * 5
        text = prefix + " The answer is clear. " + "internationalization " * 100
        head = leading_words(text, 60)
        assert prefix.startswith(head)
        assert count_words(head) == 60

    def test_leading_words_keeps_latin_words_whole_in_mixed_text(self):
        prefix = "internationalization " * 20
        text = prefix + "中文" * 100
        assert leading_words(text, 20).rstrip() == prefix.rstrip()


# ---------------------------------------------------------------------------
# Scripts on a Chinese page served without a charset header
# ---------------------------------------------------------------------------

class TestChinesePages:

    def _get(self, *args, **kwargs):
        return _response(ZH_PAGE.encode("utf-8"), url=args[0] if args else "https://example.cn/")

    def test_fetch_page_title_and_word_count(self):
        with patch("fetch_page.requests.get", side_effect=self._get):
            page = fetch_page("https://example.cn/")
        assert page["title"] == ZH_TITLE
        assert page["h1_tags"] == ["什么是绿茶？"]
        assert page["word_count"] > 50

    def test_robots_txt_with_chinese_comment(self):
        body = "# 允许所有爬虫\nUser-agent: *\nAllow: /\n".encode("utf-8")
        with patch("fetch_page.requests.get", return_value=_response(body, "text/plain")):
            robots = fetch_robots_txt("https://example.cn/")
        assert "允许所有爬虫" in robots["content"]

    def test_citability_finds_chinese_blocks(self):
        with patch("citability_scorer.requests.get", side_effect=self._get):
            result = analyze_page_citability("https://example.cn/")
        assert result["total_blocks_analyzed"] == 1
        block = result["all_blocks"][0]
        assert block["heading"] == "什么是绿茶？"
        assert block["preview"].startswith("绿茶是一种")

    def test_llmstxt_generator_keeps_chinese(self):
        with patch("llmstxt_generator.requests.get", side_effect=self._get):
            result = generate_llmstxt("https://example.cn/", max_pages=5)
        assert result["generated_llmstxt"].startswith("# 绿茶入门")
        assert "介绍绿茶的种类" in result["generated_llmstxt"]
        assert "[关于我们](https://example.cn/about.html)" in result["generated_llmstxt"]


# ---------------------------------------------------------------------------
# Citability scoring parity between English and Chinese
# ---------------------------------------------------------------------------

EN_PASSAGE = (
    "Generative Engine Optimization (GEO) is a set of practices that help content get cited by AI search engines "
    "such as ChatGPT and Perplexity. According to a 2025 study by Ahrefs, brand mentions correlate 3x more strongly "
    "with AI visibility than backlinks. In practice, 134-167 word passages that directly answer a question are cited "
    "most often. For example, a SaaS company using FAQ schema saw 40% more citations. Our research found 1,200 sites "
    "improved within 90 days. First, allow AI crawlers. Second, add structured data. Finally, publish original "
    "statistics with named sources."
)
ZH_PASSAGE = (
    "生成式引擎优化（GEO）是一套帮助内容被ChatGPT、Perplexity等AI搜索引擎引用的方法。根据Ahrefs在2025年的研究，"
    "品牌提及与AI可见度的相关性是外链的3倍。实践中，直接回答问题、长度适中的段落最容易被引用。例如，一家使用FAQ结构化数据的"
    "SaaS公司引用量提升了40%。我们的研究发现1200个网站在90天内得到改善。首先，允许AI爬虫访问；其次，添加结构化数据；"
    "最后，发布带有明确来源的原创统计数据。"
)
ZH_WEAK = (
    "这个东西其实大家都知道，它的作用很多，我们也经常会遇到这些情况。那些问题处理起来比较麻烦，"
    "所以他们一般会找人帮忙，这样就比较方便，效果也还可以，总的来说还是不错的，大家可以试一试看看。"
)


class TestChineseScoring:

    def test_answer_after_first_sixty_words_gets_no_early_answer_bonus(self):
        prefix = "内容优化需要清晰描述产品功能并提供可靠的数据来源。" * 5
        suffix = "internationalization " * 100
        with_is = score_passage(prefix + " The answer is clear. " + suffix)
        without_is = score_passage(prefix + " The answer stays clear. " + suffix)
        assert (
            with_is["breakdown"]["answer_block_quality"]
            == without_is["breakdown"]["answer_block_quality"]
        )

    def test_translation_scores_close_to_english(self):
        en = score_passage(EN_PASSAGE, "What is GEO?")
        zh = score_passage(ZH_PASSAGE, "什么是GEO？")
        assert abs(en["word_count"] - zh["word_count"]) <= 15
        assert abs(en["total_score"] - zh["total_score"]) <= 10

    def test_full_width_question_mark_heading(self):
        # ZH_WEAK has no definition sentence, so answer_block_quality isn't capped at 30.
        with_q = score_passage(ZH_WEAK, "这是什么？")["breakdown"]["answer_block_quality"]
        without_q = score_passage(ZH_WEAK, "介绍")["breakdown"]["answer_block_quality"]
        assert with_q == without_q + 10

    def test_vague_chinese_scores_low(self):
        assert score_passage(ZH_WEAK, "介绍")["grade"] == "F"
        assert score_passage(ZH_WEAK, "介绍")["total_score"] < score_passage(ZH_PASSAGE, "介绍")["total_score"] - 30

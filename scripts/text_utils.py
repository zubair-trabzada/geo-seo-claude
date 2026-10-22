"""
Shared text helpers for the GEO scripts: decoding fetched pages and counting
words in languages that don't separate words with spaces.

Decoding: `requests` falls back to ISO-8859-1 for any text/* response whose
Content-Type header has no charset, which turns UTF-8 Chinese, Japanese and
other non-Latin pages into mojibake. `response_text()` decodes the way a
browser does instead.

Word counting: Chinese and Japanese are written without spaces, so
`len(text.split())` counts a whole paragraph as one word. `count_words()`
converts CJK characters into an English-word equivalent so the existing
word-based thresholds (e.g. the 134-167 word citability sweet spot) still
apply. Text without CJK characters is counted exactly as before.
"""

import codecs
import re

# How far into the body to look for <meta charset> or an XML declaration.
_SNIFF_BYTES = 8192

_HEADER_CHARSET = re.compile(r"""charset\s*=\s*["']?\s*([A-Za-z0-9_.:-]+)""", re.I)
_META_CHARSET = re.compile(rb"""<meta[^>]+charset\s*=\s*["']?\s*([A-Za-z0-9_.:-]+)""", re.I)
_XML_ENCODING = re.compile(rb"""^\s*<\?xml[^>]+encoding\s*=\s*["']([A-Za-z0-9_.:-]+)["']""", re.I)

# Pages labelled GB2312 or GBK routinely contain characters only GB18030 (a
# superset of both) can decode, so browsers treat all three as GB18030.
_SUPERSETS = {"gb2312": "gb18030", "gbk": "gb18030"}

_BOMS = (
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)

# Han ideographs plus Japanese kana. Hangul is left out on purpose: Korean
# separates words with spaces, so splitting on whitespace already works.
_CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

# Roughly how many Chinese characters carry the meaning of one English word.
CJK_CHARS_PER_WORD = 1.7


def _codec_name(label):
    """Return a usable Python codec name for a charset label, or None."""
    if isinstance(label, bytes):
        label = label.decode("ascii", "ignore")
    try:
        name = codecs.lookup(label.strip()).name
        # The codec registry also contains transforms such as base64 and rot13.
        # Only accept codecs usable for decoding a response body into text.
        b" ".decode(name, errors="replace")
    except (LookupError, AttributeError, UnicodeError):
        return None
    return _SUPERSETS.get(name, name)


def detect_encoding(body: bytes, content_type: str = ""):
    """Pick the charset a browser would use, or None if nothing declares one.

    Order: byte-order mark, Content-Type header, then the document's own
    <meta charset> / <meta http-equiv> or <?xml encoding?> declaration.
    """
    for bom, name in _BOMS:
        if body.startswith(bom):
            return name

    match = _HEADER_CHARSET.search(content_type or "")
    if match and _codec_name(match.group(1)):
        return _codec_name(match.group(1))

    head = body[:_SNIFF_BYTES]
    for pattern in (_XML_ENCODING, _META_CHARSET):
        match = pattern.search(head)
        if match and _codec_name(match.group(1)):
            return _codec_name(match.group(1))
    return None


def response_text(response) -> str:
    """Decode a `requests` response body the way a browser would.

    Use this instead of `response.text`. Falls back to `requests`' own
    detection, then UTF-8, when the page declares no charset at all.
    """
    body = getattr(response, "content", None)
    if not isinstance(body, (bytes, bytearray)):
        # Mocked responses in tests only provide .text.
        return response.text

    headers = getattr(response, "headers", None) or {}
    encoding = detect_encoding(bytes(body), headers.get("Content-Type", ""))
    if not encoding:
        encoding = _codec_name(getattr(response, "apparent_encoding", None) or "") or "utf-8"
    return bytes(body).decode(encoding, errors="replace")


def has_cjk(text: str) -> bool:
    """True if the text contains any Chinese or Japanese characters."""
    return bool(_CJK.search(text or ""))


def count_words(text: str) -> int:
    """Count words, converting CJK characters into English-word equivalents.

    Text without CJK characters returns exactly `len(text.split())`.
    """
    text = text or ""
    cjk_chars = len(_CJK.findall(text))
    if not cjk_chars:
        return len(text.split())
    # Latin words, numbers and codes mixed into the CJK text ("API", "2.0").
    other_words = [t for t in _CJK.sub(" ", text).split() if re.search(r"\w", t)]
    return len(other_words) + round(cjk_chars / CJK_CHARS_PER_WORD)


def leading_words(text: str, n: int) -> str:
    """Return roughly the first `n` words of the text (CJK-aware)."""
    if not has_cjk(text):
        return " ".join(text.split()[:n])
    total = count_words(text)
    if total <= n:
        return text
    cjk_chars = other_words = 0
    in_other_word = False
    for index, char in enumerate(text):
        if _CJK.match(char):
            cjk_chars += 1
            in_other_word = False
        elif char.isspace():
            in_other_word = False
        elif not in_other_word and re.match(r"\w", char):
            other_words += 1
            in_other_word = True
        if other_words + round(cjk_chars / CJK_CHARS_PER_WORD) > n:
            return text[:index]
    return text

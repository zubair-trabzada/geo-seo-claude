#!/usr/bin/env python3
"""
Citability Scorer — Analyzes content blocks for AI citation readiness.
Scores passages based on how likely AI models are to cite them.

Based on research showing optimal AI-cited passages are:
- 134-167 words long
- Self-contained (extractable without context)
- Fact-rich with specific statistics
- Structured with clear answer patterns

Chinese/Japanese passages are supported: word counts use CJK-aware counting
(see text_utils.count_words) and each heuristic gains Chinese equivalents.
The Chinese patterns only run when a passage contains CJK characters, so
English scores are unchanged.
"""

import sys
import json
import re
from typing import Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

from text_utils import count_words, has_cjk, leading_words, response_text

# Chinese equivalents of the English heuristics in score_passage().
ZH_PATTERNS = {
    # "X 是指…", "X 是一种…", "简称…"
    "definition": r"(?:是指|指的是|是一种|是一类|是一个|是一项|被定义为|定义为|简称|全称(?:是|为)|又称|也称|所谓)",
    "early_answer": [
        r"(?:是|指|意味着)",
        r"\d+(?:\.\d+)?\s*(?:万|亿)",
        r"[¥￥]\s?[\d,]+|[\d,]+(?:\.\d+)?\s*(?:万|亿)?元",
    ],
    "claim": (
        r"(?:根据|据)[^，。；]{0,15}(?:统计|报告|研究|数据|调查)"
        r"|研究(?:表明|显示|发现|指出)|数据(?:显示|表明)|调查(?:显示|发现)|报告(?:显示|指出)"
    ),
    "pronouns": (
        r"它们?|他们|她们|(?<!其)[他她](?!们)|(?<![应活])该|(?<![因如从彼])此|这些|那些"
        r"|这[个种类项样里]|那[个种类项样里]|(?<![尤极])其(?![他中实次余])"
    ),
    "proper_nouns": [
        r"(?<![A-Za-z])[A-Z][A-Za-z0-9]*(?:[.\-][A-Za-z0-9]+)*",  # GEO, ChatGPT, HTML5
        r"[\u4e00-\u9fff]{2,10}(?:公司|集团|大学|学院|研究院|研究所|协会|医院|银行)",
        r"《[^》]{2,40}》",  # titles of books, articles and reports
    ],
    "sentence_end": r"[。！？!?]+|\.(?=\s|$)",
    "transitions": r"(?:首先|其次|再次|然后|最后|另外|此外|同时|第一|第二|第三)",
    "numbered": (
        r"(?:^|[\s：:。；;，,])(?:[（(][一二三四五六七八九十\d]{1,2}[）)]|[一二三四五六七八九十\d]{1,2}[、．]|\d{1,2}\.(?=[\u4e00-\u9fff]))"
        r"|第[一二三四五六七八九十\d]+步"
    ),
    "money": r"[¥￥]\s?[\d,]+(?:\.\d+)?|[\d,]+(?:\.\d+)?\s*(?:万|亿)?元",
    "number_context": (
        r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:万|亿)?\s*"
        r"(?:个|家|位|名|项|种|次|倍|天|周|小时|分钟|人|公里|公斤|千克|克|米)(?![A-Za-z])"
    ),
    "year": r"20(?:2[3-6]|1\d)\s*年",
    "sources": [
        r"(?:根据|按照)[^，。；]{1,20}(?:报告|数据|研究|调查|统计)",
        r"《[^》]{2,40}》",
        r"[\u4e00-\u9fff]{2,12}(?:大学|研究院|研究所|协会)的?(?:研究|报告|调查|数据)",
    ],
    "original_data": (
        r"我们的?(?:研究|调查|数据|分析|统计)"
        r"|我们(?:发现|调查了|分析了|统计了|对比了|记录了)"
        r"|本(?:文|站|团队)的?(?:研究|调查|统计|数据)"
    ),
    "case": r"(?:案例|例如|比如|举例|譬如|实践中|实际使用|亲身体验)",
    "tool": r"(?:使用|采用|借助|利用)[^，。；]{0,8}?(?:[A-Z][A-Za-z0-9]+|软件|工具|应用|平台)",
}


def score_passage(text: str, heading: Optional[str] = None) -> dict:
    """Score a single passage for AI citability (0-100)."""
    word_count = count_words(text)
    cjk = has_cjk(text)

    scores = {
        "answer_block_quality": 0,
        "self_containment": 0,
        "structural_readability": 0,
        "statistical_density": 0,
        "uniqueness_signals": 0,
    }

    # === 1. Answer Block Quality (30%) ===
    abq_score = 0

    # Check for definition patterns ("X is...", "X refers to...", "X means...")
    definition_patterns = [
        r"\b\w+\s+is\s+(?:a|an|the)\s",
        r"\b\w+\s+refers?\s+to\s",
        r"\b\w+\s+means?\s",
        r"\b\w+\s+(?:can be |are )?defined\s+as\s",
        r"\bin\s+(?:simple|other)\s+(?:terms|words)\s*,",
    ]
    if cjk:
        definition_patterns.append(ZH_PATTERNS["definition"])
    for pattern in definition_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            abq_score += 15
            break

    # Check if answer appears early (first 60 words)
    first_60_words = leading_words(text, 60)
    early_patterns = [
        r"\b(?:is|are|was|were|means?|refers?)\b",
        r"\d+%",
        r"\$[\d,]+",
        r"\d+\s+(?:million|billion|thousand)",
    ]
    if cjk:
        early_patterns += ZH_PATTERNS["early_answer"]
    if any(re.search(p, first_60_words, re.IGNORECASE) for p in early_patterns):
        abq_score += 15

    # Question-based heading bonus
    if heading and heading.endswith(("?", "？")):
        abq_score += 10

    # Clear, direct sentence structure
    sentences = re.split(ZH_PATTERNS["sentence_end"] if cjk else r"[.!?]+", text)
    short_clear_sentences = sum(
        1 for s in sentences if 5 <= count_words(s) <= 25
    )
    if sentences:
        clarity_ratio = short_clear_sentences / len(sentences)
        abq_score += int(clarity_ratio * 10)

    # Has specific, quotable claim
    if re.search(
        r"(?:according to|research shows|studies? (?:show|indicate|suggest|found)|data (?:shows|indicates|suggests))",
        text,
        re.IGNORECASE,
    ) or (cjk and re.search(ZH_PATTERNS["claim"], text)):
        abq_score += 10

    scores["answer_block_quality"] = min(abq_score, 30)

    # === 2. Self-Containment (25%) ===
    sc_score = 0

    # Optimal word count (134-167 words)
    if 134 <= word_count <= 167:
        sc_score += 10
    elif 100 <= word_count <= 200:
        sc_score += 7
    elif 80 <= word_count <= 250:
        sc_score += 4
    elif word_count < 30 or word_count > 400:
        sc_score += 0
    else:
        sc_score += 2

    # Low pronoun density (fewer pronouns = more self-contained)
    pronoun_count = len(
        re.findall(
            r"\b(?:it|they|them|their|this|that|these|those|he|she|his|her)\b",
            text,
            re.IGNORECASE,
        )
    )
    if cjk:
        pronoun_count += len(re.findall(ZH_PATTERNS["pronouns"], text))
    if word_count > 0:
        pronoun_ratio = pronoun_count / word_count
        if pronoun_ratio < 0.02:
            sc_score += 8
        elif pronoun_ratio < 0.04:
            sc_score += 5
        elif pronoun_ratio < 0.06:
            sc_score += 3

    # Contains named entities (proper nouns, brands, specific terms)
    proper_nouns = len(re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text))
    if cjk:
        # No capital letters in Chinese: count Latin terms, organisations and 《titles》.
        zh_entities = sum(len(re.findall(p, text)) for p in ZH_PATTERNS["proper_nouns"])
        proper_nouns = max(proper_nouns, zh_entities)
    if proper_nouns >= 3:
        sc_score += 7
    elif proper_nouns >= 1:
        sc_score += 4

    scores["self_containment"] = min(sc_score, 25)

    # === 3. Structural Readability (20%) ===
    sr_score = 0

    # Sentence count and length distribution
    if sentences:
        avg_sentence_length = word_count / len(sentences)
        if 10 <= avg_sentence_length <= 20:
            sr_score += 8
        elif 8 <= avg_sentence_length <= 25:
            sr_score += 5
        else:
            sr_score += 2

    # Contains list-like structures
    if re.search(r"(?:first|second|third|finally|additionally|moreover|furthermore)", text, re.IGNORECASE) or (
        cjk and re.search(ZH_PATTERNS["transitions"], text)
    ):
        sr_score += 4

    # Contains numbered items or bullet-like content
    if re.search(r"(?:\d+[\.\)]\s|\b(?:step|tip|point)\s+\d+)", text, re.IGNORECASE) or (
        cjk and re.search(ZH_PATTERNS["numbered"], text)
    ):
        sr_score += 4

    # Paragraph breaks (indicates structure)
    if "\n" in text:
        sr_score += 4

    scores["structural_readability"] = min(sr_score, 20)

    # === 4. Statistical Density (15%) ===
    sd_score = 0

    # Percentages
    pct_count = len(re.findall(r"\d+(?:\.\d+)?%", text))
    sd_score += min(pct_count * 3, 6)

    # Dollar amounts
    dollar_count = len(re.findall(r"\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|M|B|K))?", text))
    if cjk:
        dollar_count += len(re.findall(ZH_PATTERNS["money"], text))
    sd_score += min(dollar_count * 3, 5)

    # Other numbers with context
    number_count = len(re.findall(r"\b\d+(?:,\d{3})*(?:\.\d+)?\s+(?:users|customers|pages|sites|companies|businesses|people|percent|times|x\b)", text, re.IGNORECASE))
    if cjk:
        number_count += len(re.findall(ZH_PATTERNS["number_context"], text))
    sd_score += min(number_count * 2, 4)

    # Year references (indicates timeliness)
    year_count = len(re.findall(r"\b20(?:2[3-6]|1\d)\b", text))
    if cjk:
        year_count += len(re.findall(ZH_PATTERNS["year"], text))
    if year_count > 0:
        sd_score += 2

    # Named sources
    source_patterns = [
        r"(?:according to|per|from|by)\s+[A-Z]",
        r"(?:Gartner|Forrester|McKinsey|Harvard|Stanford|MIT|Google|Microsoft|OpenAI|Anthropic)",
        r"\([A-Z][a-z]+(?:\s+\d{4})?\)",
    ]
    if cjk:
        source_patterns += ZH_PATTERNS["sources"]
    for pattern in source_patterns:
        if re.search(pattern, text):
            sd_score += 2

    scores["statistical_density"] = min(sd_score, 15)

    # === 5. Uniqueness Signals (10%) ===
    us_score = 0

    # Original data indicators
    if re.search(
        r"(?:our (?:research|study|data|analysis|survey|findings)|we (?:found|discovered|analyzed|surveyed|measured))",
        text,
        re.IGNORECASE,
    ) or (cjk and re.search(ZH_PATTERNS["original_data"], text)):
        us_score += 5

    # Case study or example indicators
    if re.search(
        r"(?:case study|for example|for instance|in practice|real-world|hands-on)",
        text,
        re.IGNORECASE,
    ) or (cjk and re.search(ZH_PATTERNS["case"], text)):
        us_score += 3

    # Specific tool/product mentions (shows practical experience)
    if re.search(r"(?:using|with|via|through)\s+[A-Z][a-z]+", text) or (
        cjk and re.search(ZH_PATTERNS["tool"], text)
    ):
        us_score += 2

    scores["uniqueness_signals"] = min(us_score, 10)

    # === Calculate total ===
    total = sum(scores.values())

    # Determine grade
    if total >= 80:
        grade = "A"
        label = "Highly Citable"
    elif total >= 65:
        grade = "B"
        label = "Good Citability"
    elif total >= 50:
        grade = "C"
        label = "Moderate Citability"
    elif total >= 35:
        grade = "D"
        label = "Low Citability"
    else:
        grade = "F"
        label = "Poor Citability"

    return {
        "heading": heading,
        "word_count": word_count,
        "total_score": total,
        "grade": grade,
        "label": label,
        "breakdown": scores,
        "preview": leading_words(text, 30) + ("..." if word_count > 30 else ""),
    }


def analyze_page_citability(url: str) -> dict:
    """Analyze all content blocks on a page for citability."""
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            },
            timeout=30,
        )
        response.raise_for_status()
    except Exception as e:
        return {"error": f"Failed to fetch page: {str(e)}"}

    soup = BeautifulSoup(response_text(response), "lxml")

    # Remove non-content elements
    for element in soup.find_all(
        ["script", "style", "nav", "footer", "header", "aside", "form"]
    ):
        element.decompose()

    # Extract content blocks
    blocks = []
    current_heading = "Introduction"
    current_paragraphs = []

    for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "table"]):
        if element.name.startswith("h"):
            # Save previous section
            if current_paragraphs:
                combined = " ".join(current_paragraphs)
                if count_words(combined) >= 20:
                    blocks.append(
                        {"heading": current_heading, "content": combined}
                    )
            current_heading = element.get_text(strip=True)
            current_paragraphs = []
        else:
            text = element.get_text(strip=True)
            if text and count_words(text) >= 5:
                current_paragraphs.append(text)

    # Last block
    if current_paragraphs:
        combined = " ".join(current_paragraphs)
        if count_words(combined) >= 20:
            blocks.append({"heading": current_heading, "content": combined})

    # Score each block
    scored_blocks = []
    for block in blocks:
        score = score_passage(block["content"], block["heading"])
        scored_blocks.append(score)

    # Calculate page-level metrics
    if scored_blocks:
        avg_score = sum(b["total_score"] for b in scored_blocks) / len(scored_blocks)
        top_blocks = sorted(scored_blocks, key=lambda x: x["total_score"], reverse=True)[:5]
        bottom_blocks = sorted(scored_blocks, key=lambda x: x["total_score"])[:5]

        # Optimal passage count (134-167 words)
        optimal_count = sum(
            1 for b in scored_blocks if 134 <= b["word_count"] <= 167
        )
    else:
        avg_score = 0
        top_blocks = []
        bottom_blocks = []
        optimal_count = 0

    # Grade distribution
    grade_dist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for block in scored_blocks:
        grade_dist[block["grade"]] += 1

    return {
        "url": url,
        "total_blocks_analyzed": len(scored_blocks),
        "average_citability_score": round(avg_score, 1),
        "optimal_length_passages": optimal_count,
        "grade_distribution": grade_dist,
        "top_5_citable": top_blocks,
        "bottom_5_citable": bottom_blocks,
        "all_blocks": scored_blocks,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python citability_scorer.py <url>")
        print("Returns JSON with citability analysis for all content blocks.")
        sys.exit(1)

    url = sys.argv[1]
    result = analyze_page_citability(url)
    print(json.dumps(result, indent=2, default=str))

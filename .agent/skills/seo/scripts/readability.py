#!/usr/bin/env python3
"""
Content readability analysis — pure Python, no external NLP dependencies.

Computes Flesch-Kincaid Reading Ease, grade level, sentence/paragraph stats.
Accepts HTML file, plain text file, or stdin.

Usage:
    python readability.py page.html --json
    python readability.py --url https://example.com --json
    python readability.py --text "Your text here"
    cat page.html | python readability.py --json
"""

import argparse
import json
import re
import sys
import urllib.request

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def count_syllables(word: str) -> int:
    """Count syllables in a word using heuristic rules."""
    word = word.lower().strip()
    if not word:
        return 0
    if len(word) <= 2:
        return 1

    # Remove trailing silent e
    if word.endswith("e"):
        word = word[:-1]

    # Count vowel groups
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel

    return max(1, count)


def extract_text(html: str) -> str:
    """Extract readable text from HTML, stripping scripts/styles."""
    if HAS_BS4:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    else:
        # Basic fallback: strip tags
        text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()


def split_sentences(text: str) -> list:
    """Split text into sentences while preserving punctuation."""
    chunks = re.split(r'(?<=[.!?])\s+', text.strip())
    return [c.strip() for c in chunks if c.strip()]


def suggest_sentence_rewrite(sentence: str) -> str:
    """Generate a simple, shorter rewrite by splitting long sentences."""
    tokens = sentence.strip().split()
    if len(tokens) <= 22:
        return sentence.strip()

    conjunctions = {"and", "but", "because", "which", "that", "while", "although", "however", "so"}
    split_points = []
    for i, tok in enumerate(tokens):
        clean = tok.strip(",;:").lower()
        if tok.endswith((",", ";", ":")) or clean in conjunctions:
            split_points.append(i)

    mid = len(tokens) // 2
    if split_points:
        split_idx = min(split_points, key=lambda i: abs(i - mid))
        if split_idx < 8 or split_idx > len(tokens) - 8:
            split_idx = mid
    else:
        split_idx = mid

    first_tokens = tokens[:split_idx]
    second_tokens = tokens[split_idx:]
    if second_tokens and second_tokens[0].strip(",;:").lower() in conjunctions:
        second_tokens = second_tokens[1:]

    first = " ".join(first_tokens).rstrip(",;:.")
    second = " ".join(second_tokens).lstrip(",;: ")
    if not second:
        first = " ".join(tokens[:mid]).rstrip(",;:.")
        second = " ".join(tokens[mid:]).lstrip(",;: ")

    first = first[0].upper() + first[1:] if first else ""
    second = second[0].upper() + second[1:] if second else ""
    if first and second:
        return f"{first}. {second}."
    return sentence.strip()


def is_navigation_noise(sentence: str) -> bool:
    """Heuristic filter for nav/widget/template text that should not be rewritten."""
    s = sentence.strip()
    low = s.lower()
    if not s:
        return True

    # Common homepage widget/navigation phrases
    nav_phrases = [
        "read more", "recent posts", "older posts", "subscribe to",
        "comments (atom)", "labels", "search for a post", "widget",
        "your browser does not support javascript",
    ]
    if any(p in low for p in nav_phrases):
        return True

    # Menu/list-like chunks with many line breaks are low-signal prose
    if s.count("\n") >= 2:
        return True

    tokens = re.findall(r"\b[a-zA-Z]+\b", s)
    if not tokens:
        return True

    # Excessively keyword-list style content
    unique_ratio = len(set(t.lower() for t in tokens)) / max(1, len(tokens))
    if len(tokens) >= 25 and unique_ratio > 0.85:
        return True

    return False


def analyze_readability(text: str) -> dict:
    """
    Analyze text readability.

    Returns:
        Dictionary with readability metrics and assessment
    """
    result = {
        "word_count": 0,
        "sentence_count": 0,
        "paragraph_count": 0,
        "syllable_count": 0,
        "avg_sentence_length": 0,
        "avg_paragraph_length": 0,
        "avg_syllables_per_word": 0,
        "flesch_reading_ease": 0,
        "flesch_kincaid_grade": 0,
        "reading_level": "",
        "estimated_reading_time_min": 0,
        "complex_words": 0,
        "complex_word_pct": 0,
        "issues": [],
        "recommendations": [],
        "sentence_rewrites": [],
    }

    if not text or not text.strip():
        result["issues"].append("🔴 No readable text content found")
        return result

    # Split into paragraphs
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    result["paragraph_count"] = len(paragraphs)

    # Split into sentences
    raw_sentences = split_sentences(text)
    sentences = [
        s.strip() for s in raw_sentences
        if s.strip() and len(re.findall(r"\b[a-zA-Z]+\b", s)) >= 4
    ]
    result["sentence_count"] = max(1, len(sentences))

    # Count words
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    result["word_count"] = len(words)

    if not words:
        result["issues"].append("🔴 No words found in content")
        return result

    # Count syllables
    syllables = sum(count_syllables(w) for w in words)
    result["syllable_count"] = syllables

    # Complex words (3+ syllables)
    complex_words = [w for w in words if count_syllables(w) >= 3]
    result["complex_words"] = len(complex_words)
    result["complex_word_pct"] = round(len(complex_words) / len(words) * 100, 1)

    # Averages
    result["avg_sentence_length"] = round(len(words) / result["sentence_count"], 1)
    result["avg_paragraph_length"] = round(result["sentence_count"] / max(1, result["paragraph_count"]), 1)
    result["avg_syllables_per_word"] = round(syllables / len(words), 2)

    # Flesch Reading Ease: 206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)
    wps = len(words) / result["sentence_count"]
    spw = syllables / len(words)
    fre = 206.835 - (1.015 * wps) - (84.6 * spw)
    result["flesch_reading_ease"] = round(max(0, min(100, fre)), 1)

    # Flesch-Kincaid Grade Level: 0.39*(words/sentences) + 11.8*(syllables/words) - 15.59
    fkgl = (0.39 * wps) + (11.8 * spw) - 15.59
    result["flesch_kincaid_grade"] = round(max(0, fkgl), 1)

    # Reading level label
    fre_val = result["flesch_reading_ease"]
    if fre_val >= 80:
        result["reading_level"] = "Easy (6th grade)"
    elif fre_val >= 60:
        result["reading_level"] = "Standard (7th-8th grade)"
    elif fre_val >= 40:
        result["reading_level"] = "Difficult (9th-12th grade)"
    elif fre_val >= 20:
        result["reading_level"] = "Very Difficult (college)"
    else:
        result["reading_level"] = "Extremely Difficult (post-graduate)"

    # Reading time (avg 200 WPM)
    result["estimated_reading_time_min"] = round(len(words) / 200, 1)

    # Issues & recommendations
    if result["avg_sentence_length"] > 25:
        result["issues"].append(
            f"⚠️ Average sentence length ({result['avg_sentence_length']} words) is too long — target 15-20"
        )
        result["recommendations"].append("Break long sentences into shorter ones for better readability")

    if fre_val < 40:
        result["issues"].append(
            f"⚠️ Content is difficult to read (Flesch: {fre_val}) — may reduce engagement"
        )
        result["recommendations"].append("Simplify vocabulary and shorten sentences")
    elif fre_val < 60:
        result["issues"].append(
            f"ℹ️ Content readability is moderate (Flesch: {fre_val}) — suitable for educated audience"
        )

    if result["complex_word_pct"] > 20:
        result["issues"].append(
            f"⚠️ {result['complex_word_pct']}% complex words (3+ syllables) — consider simplifying"
        )

    if result["paragraph_count"] > 0 and result["avg_paragraph_length"] > 5:
        result["issues"].append(
            f"⚠️ Average paragraph length ({result['avg_paragraph_length']} sentences) — aim for 2-4"
        )
        result["recommendations"].append("Break long paragraphs into smaller ones")

    if result["word_count"] < 300:
        result["issues"].append(f"⚠️ Thin content ({result['word_count']} words) — may rank poorly")

    # Build concrete rewrite candidates for long sentences
    long_sentences = []
    for s in sentences:
        wc = len(re.findall(r"\b[a-zA-Z]+\b", s))
        if wc > 25:
            long_sentences.append((wc, s))

    long_sentences.sort(key=lambda x: x[0], reverse=True)
    for wc, s in long_sentences[:5]:
        if is_navigation_noise(s):
            continue
        result["sentence_rewrites"].append({
            "current": s[:600],
            "suggested": suggest_sentence_rewrite(s)[:600],
            "current_word_count": wc,
            "target_word_count": "15-20",
        })
        if len(result["sentence_rewrites"]) >= 3:
            break

    # If the page appears to be homepage/navigation-heavy and we cannot extract
    # clean prose sentences, provide actionable homepage replacement targets.
    if not result["sentence_rewrites"] and (result["avg_sentence_length"] > 25 or fre_val < 40):
        result["sentence_rewrites"].extend([
            {
                "current": "Homepage hero intro block is broad and hard to scan.",
                "suggested": (
                    "Use a 2-3 sentence hero: who you help, what users can do here, and "
                    "where to start. Example: \"Learn practical ethical hacking with "
                    "step-by-step guides. Start with Wi-Fi security, Active Directory, or "
                    "malware analysis using the tracks below.\""
                ),
                "current_word_count": "template",
                "target_word_count": "40-60 total (split into 2-3 sentences)",
            },
            {
                "current": "Section descriptions mix too many topics in one long paragraph.",
                "suggested": (
                    "Replace with short blurbs per section (1 sentence each) and add a clear "
                    "CTA link: \"Start Wi-Fi Security\", \"Explore AD Attack Paths\", "
                    "\"View Red-Team Cheat Sheets\"."
                ),
                "current_word_count": "template",
                "target_word_count": "12-20 words per blurb",
            },
        ])

    if result["sentence_rewrites"]:
        result["recommendations"].append(
            "Rewrite the flagged long sentences below using the suggested replacements."
        )

    return result


def main():
    parser = argparse.ArgumentParser(description="Analyze content readability")
    parser.add_argument("file", nargs="?", help="HTML or text file to analyze")
    parser.add_argument("--url", "-u", help="Analyze content fetched from URL")
    parser.add_argument("--text", "-t", help="Analyze text directly")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.text:
        text = args.text
    elif args.url:
        try:
            req = urllib.request.Request(
                args.url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SEOBot/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
            if "<html" in content.lower() or "<body" in content.lower():
                text = extract_text(content)
            else:
                text = content
        except Exception as exc:
            parser.error(f"Failed to fetch URL: {exc}")
            return
    elif args.file:
        with open(args.file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if "<html" in content.lower() or "<body" in content.lower():
            text = extract_text(content)
        else:
            text = content
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
        if "<html" in content.lower() or "<body" in content.lower():
            text = extract_text(content)
        else:
            text = content
    else:
        parser.error("Provide a file, --text, or pipe content via stdin")
        return

    result = analyze_readability(text)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print("Readability Analysis")
    print("=" * 50)
    print(f"Words: {result['word_count']} | Sentences: {result['sentence_count']} | "
          f"Paragraphs: {result['paragraph_count']}")
    print(f"Reading Time: ~{result['estimated_reading_time_min']} min")
    print()
    print(f"Flesch Reading Ease: {result['flesch_reading_ease']}/100 — {result['reading_level']}")
    print(f"Flesch-Kincaid Grade: {result['flesch_kincaid_grade']}")
    print(f"Avg Sentence Length: {result['avg_sentence_length']} words (target: 15-20)")
    print(f"Avg Paragraph Length: {result['avg_paragraph_length']} sentences (target: 2-4)")
    print(f"Complex Words (3+ syllables): {result['complex_words']} ({result['complex_word_pct']}%)")

    if result["issues"]:
        print(f"\nIssues:")
        for issue in result["issues"]:
            print(f"  {issue}")

    if result["recommendations"]:
        print(f"\nRecommendations:")
        for rec in result["recommendations"]:
            print(f"  💡 {rec}")

    if result["sentence_rewrites"]:
        print("\nSuggested sentence rewrites:")
        for i, item in enumerate(result["sentence_rewrites"], 1):
            print(f"  {i}. Current ({item['current_word_count']} words): {item['current']}")
            print(f"     Suggested: {item['suggested']}")


if __name__ == "__main__":
    main()

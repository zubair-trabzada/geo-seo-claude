#!/usr/bin/env python3
"""
GitHub README SEO Lint

Scores README quality for GitHub discoverability and conversion readiness.

Usage:
  python github_readme_lint.py README.md --json
"""

import argparse
import base64
import json
import os
import re
import sys
from datetime import datetime, timezone

from github_api import GitHubAPIError, fetch_json, get_token, resolve_repo


DEFAULT_INTENTS = [
    "seo",
    "audit",
    "technical seo",
    "schema",
    "core web vitals",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def looks_like_placeholder(text: str) -> bool:
    value = (text or "").strip().lower()
    if value in {"404", "404: not found", "not found"}:
        return True
    if value.startswith("404:"):
        return True
    if value.startswith("<html") and "not found" in value:
        return True
    return False


def fetch_readme_from_repo(repo: str, token: str, provider: str) -> str:
    response = fetch_json(f"/repos/{repo}/readme", token=token, provider=provider, timeout=30)
    payload = response.get("data", {})
    content = payload.get("content") or ""
    if not content:
        return ""
    raw = base64.b64decode(content.encode("utf-8"), validate=False)
    return raw.decode("utf-8", errors="replace")


def strip_code_fences(text: str) -> str:
    text = re.sub(r"(?ms)^```[\s\S]*?^```[ \t]*$", "", text)
    text = re.sub(r"(?ms)^~~~[\s\S]*?^~~~[ \t]*$", "", text)
    return text


def extract_headings(markdown: str) -> list:
    headings = []
    lines = markdown.splitlines()
    for i, line in enumerate(lines, start=1):
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.strip())
        if m:
            headings.append({"line": i, "level": len(m.group(1)), "text": m.group(2).strip()})
            continue

        # Setext headings:
        # Title
        # =====
        if i < len(lines):
            next_line = lines[i].strip()
            if line.strip() and re.match(r"^(=+|-+)\s*$", next_line):
                level = 1 if next_line.startswith("=") else 2
                headings.append({"line": i, "level": level, "text": line.strip()})
    return headings


def count_code_blocks(markdown: str) -> int:
    fenced_backticks = len(re.findall(r"(?ms)^```[\s\S]*?^```[ \t]*$", markdown))
    fenced_tildes = len(re.findall(r"(?ms)^~~~[\s\S]*?^~~~[ \t]*$", markdown))
    fenced_total = fenced_backticks + fenced_tildes

    # Count indented code blocks (>=2 consecutive indented non-empty lines)
    indented_total = 0
    run = 0
    for line in markdown.splitlines():
        if re.match(r"^(    |\t)\S", line):
            run += 1
        else:
            if run >= 2:
                indented_total += 1
            run = 0
    if run >= 2:
        indented_total += 1

    return fenced_total + indented_total


def extract_images(markdown: str) -> list:
    images = []
    for m in re.finditer(r"!\[(.*?)\]\((.*?)\)", markdown):
        images.append({"alt": (m.group(1) or "").strip(), "url": (m.group(2) or "").strip()})
    return images


def plain_word_count(markdown: str) -> int:
    text = strip_code_fences(markdown)
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[#>*`_~\-]", " ", text)
    words = re.findall(r"\b[\w']+\b", text.lower())
    return len(words)


def add_finding(findings: list, category: str, severity: str, finding: str, evidence: str, fix: str):
    findings.append(
        {
            "category": category,
            "severity": severity,
            "confidence": "Confirmed",
            "finding": finding,
            "evidence": evidence,
            "fix": fix,
        }
    )


def normalize_heading_text(headings: list) -> list:
    return [h["text"].strip().lower() for h in headings]


def detect_heading_jumps(headings: list) -> list:
    jumps = []
    prev = None
    for h in headings:
        if prev is not None and h["level"] > prev + 1:
            jumps.append({"line": h["line"], "from": prev, "to": h["level"], "text": h["text"]})
        prev = h["level"]
    return jumps


def score_report(markdown: str, intents: list) -> dict:
    headings = extract_headings(markdown)
    heading_text = normalize_heading_text(headings)
    images = extract_images(markdown)
    words = plain_word_count(markdown)
    findings = []

    # Opening clarity (20)
    opening_score = 20
    opening_chunk = strip_code_fences(markdown).strip().splitlines()[:20]
    opening_text = " ".join(opening_chunk).lower()
    matched_intents = [term for term in intents if term.lower() in opening_text]
    if not matched_intents:
        opening_score -= 12
        add_finding(
            findings,
            "Opening Clarity",
            "Warning",
            "Opening section lacks target intent terms.",
            "None of the configured intent terms appear in the opening section.",
            "Include primary use-case language in first 2-3 paragraphs.",
        )
    if words < 250:
        opening_score -= 4
        add_finding(
            findings,
            "Opening Clarity",
            "Info",
            "README is short for a discoverability-oriented project page.",
            f"Word count is {words}.",
            "Expand with concise sections for install, proof, and contribution paths.",
        )
    opening_score = max(0, opening_score)

    # Information architecture (20)
    ia_score = 20
    h1_count = sum(1 for h in headings if h["level"] == 1)
    heading_jumps = detect_heading_jumps(headings)
    if h1_count != 1:
        ia_score -= 12
        severity = "Critical" if h1_count == 0 else "Warning"
        add_finding(
            findings,
            "Information Architecture",
            severity,
            "README should contain exactly one H1 heading.",
            f"Detected H1 count: {h1_count}.",
            "Keep a single H1 title and move other top-level sections to H2.",
        )
    if heading_jumps:
        ia_score -= 5
        add_finding(
            findings,
            "Information Architecture",
            "Warning",
            "Heading hierarchy has level jumps.",
            f"Detected {len(heading_jumps)} jump(s) where heading level skips intermediary levels.",
            "Normalize heading flow (H1 -> H2 -> H3) without skipping levels.",
        )
    ia_score = max(0, ia_score)

    # Install + quickstart (20)
    install_score = 20
    install_markers = ("install", "quick start", "quickstart", "getting started", "setup")
    has_install_section = any(any(marker in t for marker in install_markers) for t in heading_text)
    if not has_install_section:
        install_score -= 14
        add_finding(
            findings,
            "Install + Quickstart",
            "Critical",
            "Installation/quickstart section is missing.",
            "No install or getting-started heading detected.",
            "Add a dedicated install section with copy-paste commands and prerequisites.",
        )
    code_block_count = count_code_blocks(markdown)
    if code_block_count == 0:
        install_score -= 4
        add_finding(
            findings,
            "Install + Quickstart",
            "Warning",
            "No code examples detected.",
            "README contains zero detectable code blocks (fenced or indented).",
            "Add runnable command examples for setup and core usage.",
        )
    install_score = max(0, install_score)

    # Proof + credibility (15)
    proof_score = 15
    proof_markers = ("example", "output", "report", "screenshot", "demo", "result")
    has_examples_section = any(any(marker in t for marker in proof_markers) for t in heading_text)
    if not has_examples_section:
        proof_score -= 8
        add_finding(
            findings,
            "Proof + Credibility",
            "Warning",
            "README lacks explicit proof/results section.",
            "No heading found for examples, reports, screenshots, or outputs.",
            "Add evidence sections with sample outputs or screenshots.",
        )
    if "license" not in " ".join(heading_text) and "license" not in markdown.lower():
        proof_score -= 4
        add_finding(
            findings,
            "Proof + Credibility",
            "Warning",
            "License reference is missing or unclear in README.",
            "No explicit license mention detected.",
            "Add a short license section linking to LICENSE file.",
        )
    proof_score = max(0, proof_score)

    # CTA + community (15)
    cta_score = 15
    cta_markers = ("contribut", "issue", "pull request", "support", "discussion", "star")
    cta_hits = sum(1 for marker in cta_markers if marker in markdown.lower())
    has_contributing_section = "contribut" in markdown.lower()
    if cta_hits < 2:
        cta_score -= 9
        add_finding(
            findings,
            "CTA + Community",
            "Warning",
            "README has weak contribution/support call-to-action coverage.",
            f"Detected {cta_hits} CTA marker(s) from contribution/support keyword set.",
            "Add clear paths for contributing, opening issues, and support requests.",
        )
    cta_score = max(0, cta_score)

    # Readability + accessibility (10)
    read_score = 10
    missing_alt = [img for img in images if not img["alt"]]
    if missing_alt:
        read_score -= 6
        add_finding(
            findings,
            "Readability + Accessibility",
            "Warning",
            "Some README images are missing alt text.",
            f"{len(missing_alt)} image(s) detected with empty alt text.",
            "Add descriptive alt text for each non-decorative image.",
        )
    if len(headings) < 4:
        read_score -= 2
        add_finding(
            findings,
            "Readability + Accessibility",
            "Info",
            "README sectioning is shallow.",
            f"Detected only {len(headings)} heading(s).",
            "Use additional headings to improve scannability and structure.",
        )
    read_score = max(0, read_score)

    category_scores = {
        "opening_clarity": opening_score,
        "information_architecture": ia_score,
        "install_quickstart": install_score,
        "proof_credibility": proof_score,
        "cta_community": cta_score,
        "readability_accessibility": read_score,
    }
    total_score = sum(category_scores.values())

    if total_score >= 90:
        rating = "Excellent"
    elif total_score >= 70:
        rating = "Good"
    elif total_score >= 50:
        rating = "Needs Improvement"
    elif total_score >= 30:
        rating = "Poor"
    else:
        rating = "Critical"

    if not findings:
        add_finding(
            findings,
            "Overall",
            "Pass",
            "README meets baseline GitHub SEO and conversion quality checks.",
            "No major structural, install, or accessibility deficiencies detected.",
            "Maintain quality with periodic linting and updates.",
        )

    return {
        "summary": {"score": total_score, "rating": rating},
        "metrics": {
            "word_count": words,
            "heading_count": len(headings),
            "h1_count": h1_count,
            "code_block_count": code_block_count,
            "image_count": len(images),
            "images_missing_alt": len(missing_alt),
            "matched_intents_in_opening": matched_intents,
            "has_install_section": has_install_section,
            "has_examples_section": has_examples_section,
            "has_contributing_section": has_contributing_section,
        },
        "category_scores": category_scores,
        "findings": findings,
    }


def print_text(report: dict):
    summary = report.get("summary", {})
    print("\nREADME SEO Lint")
    print("=" * 60)
    print(f"Score: {summary.get('score', 'NA')}/100 ({summary.get('rating', 'Unknown')})")
    metrics = report.get("metrics", {})
    print(
        f"Words: {metrics.get('word_count', 0)} | Headings: {metrics.get('heading_count', 0)} | "
        f"Images missing alt: {metrics.get('images_missing_alt', 0)}"
    )
    print("\nTop findings:")
    for f in report.get("findings", [])[:10]:
        print(f"- [{f['severity']}] {f['finding']}")


def main():
    parser = argparse.ArgumentParser(description="README SEO and conversion linting for GitHub repositories.")
    parser.add_argument("readme_path", nargs="?", default="README.md", help="Path to README file (default: README.md)")
    parser.add_argument("--repo", help="Repository slug or URL (owner/repo) for remote README fallback.")
    parser.add_argument("--provider", choices=["auto", "api", "gh"], default="auto", help="GitHub data provider mode for README fallback.")
    parser.add_argument("--token", help="GitHub token override. Prefer env vars GITHUB_TOKEN or GH_TOKEN.")
    parser.add_argument("--intent", action="append", help="Target intent phrase (repeatable).")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    parser.add_argument("--output", help="Write JSON report to file path.")
    args = parser.parse_args()

    intents = args.intent if args.intent else DEFAULT_INTENTS
    limitations = []
    content_source = "local_file"
    markdown = ""

    if os.path.exists(args.readme_path):
        markdown = read_text(args.readme_path)
    else:
        limitations.append(f"Local README file not found: {args.readme_path}")

    needs_remote = (not markdown.strip()) or looks_like_placeholder(markdown)
    if needs_remote and args.repo:
        try:
            token = get_token(args.token)
            repo = resolve_repo(args.repo)
            remote_md = fetch_readme_from_repo(repo=repo, token=token, provider=args.provider)
            if remote_md.strip():
                markdown = remote_md
                content_source = "github_api"
                limitations.append("Used remote README fallback due missing/placeholder local README.")
        except GitHubAPIError as exc:
            limitations.append(f"Remote README fallback failed: {exc}")

    if looks_like_placeholder(markdown):
        print(
            "Error: README content appears to be placeholder/404. Provide valid README path or repo access for remote fallback.",
            file=sys.stderr,
        )
        sys.exit(2)

    if not markdown.strip():
        print("Error: README content unavailable from local file and remote fallback.", file=sys.stderr)
        sys.exit(2)

    scored = score_report(markdown=markdown, intents=intents)
    report = {
        "timestamp_utc": utc_now_iso(),
        "readme_path": args.readme_path,
        "content_source": content_source,
        "limitations": limitations,
        "intents": intents,
        **scored,
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text(report)


if __name__ == "__main__":
    main()

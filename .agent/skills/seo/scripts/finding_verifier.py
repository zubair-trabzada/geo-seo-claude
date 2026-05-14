#!/usr/bin/env python3
"""
Reusable finding verifier.

Purpose:
- remove duplicate findings across sources
- suppress clearly contradicted findings based on provided evidence context
- return clean, prioritized findings for final reporting
"""

import argparse
import json
import re
import sys


SEVERITY_RANK = {"Critical": 0, "Warning": 1, "Info": 2, "Pass": 3}


def _sev_rank(severity: str) -> int:
    return SEVERITY_RANK.get(severity or "Info", 9)


def _normalize_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def canonical_key(finding: dict) -> str:
    text = _normalize_text(finding.get("finding", ""))

    m = re.search(r"missing required (?:repository )?(?:file|artifact):\s*([^\.\n]+)", text)
    if m:
        return f"missing-required:{m.group(1).strip()}"

    m = re.search(r"missing recommended (?:trust|community) artifact:\s*([^\.\n]+)", text)
    if m:
        return f"missing-recommended:{m.group(1).strip()}"

    m = re.search(r"missing community profile component:\s*([^\.\n]+)", text)
    if m:
        return f"community-profile-missing:{m.group(1).strip()}"

    m = re.search(r"remote community profile marks [`']?([^`'\.\n]+)[`']? as missing", text)
    if m:
        return f"community-profile-missing:{m.group(1).strip()}"

    # Generic fallback
    base = re.sub(r"[^a-z0-9\s:_\-]", "", text)
    return base[:160]


def should_suppress(finding: dict, context: dict) -> tuple:
    text = _normalize_text(finding.get("finding", ""))
    metrics = (context or {}).get("readme_metrics", {}) or {}

    if "no code examples detected" in text:
        if int(metrics.get("code_block_count", 0)) > 0:
            return True, "Suppressed: README metrics show code blocks present."

    if "readme should contain exactly one h1 heading" in text:
        if int(metrics.get("h1_count", 0)) == 1:
            return True, "Suppressed: README metrics show exactly one H1."

    if "installation/quickstart section is missing" in text:
        if bool(metrics.get("has_install_section")):
            return True, "Suppressed: README metrics indicate install section exists."

    if "readme sectioning is shallow" in text:
        if int(metrics.get("heading_count", 0)) >= 4:
            return True, "Suppressed: README has sufficient heading depth."

    return False, ""


def verify_findings(findings: list, context: dict = None) -> dict:
    """
    Verify and dedupe findings.

    Returns:
    {
      "findings": [...],
      "dropped": [{"finding":..., "reason": ...}],
      "raw_count": N,
      "verified_count": M
    }
    """
    context = context or {}
    dropped = []
    grouped = {}

    for item in findings or []:
        suppress, reason = should_suppress(item, context=context)
        if suppress:
            dropped.append({"finding": item.get("finding", ""), "reason": reason})
            continue

        key = canonical_key(item)
        existing = grouped.get(key)
        if not existing:
            entry = dict(item)
            entry["sources"] = [item.get("source")] if item.get("source") else []
            grouped[key] = entry
            continue

        # Merge duplicates and keep stronger severity.
        if _sev_rank(item.get("severity")) < _sev_rank(existing.get("severity")):
            for field in ("severity", "finding", "evidence", "fix", "confidence"):
                existing[field] = item.get(field, existing.get(field))
        src = item.get("source")
        if src and src not in existing.get("sources", []):
            existing.setdefault("sources", []).append(src)

    deduped = list(grouped.values())
    deduped.sort(key=lambda x: _sev_rank(x.get("severity")))

    return {
        "findings": deduped,
        "dropped": dropped,
        "raw_count": len(findings or []),
        "verified_count": len(deduped),
    }


def main():
    parser = argparse.ArgumentParser(description="Verify/dedupe findings from JSON input.")
    parser.add_argument("--findings-json", help="Path to JSON array of findings.")
    parser.add_argument("--context-json", help="Path to JSON context object.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    args = parser.parse_args()

    if not args.findings_json:
        print("Error: --findings-json is required", file=sys.stderr)
        sys.exit(2)

    with open(args.findings_json, "r", encoding="utf-8") as f:
        findings = json.load(f)
    context = {}
    if args.context_json:
        with open(args.context_json, "r", encoding="utf-8") as f:
            context = json.load(f)

    result = verify_findings(findings=findings, context=context)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Raw findings: {result['raw_count']}")
        print(f"Verified findings: {result['verified_count']}")
        print(f"Dropped: {len(result['dropped'])}")


if __name__ == "__main__":
    main()

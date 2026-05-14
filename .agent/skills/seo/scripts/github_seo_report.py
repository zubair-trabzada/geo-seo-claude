#!/usr/bin/env python3
"""
GitHub SEO Report Generator

Runs GitHub SEO scripts and combines their outputs into a single markdown report.

Usage:
  python github_seo_report.py --repo owner/repo --markdown GITHUB-SEO-REPORT.md
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

from finding_verifier import verify_findings
from github_api import get_token, resolve_repo


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
QUERY_STOP_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_json_script(script_name: str, extra_args: list) -> dict:
    script_path = os.path.join(SCRIPT_DIR, script_name)
    cmd = [sys.executable, script_path] + extra_args + ["--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {
            "ok": False,
            "error": (result.stderr or result.stdout or f"Exit {result.returncode}").strip(),
            "returncode": result.returncode,
        }
    try:
        payload = json.loads((result.stdout or "").strip() or "{}")
        return {"ok": True, "data": payload}
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"Invalid JSON from {script_name}: {exc}", "returncode": 1}


def _normalize_query_phrase(text: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    filtered = [t for t in tokens if len(t) > 1 and t not in QUERY_STOP_WORDS]
    if not filtered:
        filtered = [t for t in tokens if len(t) > 1]
    return " ".join(filtered[:6]).strip()


def _dedupe_queries(values: list) -> list:
    out = []
    seen = set()
    for item in values:
        cleaned = " ".join((item or "").split()).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
    return out


def load_explicit_queries(args) -> tuple[list, list]:
    queries = []
    warnings = []
    if args.query:
        queries.extend([q.strip() for q in args.query if q and q.strip()])
    if args.query_file:
        if not os.path.exists(args.query_file):
            warnings.append(f"Query file not found: {args.query_file}")
        else:
            try:
                with open(args.query_file, "r", encoding="utf-8") as f:
                    for line in f:
                        text = line.strip()
                        if text and not text.startswith("#"):
                            queries.append(text)
            except Exception as exc:
                warnings.append(f"Could not read query file `{args.query_file}`: {exc}")
    return _dedupe_queries(queries), warnings


def derive_auto_queries(repo: str, repo_audit_data: dict, max_queries: int = 6) -> list:
    metadata = (repo_audit_data or {}).get("metadata", {}) or {}
    title_analysis = (repo_audit_data or {}).get("title_analysis", {}) or {}
    owner, _, repo_name = repo.partition("/")

    candidates = []
    for seed in (
        repo_name,
        metadata.get("name"),
        title_analysis.get("recommended_repo_slug"),
        title_analysis.get("recommended_display_title"),
    ):
        phrase = _normalize_query_phrase(seed or "")
        if phrase:
            candidates.append(phrase)

    topics = metadata.get("topics") or []
    for topic in topics[:10]:
        phrase = _normalize_query_phrase(topic)
        if phrase:
            candidates.append(phrase)

    keywords = []
    for raw in (title_analysis.get("search_intent_keywords") or [])[:14]:
        token = _normalize_query_phrase(raw)
        if token:
            keywords.append(token.split()[0])
    keywords = _dedupe_queries(keywords)

    if len(keywords) >= 2:
        candidates.append(" ".join(keywords[:2]))
    if len(keywords) >= 3:
        candidates.append(" ".join(keywords[:3]))
    for i in range(0, max(0, len(keywords) - 1)):
        candidates.append(" ".join(keywords[i:i + 2]))

    core_tokens = _normalize_query_phrase(repo_name).split()
    for kw in keywords[:6]:
        if kw in core_tokens:
            continue
        blend = _dedupe_queries(core_tokens[:2] + [kw])
        if len(blend) >= 2:
            candidates.append(" ".join(blend))

    owner_phrase = _normalize_query_phrase(owner)
    if owner_phrase and core_tokens:
        candidates.append(f"{owner_phrase} {' '.join(core_tokens[:2])}".strip())

    final = _dedupe_queries(candidates)
    if not final:
        slug_fallback = _normalize_query_phrase(repo_name)
        if slug_fallback:
            final = [slug_fallback]
    return final[: max(1, max_queries)]


def collect_inputs(args, repo: str, token: str, queries: list) -> dict:
    common = ["--repo", repo, "--provider", args.provider]
    if token:
        common += ["--token", token]

    traffic_args = common + ["--archive-dir", args.archive_dir]
    if args.no_archive_write:
        traffic_args += ["--no-write"]

    readme_args = [args.readme_path, "--repo", repo, "--provider", args.provider]
    if token:
        readme_args += ["--token", token]

    tasks = {
        "repo_audit": ["github_repo_audit.py", common],
        "readme_lint": ["github_readme_lint.py", readme_args],
        "community_health": ["github_community_health.py", common],
        "traffic_archiver": ["github_traffic_archiver.py", traffic_args],
    }

    benchmark_args = common[:]
    query_supplied = False
    for query in queries:
        benchmark_args += ["--query", query]
        query_supplied = True
    benchmark_args += ["--max-pages", str(args.max_pages), "--per-page", str(args.per_page)]

    competitor_args = benchmark_args[:] + ["--top-n", str(args.competitor_top_n)]
    competitor_supplied = False
    if args.competitor:
        for comp in args.competitor:
            competitor_args += ["--competitor", comp]
            competitor_supplied = True

    if query_supplied:
        tasks["search_benchmark"] = ["github_search_benchmark.py", benchmark_args]

    if query_supplied or competitor_supplied:
        tasks["competitor_research"] = ["github_competitor_research.py", competitor_args]

    return tasks


def apply_result(result_key: str, result: dict, limitations: list):
    if not result.get("ok"):
        limitations.append(f"{result_key} failed: {result.get('error', 'unknown')}")
        return
    for item in result["data"].get("limitations", []):
        limitations.append(f"{result_key}: {item}")
    if result_key == "traffic_archiver":
        snapshot = result["data"].get("snapshot", {})
        for item in snapshot.get("limitations", []):
            limitations.append(f"{result_key}: {item}")


def extract_score(outputs: dict) -> dict:
    score_map = {}
    if outputs.get("repo_audit", {}).get("ok"):
        score_map["repo_audit"] = outputs["repo_audit"]["data"].get("summary", {}).get("score")
    if outputs.get("readme_lint", {}).get("ok"):
        score_map["readme_lint"] = outputs["readme_lint"]["data"].get("summary", {}).get("score")
    if outputs.get("community_health", {}).get("ok"):
        score_map["community_health"] = outputs["community_health"]["data"].get("score")
    valid = [v for v in score_map.values() if isinstance(v, (int, float))]
    overall = round(sum(valid) / len(valid), 2) if valid else None
    return {"components": score_map, "overall": overall}


def collect_findings(outputs: dict) -> list:
    findings = []
    for key in ("repo_audit", "readme_lint", "community_health"):
        item = outputs.get(key, {})
        if not item.get("ok"):
            continue
        for finding in item["data"].get("findings", []):
            findings.append(
                {
                    "source": key,
                    "severity": finding.get("severity", "Info"),
                    "finding": finding.get("finding", ""),
                    "evidence": finding.get("evidence", ""),
                    "fix": finding.get("fix", ""),
                    "confidence": finding.get("confidence", "Likely"),
                }
            )
    competitor = outputs.get("competitor_research", {})
    if competitor.get("ok"):
        for opp in competitor.get("data", {}).get("gaps", {}).get("opportunities", []):
            findings.append(
                {
                    "source": "competitor_research",
                    "severity": opp.get("severity", "Info"),
                    "finding": opp.get("finding", ""),
                    "evidence": opp.get("evidence", ""),
                    "fix": opp.get("fix", ""),
                    "confidence": "Likely",
                }
            )
    severity_order = {"Critical": 0, "Warning": 1, "Pass": 2, "Info": 3}
    findings.sort(key=lambda x: severity_order.get(x["severity"], 9))
    return findings


def build_backlink_plan(outputs: dict) -> dict:
    """Create a practical backlink and promotion plan for the repository."""
    repo_audit = outputs.get("repo_audit", {})
    metadata = {}
    title_analysis = {}
    if repo_audit.get("ok"):
        metadata = repo_audit.get("data", {}).get("metadata", {}) or {}
        title_analysis = repo_audit.get("data", {}).get("title_analysis", {}) or {}

    keywords = title_analysis.get("search_intent_keywords", [])[:6]
    base_title = title_analysis.get("recommended_display_title") or metadata.get("name") or "Repository"
    repo_url = metadata.get("html_url")
    if not repo_url:
        repo_slug = metadata.get("full_name")
        if repo_slug:
            repo_url = f"https://github.com/{repo_slug}"

    title_ideas = [
        f"How I Built {base_title} for SEO Automation",
        f"GitHub SEO Playbook: Improving Discoverability for {base_title}",
        f"{base_title}: From Idea to Open-Source SEO Workflow",
    ]
    if keywords:
        kw_phrase = ", ".join(keywords[:3])
        title_ideas.append(f"Open-Source Guide: {kw_phrase} with {base_title}")

    channels = [
        {
            "channel": "Medium",
            "type": "Technical case study",
            "cadence": "1 post per major release",
            "cta": "Link to repo + install quickstart + release notes",
        },
        {
            "channel": "Dev.to",
            "type": "Tutorial / launch post",
            "cadence": "1 launch post + update posts quarterly",
            "cta": "Link to GitHub repo and usage examples",
        },
        {
            "channel": "Hashnode",
            "type": "Deep-dive engineering write-up",
            "cadence": "Bi-monthly",
            "cta": "Link to architecture docs and scripts",
        },
        {
            "channel": "Personal/Company Blog",
            "type": "Canonical long-form article",
            "cadence": "Monthly",
            "cta": "Link to repo, docs, and comparison pages",
        },
        {
            "channel": "LinkedIn Article",
            "type": "Problem/solution summary for practitioners",
            "cadence": "Per release",
            "cta": "Link to repo and demo outputs",
        },
        {
            "channel": "Reddit (relevant subreddits)",
            "type": "Show-and-tell with value-first context",
            "cadence": "Selective (major feature drops)",
            "cta": "Share repo only after explaining workflow and results",
        },
    ]

    anchor_guidance = {
        "exact_match_max_percent": 10,
        "recommended_mix": [
            "Brand anchors (repo/owner name)",
            "Partial-match anchors (e.g., 'agentic SEO skill')",
            "Generic anchors ('GitHub repo', 'source code')",
            "Naked URL anchors",
        ],
    }

    return {
        "repo_url": repo_url,
        "title_ideas": title_ideas[:4],
        "channels": channels,
        "anchor_text_guidance": anchor_guidance,
    }


def dedupe_preserve(items: list) -> list:
    out = []
    seen = set()
    for item in items:
        key = item.strip()
        if key and key not in seen:
            out.append(item)
            seen.add(key)
    return out


def build_markdown(report: dict) -> str:
    lines = []
    lines.append("# GitHub SEO Report")
    lines.append("")
    lines.append(f"- Repository: `{report['repo']}`")
    lines.append(f"- Generated (UTC): `{report['timestamp_utc']}`")
    lines.append(f"- Provider mode: `{report['provider']}`")
    lines.append(f"- Overall score: `{report['scores']['overall']}`")
    verification = report.get("verification", {})
    if verification:
        lines.append(
            f"- Verified findings: `{verification.get('verified_count', 0)}` "
            f"(raw: `{verification.get('raw_count', 0)}`, dropped: `{verification.get('dropped_count', 0)}`)"
        )
    lines.append("")

    lines.append("## Score Components")
    lines.append("")
    lines.append("| Component | Score |")
    lines.append("|-----------|-------|")
    for key, value in report["scores"]["components"].items():
        lines.append(f"| {key} | {value} |")
    lines.append("")

    lines.append("## Script Status")
    lines.append("")
    lines.append("| Script | Status |")
    lines.append("|--------|--------|")
    for key, payload in report["outputs"].items():
        status = "ok" if payload.get("ok") else f"failed: {payload.get('error', 'unknown')}"
        lines.append(f"| {key} | {status} |")
    lines.append("")

    query_inputs = report.get("query_inputs", {}) or {}
    if query_inputs:
        lines.append("## Query Discovery")
        lines.append("")
        lines.append(f"- Mode: `{query_inputs.get('mode', 'unknown')}`")
        source = query_inputs.get("source")
        if source:
            lines.append(f"- Source: `{source}`")
        queries = query_inputs.get("queries", []) or []
        if queries:
            lines.append(f"- Queries: `{'; '.join(queries)}`")
        else:
            lines.append("- Queries: `none`")
        lines.append("")

    if report["limitations"]:
        lines.append("## Limitations")
        lines.append("")
        for item in report["limitations"]:
            lines.append(f"- {item}")
        lines.append("")

    if verification and verification.get("dropped"):
        lines.append("## Verifier Notes")
        lines.append("")
        lines.append("Suppressed findings due to contradiction/duplication checks:")
        for item in verification.get("dropped", [])[:10]:
            lines.append(f"- {item.get('finding')} ({item.get('reason')})")
        lines.append("")

    lines.append("## Prioritized Findings")
    lines.append("")
    lines.append("| Severity | Source | Finding | Evidence | Fix |")
    lines.append("|----------|--------|---------|----------|-----|")
    for finding in report["findings"][:40]:
        source = finding.get("source")
        if finding.get("sources"):
            source = ", ".join(finding.get("sources", []))
        lines.append(
            "| {severity} | {source} | {finding} | {evidence} | {fix} |".format(
                severity=finding["severity"],
                source=source,
                finding=finding["finding"].replace("|", "/"),
                evidence=finding["evidence"].replace("|", "/"),
                fix=finding["fix"].replace("|", "/"),
            )
        )
    if not report["findings"]:
        lines.append("| Pass | system | No major findings captured. | n/a | Continue monitoring. |")
    lines.append("")

    benchmark = report["outputs"].get("search_benchmark", {})
    if benchmark.get("ok"):
        data = benchmark["data"]
        lines.append("## Query Benchmark")
        lines.append("")
        lines.append("| Query | Rank | Sampled | Total Results |")
        lines.append("|-------|------|---------|---------------|")
        for item in data.get("results", []):
            rank = item["target_rank"] if item["target_rank"] is not None else "Not found"
            lines.append(
                f"| {item['query']} | {rank} | {item.get('sampled_results')} | {item.get('total_count')} |"
            )
        lines.append("")

    competitor = report["outputs"].get("competitor_research", {})
    if competitor.get("ok"):
        comp_data = competitor["data"]
        lines.append("## Competitor Research")
        lines.append("")
        summary = comp_data.get("summary", {})
        lines.append(
            f"- Competitors analyzed: `{summary.get('competitors_analyzed', 0)}` "
            f"across `{summary.get('queries_used', 0)}` queries"
        )
        lines.append("")
        lines.append("| Competitor | Seen Queries | Best Rank | Stars | Topics |")
        lines.append("|------------|--------------|-----------|-------|--------|")
        for item in comp_data.get("competitors", [])[:10]:
            md = item.get("metadata", {})
            lines.append(
                f"| {item.get('full_name')} | {item.get('seen_in_queries')} | {item.get('best_rank')} | "
                f"{md.get('stargazers_count')} | {len(md.get('topics') or [])} |"
            )
        if not comp_data.get("competitors"):
            lines.append("| n/a | 0 | n/a | n/a | n/a |")
        lines.append("")
        gap_data = comp_data.get("gaps", {})
        lines.append("### Topic Gaps")
        lines.append("")
        topic_gaps = gap_data.get("topic_gaps", [])[:10]
        if topic_gaps:
            for gap in topic_gaps:
                lines.append(
                    f"- `{gap.get('topic')}` (covered by {gap.get('covered_by_competitors')} competitors)"
                )
        else:
            lines.append("- No high-confidence topic gaps detected from current sample.")
        lines.append("")
        lines.append("### Competitor Opportunities")
        lines.append("")
        opportunities = gap_data.get("opportunities", [])
        if opportunities:
            for opp in opportunities:
                lines.append(f"- [{opp.get('severity', 'Info')}] {opp.get('finding')}")
                lines.append(f"  Evidence: {opp.get('evidence')}")
                lines.append(f"  Fix: {opp.get('fix')}")
        else:
            lines.append("- No additional competitor-derived opportunities captured.")
        lines.append("")

    traffic = report["outputs"].get("traffic_archiver", {})
    if traffic.get("ok"):
        snap = traffic["data"].get("snapshot", {})
        totals = snap.get("totals", {})
        lines.append("## Traffic Snapshot")
        lines.append("")
        lines.append(
            f"- Views: `{totals.get('views_count')}` (unique: `{totals.get('views_uniques')}`)"
        )
        lines.append(
            f"- Clones: `{totals.get('clones_count')}` (unique: `{totals.get('clones_uniques')}`)"
        )
        archive_paths = traffic["data"].get("archive_paths", {})
        if archive_paths:
            lines.append(f"- Archive history: `{archive_paths.get('traffic_history')}`")
            lines.append(f"- Latest snapshot: `{archive_paths.get('latest_snapshot')}`")
        lines.append("")

    title_analysis = report.get("title_analysis", {})
    if title_analysis:
        lines.append("## Title Optimization")
        lines.append("")
        lines.append(f"- Current name: `{title_analysis.get('current_name')}`")
        lines.append(f"- Recommended slug: `{title_analysis.get('recommended_repo_slug')}`")
        lines.append(f"- Recommended title: `{title_analysis.get('recommended_display_title')}`")
        keywords = title_analysis.get("search_intent_keywords", [])
        if keywords:
            lines.append(f"- Intent keywords: `{', '.join(keywords)}`")
        lines.append("")

    backlink_plan = report.get("backlink_plan", {})
    if backlink_plan:
        lines.append("## Backlink Distribution Plan")
        lines.append("")
        if backlink_plan.get("repo_url"):
            lines.append(f"- Target repo URL: `{backlink_plan.get('repo_url')}`")
        lines.append("")
        lines.append("### Suggested Post Titles")
        lines.append("")
        for title in backlink_plan.get("title_ideas", []):
            lines.append(f"- {title}")
        lines.append("")
        lines.append("### Channels")
        lines.append("")
        lines.append("| Channel | Content Type | Cadence | CTA |")
        lines.append("|---------|--------------|---------|-----|")
        for item in backlink_plan.get("channels", []):
            lines.append(
                f"| {item['channel']} | {item['type']} | {item['cadence']} | {item['cta']} |"
            )
        lines.append("")
        anchor = backlink_plan.get("anchor_text_guidance", {})
        lines.append("### Anchor Guidance")
        lines.append("")
        lines.append(
            f"- Exact-match anchor cap: `{anchor.get('exact_match_max_percent', 10)}%`"
        )
        for mix in anchor.get("recommended_mix", []):
            lines.append(f"- {mix}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _priority_for_severity(severity: str) -> str:
    if severity == "Critical":
        return "P0"
    if severity == "Warning":
        return "P1"
    if severity == "Info":
        return "P2"
    return "P3"


def build_action_plan_markdown(report: dict) -> str:
    lines = []
    lines.append("# GitHub Action Plan")
    lines.append("")
    lines.append(f"- Repository: `{report.get('repo')}`")
    lines.append(f"- Generated (UTC): `{report.get('timestamp_utc')}`")
    lines.append(f"- Source report: `{report.get('markdown_path', 'GITHUB-SEO-REPORT.md')}`")
    lines.append(f"- Overall score: `{report.get('scores', {}).get('overall')}`")
    verification = report.get("verification", {}) or {}
    lines.append(f"- Verified findings: `{verification.get('verified_count', len(report.get('findings', [])))}`")
    lines.append("")

    actionable = []
    for finding in report.get("findings", []):
        sev = finding.get("severity", "Info")
        if sev in ("Pass",):
            continue
        fix = (finding.get("fix") or "").strip()
        if not fix:
            continue
        actionable.append(
            {
                "priority": _priority_for_severity(sev),
                "severity": sev,
                "source": finding.get("source") or ", ".join(finding.get("sources") or []),
                "finding": finding.get("finding", ""),
                "evidence": finding.get("evidence", ""),
                "fix": fix,
            }
        )

    severity_order = {"Critical": 0, "Warning": 1, "Info": 2, "Pass": 3}
    actionable.sort(key=lambda x: (severity_order.get(x["severity"], 9), x["finding"]))

    now_items = [x for x in actionable if x["severity"] in ("Critical", "Warning")]
    next_items = [x for x in actionable if x["severity"] == "Info"]

    lines.append("## Now (0-7 Days)")
    lines.append("")
    lines.append("| Priority | Task | Evidence | Owner |")
    lines.append("|----------|------|----------|-------|")
    if now_items:
        for item in now_items[:20]:
            task = item["fix"].replace("|", "/")
            evidence = item["evidence"].replace("|", "/")
            lines.append(f"| {item['priority']} | {task} | {evidence} | Repo maintainer |")
    else:
        lines.append("| P2 | Maintain current baseline and monitor weekly. | No critical/warning issues in current run. | Repo maintainer |")
    lines.append("")

    lines.append("## Next (1-4 Weeks)")
    lines.append("")
    lines.append("| Priority | Improvement | Source |")
    lines.append("|----------|-------------|--------|")
    if next_items:
        for item in next_items[:15]:
            improvement = item["fix"].replace("|", "/")
            source = (item["source"] or "analysis").replace("|", "/")
            lines.append(f"| {item['priority']} | {improvement} | {source} |")
    else:
        lines.append("| P3 | Continue incremental README/topic optimization and monitor competitor changes. | analysis |")
    lines.append("")

    competitor = report.get("outputs", {}).get("competitor_research", {})
    if competitor.get("ok"):
        comp_data = competitor.get("data", {}) or {}
        gaps = (comp_data.get("gaps", {}) or {}).get("topic_gaps", [])[:8]
        lines.append("## Competitor Moves")
        lines.append("")
        if gaps:
            lines.append("Top topic opportunities to validate and adopt when relevant:")
            for gap in gaps:
                lines.append(
                    f"- Evaluate topic `{gap.get('topic')}` (observed across {gap.get('covered_by_competitors')} competitors)."
                )
        else:
            lines.append("- No high-confidence topic gaps detected in this sample.")
        lines.append("")

    backlink = report.get("backlink_plan", {}) or {}
    channels = backlink.get("channels", [])[:5]
    if channels:
        lines.append("## Backlink Distribution")
        lines.append("")
        lines.append("| Channel | Cadence | Next Action |")
        lines.append("|---------|---------|-------------|")
        for ch in channels:
            action = f"Publish/update a post and link to `{backlink.get('repo_url') or report.get('repo')}`"
            lines.append(f"| {ch.get('channel')} | {ch.get('cadence')} | {action} |")
        lines.append("")

    lines.append("## Measurement Cadence")
    lines.append("")
    lines.append("1. Run `github_seo_report.py` weekly and track score/findings deltas.")
    lines.append("2. Archive traffic snapshots at least every 7 days to avoid 14-day GitHub retention loss.")
    lines.append("3. Re-run competitor benchmarking monthly or after major releases.")
    lines.append("")

    lines.append("## Completion Criteria")
    lines.append("")
    lines.append("- All `Critical` and `Warning` tasks in `Now` are resolved or explicitly deferred.")
    lines.append("- Repository metadata and README reflect target intent terms and trust signals.")
    lines.append("- Traffic history remains continuously archived.")
    lines.append("")

    return "\n".join(lines).strip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate consolidated GitHub SEO report from local script outputs.")
    parser.add_argument("--repo", help="Repository slug or URL (owner/repo). If omitted, infer from git origin.")
    parser.add_argument("--token", help="GitHub token override. Prefer env vars GITHUB_TOKEN or GH_TOKEN.")
    parser.add_argument(
        "--provider",
        choices=["auto", "api", "gh"],
        default="auto",
        help="GitHub data provider mode (default: auto).",
    )
    parser.add_argument("--readme-path", default="README.md", help="README path for linting (default: README.md)")
    parser.add_argument("--query", action="append", help="Search query for benchmark (repeatable).")
    parser.add_argument("--query-file", help="Path to query list file.")
    parser.add_argument("--competitor", action="append", help="Explicit competitor repo slug/URL (repeatable).")
    parser.add_argument("--max-pages", type=int, default=2, help="Search pages per query (default: 2).")
    parser.add_argument("--per-page", type=int, default=50, help="Search results per page (default: 50).")
    parser.add_argument("--competitor-top-n", type=int, default=6, help="Competitors to analyze in depth (default: 6).")
    parser.add_argument(
        "--auto-query-max",
        type=int,
        default=6,
        help="Maximum auto-derived benchmark queries when explicit queries are not provided (default: 6).",
    )
    parser.add_argument("--archive-dir", default=".github-seo-data", help="Traffic archive directory.")
    parser.add_argument("--no-archive-write", action="store_true", help="Do not write traffic archive files.")
    parser.add_argument("--markdown", default="GITHUB-SEO-REPORT.md", help="Output markdown path.")
    parser.add_argument(
        "--action-plan",
        default="GITHUB-ACTION-PLAN.md",
        help="Output markdown path for prioritized action plan (default: GITHUB-ACTION-PLAN.md).",
    )
    parser.add_argument("--json", action="store_true", help="Output merged JSON.")
    parser.add_argument("--output", help="Write merged JSON to file path.")
    args = parser.parse_args()

    try:
        repo = resolve_repo(args.repo)
        token = get_token(args.token)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    outputs = {}
    limitations = []
    explicit_queries, query_warnings = load_explicit_queries(args)
    limitations.extend(query_warnings)

    repo_audit_args = ["--repo", repo, "--provider", args.provider]
    if token:
        repo_audit_args += ["--token", token]
    outputs["repo_audit"] = run_json_script("github_repo_audit.py", repo_audit_args)
    apply_result("repo_audit", outputs["repo_audit"], limitations)

    query_mode = "explicit" if explicit_queries else "none"
    query_source = "cli: --query/--query-file" if explicit_queries else ""
    benchmark_queries = explicit_queries[:]

    if not benchmark_queries:
        repo_audit_data = outputs.get("repo_audit", {}).get("data", {}) if outputs.get("repo_audit", {}).get("ok") else {}
        benchmark_queries = derive_auto_queries(
            repo=repo,
            repo_audit_data=repo_audit_data,
            max_queries=max(1, args.auto_query_max),
        )
        if benchmark_queries:
            query_mode = "auto-derived"
            query_source = "repo slug + metadata + title analysis"
            limitations.append(
                "search_benchmark: no explicit query supplied; using auto-derived repo-specific benchmark queries."
            )
        else:
            limitations.append(
                "search_benchmark skipped: could not derive benchmark queries from repository slug/metadata. Provide `--query`/`--query-file`."
            )

    plan = collect_inputs(args=args, repo=repo, token=token, queries=benchmark_queries)

    for key, (script_name, extra_args) in plan.items():
        if key in outputs:
            continue
        result = run_json_script(script_name, extra_args)
        outputs[key] = result
        apply_result(key, result, limitations)

    if "search_benchmark" not in plan:
        limitations.append(
            "search_benchmark skipped: provide `--query`/`--query-file` (or ensure repo metadata supports auto query derivation)."
        )
    if "competitor_research" not in plan:
        limitations.append(
            "competitor_research skipped: provide `--competitor` repo list or benchmark queries."
        )

    report = {
        "timestamp_utc": utc_now_iso(),
        "repo": repo,
        "provider": args.provider,
        "outputs": outputs,
        "limitations": limitations,
    }
    report["limitations"] = dedupe_preserve(report["limitations"])
    report["scores"] = extract_score(outputs)
    raw_findings = collect_findings(outputs)
    verification_result = verify_findings(
        findings=raw_findings,
        context={
            "readme_metrics": outputs.get("readme_lint", {}).get("data", {}).get("metrics", {}) or {}
        },
    )
    report["findings"] = verification_result.get("findings", [])
    report["verification"] = {
        "raw_count": verification_result.get("raw_count", len(raw_findings)),
        "verified_count": verification_result.get("verified_count", len(report["findings"])),
        "dropped_count": len(verification_result.get("dropped", [])),
        "dropped": verification_result.get("dropped", []),
    }
    report["query_inputs"] = {
        "mode": query_mode,
        "source": query_source,
        "queries": benchmark_queries,
    }
    report["title_analysis"] = outputs.get("repo_audit", {}).get("data", {}).get("title_analysis", {})
    report["backlink_plan"] = build_backlink_plan(outputs)
    report["markdown_path"] = args.markdown
    report["action_plan_path"] = args.action_plan

    markdown = build_markdown(report)
    with open(args.markdown, "w", encoding="utf-8") as f:
        f.write(markdown)
    action_plan_markdown = build_action_plan_markdown(report)
    with open(args.action_plan, "w", encoding="utf-8") as f:
        f.write(action_plan_markdown)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Generated markdown report: {args.markdown}")
        print(f"Generated action plan: {args.action_plan}")
        if limitations:
            print("Limitations:")
            for item in limitations[:10]:
                print(f"- {item}")


if __name__ == "__main__":
    main()

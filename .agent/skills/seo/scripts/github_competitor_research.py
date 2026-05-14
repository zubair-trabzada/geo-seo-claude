#!/usr/bin/env python3
"""
GitHub Competitor Research

Builds a competitor intelligence snapshot from GitHub search queries, then
extracts metadata and README pattern gaps against the target repository.

Usage:
  python github_competitor_research.py --repo owner/repo --query "seo skill" --json
  python github_competitor_research.py --repo owner/repo --query-file queries.txt --top-n 8 --json
"""

import argparse
import base64
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone

from github_api import GitHubAPIError, auth_context, fetch_json, get_token, normalize_repo_slug, resolve_repo


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _dedupe(values: list) -> list:
    out = []
    seen = set()
    for item in values:
        key = item.lower().strip()
        if key and key not in seen:
            out.append(item.strip())
            seen.add(key)
    return out


def load_queries(args) -> list:
    queries = []
    if args.query:
        queries.extend([q.strip() for q in args.query if q.strip()])
    if args.query_file:
        if not os.path.exists(args.query_file):
            raise GitHubAPIError(f"Query file not found: {args.query_file}")
        with open(args.query_file, "r", encoding="utf-8") as f:
            for line in f:
                text = line.strip()
                if text and not text.startswith("#"):
                    queries.append(text)
    return _dedupe(queries)


def parse_iso8601(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def days_since(value: str):
    dt = parse_iso8601(value)
    if not dt:
        return None
    return (datetime.now(timezone.utc) - dt).days


def run_query_candidates(
    repo: str,
    query: str,
    token: str,
    provider: str,
    per_page: int,
    max_pages: int,
) -> dict:
    out = {"query": query, "sampled_results": 0, "total_count": None, "errors": []}
    candidates = []
    rank = 0
    for page in range(1, max_pages + 1):
        params = {"q": query, "per_page": per_page, "page": page}
        try:
            response = fetch_json(
                "/search/repositories",
                token=token,
                params=params,
                provider=provider,
                timeout=35,
            )
            data = response.get("data", {})
        except GitHubAPIError as exc:
            out["errors"].append(f"Page {page}: {exc} (status: {exc.status or 'unknown'})")
            break

        if out["total_count"] is None:
            out["total_count"] = data.get("total_count")

        items = data.get("items", [])
        if not items:
            break

        for item in items:
            rank += 1
            out["sampled_results"] += 1
            full_name = item.get("full_name") or ""
            if full_name.lower() == repo.lower():
                continue
            candidates.append(
                {
                    "full_name": full_name,
                    "rank": rank,
                    "stargazers_count": int(item.get("stargazers_count", 0)),
                    "description": item.get("description") or "",
                    "topics": item.get("topics") or [],
                    "html_url": item.get("html_url"),
                }
            )
    out["candidates"] = candidates
    return out


def aggregate_candidates(query_runs: list) -> dict:
    aggregate = {}
    for run in query_runs:
        query = run["query"]
        for item in run.get("candidates", []):
            slug = item["full_name"]
            entry = aggregate.setdefault(
                slug,
                {
                    "full_name": slug,
                    "seen_in_queries": 0,
                    "best_rank": item["rank"],
                    "query_ranks": {},
                    "sample_item": item,
                },
            )
            if query not in entry["query_ranks"]:
                entry["seen_in_queries"] += 1
            entry["query_ranks"][query] = min(entry["query_ranks"].get(query, 10**9), item["rank"])
            entry["best_rank"] = min(entry["best_rank"], item["rank"])
    return aggregate


def score_competitor(entry: dict) -> tuple:
    # Lower rank and wider query coverage should bubble up.
    return (-entry["seen_in_queries"], entry["best_rank"])


def fetch_repo_metadata(repo: str, token: str, provider: str) -> dict:
    try:
        response = fetch_json(f"/repos/{repo}", token=token, provider=provider, timeout=30)
        return response.get("data", {})
    except GitHubAPIError:
        return {}


def decode_readme_content(payload: dict) -> str:
    content = payload.get("content") or ""
    if not content:
        return ""
    try:
        raw = base64.b64decode(content.encode("utf-8"), validate=False)
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def fetch_readme_metrics(repo: str, token: str, provider: str) -> dict:
    try:
        response = fetch_json(f"/repos/{repo}/readme", token=token, provider=provider, timeout=30)
        payload = response.get("data", {})
    except GitHubAPIError:
        return {"available": False}

    text = decode_readme_content(payload)
    if not text:
        return {"available": False}

    headings = re.findall(r"^(#{1,6})\s+.+$", text, flags=re.MULTILINE)
    words = re.findall(r"\b[\w']+\b", re.sub(r"```.*?```", "", text, flags=re.DOTALL))
    images = re.findall(r"!\[(.*?)\]\((.*?)\)", text)
    lower = text.lower()

    return {
        "available": True,
        "word_count": len(words),
        "heading_count": len(headings),
        "h1_count": len([h for h in headings if len(h) == 1]),
        "image_count": len(images),
        "images_missing_alt": len([img for img in images if not (img[0] or "").strip()]),
        "has_install_section": "install" in lower or "getting started" in lower or "quickstart" in lower,
        "has_contributing_section": "contribut" in lower,
        "has_examples_section": "example" in lower or "usage" in lower or "demo" in lower,
    }


def summarize_gaps(target_repo_data: dict, competitor_details: list) -> dict:
    target_topics = set((target_repo_data.get("topics") or []))
    target_desc = (target_repo_data.get("description") or "").strip()
    target_desc_words = len(re.findall(r"\b[\w']+\b", target_desc))

    competitor_topics = Counter()
    competitor_readme_signals = Counter()
    competitor_desc_words = []

    for item in competitor_details:
        md = item.get("metadata", {})
        rm = item.get("readme_metrics", {})
        topics = md.get("topics") or []
        competitor_topics.update(topics)
        desc = (md.get("description") or "").strip()
        competitor_desc_words.append(len(re.findall(r"\b[\w']+\b", desc)))

        if rm.get("has_install_section"):
            competitor_readme_signals["install"] += 1
        if rm.get("has_contributing_section"):
            competitor_readme_signals["contributing"] += 1
        if rm.get("has_examples_section"):
            competitor_readme_signals["examples"] += 1

    topic_gaps = []
    for topic, freq in competitor_topics.most_common(40):
        if topic not in target_topics:
            topic_gaps.append({"topic": topic, "covered_by_competitors": freq})
    topic_gaps = topic_gaps[:12]

    avg_desc_words = round(sum(competitor_desc_words) / len(competitor_desc_words), 2) if competitor_desc_words else None

    opportunities = []
    if topic_gaps:
        top = ", ".join([t["topic"] for t in topic_gaps[:5]])
        opportunities.append(
            {
                "severity": "Warning",
                "area": "Topics",
                "finding": "High-frequency competitor topics are missing from target repo.",
                "evidence": f"Missing topic examples: {top}",
                "fix": "Add relevant missing topics (without exceeding 20 total) based on actual repository scope.",
            }
        )

    if avg_desc_words is not None and target_desc_words and target_desc_words < avg_desc_words:
        opportunities.append(
            {
                "severity": "Info",
                "area": "Description",
                "finding": "Target repository description is shorter than competitor baseline.",
                "evidence": f"Target words: {target_desc_words}, competitor average: {avg_desc_words}",
                "fix": "Expand description with intent terms, scope, and supported environments.",
            }
        )

    for signal_key, label in (("install", "install"), ("examples", "usage/examples"), ("contributing", "contributing")):
        if competitor_readme_signals.get(signal_key, 0) >= 2:
            opportunities.append(
                {
                    "severity": "Info",
                    "area": "README",
                    "finding": f"Competitors frequently include `{label}` sections.",
                    "evidence": f"{competitor_readme_signals.get(signal_key, 0)} competitor repos include this pattern.",
                    "fix": f"Ensure README has a clear `{label}` section near the top-level navigation flow.",
                }
            )

    return {
        "target_topics_count": len(target_topics),
        "topic_gaps": topic_gaps,
        "description_word_count_target": target_desc_words,
        "description_word_count_competitor_avg": avg_desc_words,
        "readme_pattern_frequency": dict(competitor_readme_signals),
        "opportunities": opportunities,
    }


def build_report(
    repo: str,
    token: str,
    provider: str,
    queries: list,
    competitors: list,
    per_page: int,
    max_pages: int,
    top_n: int,
) -> dict:
    ctx = auth_context(token=token)
    report = {
        "timestamp_utc": utc_now_iso(),
        "repo": repo,
        "provider": provider,
        "auth_context": ctx,
        "token_present": bool(token),
        "queries": queries,
        "query_runs": [],
        "competitors": [],
        "gaps": {},
        "limitations": [],
    }

    if not token:
        if ctx.get("gh_authenticated"):
            report["limitations"].append(
                "No GitHub token found. Using authenticated gh CLI fallback for competitor research."
            )
        elif ctx.get("gh_available"):
            report["limitations"].append(
                "No GitHub token found and gh CLI is not authenticated. Run `gh auth login -h github.com` or set GITHUB_TOKEN/GH_TOKEN."
            )
        else:
            report["limitations"].append(
                "No GitHub token found and gh CLI is unavailable. Competitor research may be rate-limited; set GITHUB_TOKEN/GH_TOKEN."
            )

    ranked = []
    if competitors:
        for slug in competitors:
            if slug.lower() == repo.lower():
                continue
            ranked.append(
                {
                    "full_name": slug,
                    "seen_in_queries": 0,
                    "best_rank": None,
                    "query_ranks": {},
                    "sample_item": {"description": "", "topics": [], "stargazers_count": 0, "html_url": f"https://github.com/{slug}"},
                }
            )
        ranked = ranked[:top_n]
    elif queries:
        query_run_full = []
        for query in queries:
            run = run_query_candidates(
                repo=repo,
                query=query,
                token=token,
                provider=provider,
                per_page=per_page,
                max_pages=max_pages,
            )
            query_run_full.append(run)
            report["query_runs"].append({
                "query": run["query"],
                "sampled_results": run["sampled_results"],
                "total_count": run["total_count"],
                "errors": run["errors"],
            })
            for err in run.get("errors", []):
                report["limitations"].append(f"{query}: {err}")
        aggregate = aggregate_candidates(query_run_full)
        ranked = sorted(aggregate.values(), key=score_competitor)[:top_n]
    else:
        report["limitations"].append(
            "No competitor inputs provided. Supply `--query/--query-file` from LLM/web search or pass explicit `--competitor` repo slugs."
        )

    target_repo_data = fetch_repo_metadata(repo=repo, token=token, provider=provider)
    competitor_details = []
    for entry in ranked:
        slug = entry["full_name"]
        md = fetch_repo_metadata(repo=slug, token=token, provider=provider)
        rm = fetch_readme_metrics(repo=slug, token=token, provider=provider)
        competitor_details.append(
            {
                "full_name": slug,
                "seen_in_queries": entry["seen_in_queries"],
                "best_rank": entry["best_rank"],
                "query_ranks": entry["query_ranks"],
                "metadata": {
                    "description": md.get("description") or entry["sample_item"].get("description", ""),
                    "topics": md.get("topics") or entry["sample_item"].get("topics", []),
                    "stargazers_count": int(md.get("stargazers_count", entry["sample_item"].get("stargazers_count", 0))),
                    "forks_count": int(md.get("forks_count", 0)),
                    "homepage": md.get("homepage") or "",
                    "pushed_at": md.get("pushed_at"),
                    "pushed_days_ago": days_since(md.get("pushed_at")),
                    "html_url": md.get("html_url") or entry["sample_item"].get("html_url"),
                },
                "readme_metrics": rm,
            }
        )

    report["competitors"] = competitor_details
    report["gaps"] = summarize_gaps(target_repo_data=target_repo_data, competitor_details=competitor_details)
    report["target_metadata"] = {
        "description": target_repo_data.get("description") or "",
        "topics": target_repo_data.get("topics") or [],
        "stargazers_count": int(target_repo_data.get("stargazers_count", 0)),
        "forks_count": int(target_repo_data.get("forks_count", 0)),
        "html_url": target_repo_data.get("html_url") or f"https://github.com/{repo}",
    }
    report["summary"] = {
        "competitors_analyzed": len(competitor_details),
        "queries_used": len(queries),
        "top_topic_gaps": report["gaps"].get("topic_gaps", [])[:5],
    }
    return report


def print_text(report: dict):
    print(f"\nGitHub Competitor Research: {report.get('repo')}")
    print("=" * 60)
    summary = report.get("summary", {})
    print(
        f"Competitors analyzed: {summary.get('competitors_analyzed', 0)} | "
        f"Queries: {summary.get('queries_used', 0)}"
    )
    top_gaps = summary.get("top_topic_gaps", [])
    if top_gaps:
        print("Top topic gaps:")
        for gap in top_gaps:
            print(f"- {gap['topic']} ({gap['covered_by_competitors']} competitors)")
    if report.get("limitations"):
        print("\nLimitations:")
        for item in report["limitations"][:10]:
            print(f"- {item}")


def main():
    parser = argparse.ArgumentParser(description="Run GitHub competitor research against query-defined peers.")
    parser.add_argument("--repo", help="Repository slug or URL (owner/repo). If omitted, infer from git origin.")
    parser.add_argument("--token", help="GitHub token override. Prefer env vars GITHUB_TOKEN or GH_TOKEN.")
    parser.add_argument("--query", action="append", help="Search query (repeatable).")
    parser.add_argument("--query-file", help="Path to newline-delimited query file.")
    parser.add_argument("--competitor", action="append", help="Explicit competitor repo slug/URL (repeatable).")
    parser.add_argument("--per-page", type=int, default=30, help="Results per page (default: 30, max: 100).")
    parser.add_argument("--max-pages", type=int, default=2, help="Max search pages per query (default: 2).")
    parser.add_argument("--top-n", type=int, default=6, help="Number of competitor repos to analyze deeply (default: 6).")
    parser.add_argument(
        "--provider",
        choices=["auto", "api", "gh"],
        default="auto",
        help="GitHub data provider mode (default: auto).",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    parser.add_argument("--output", help="Write JSON report to path.")
    args = parser.parse_args()

    try:
        repo = resolve_repo(args.repo)
        token = get_token(args.token)
        queries = load_queries(args)
    except GitHubAPIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    competitors = []
    if args.competitor:
        for raw in args.competitor:
            slug = normalize_repo_slug(raw)
            if slug:
                competitors.append(slug)
    competitors = _dedupe(competitors)

    report = build_report(
        repo=repo,
        token=token,
        provider=args.provider,
        queries=queries,
        competitors=competitors,
        per_page=max(1, min(100, args.per_page)),
        max_pages=max(1, args.max_pages),
        top_n=max(1, min(25, args.top_n)),
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text(report)


if __name__ == "__main__":
    main()

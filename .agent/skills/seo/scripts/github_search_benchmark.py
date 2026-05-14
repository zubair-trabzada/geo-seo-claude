#!/usr/bin/env python3
"""
GitHub Search Benchmark

Benchmarks repository visibility for a deterministic set of search queries.

Usage:
  python github_search_benchmark.py --repo owner/repo --query "seo skill" --json
  python github_search_benchmark.py --repo owner/repo --query-file queries.txt --max-pages 2
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from github_api import (
    GitHubAPIError,
    auth_context,
    fetch_json,
    get_token,
    resolve_repo,
)


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


def run_query(repo: str, query: str, token: str, per_page: int, max_pages: int, provider: str) -> dict:
    target_rank = None
    competitors = []
    sampled = 0
    total_count = None
    errors = []

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
            errors.append(f"Page {page}: {exc} (status: {exc.status or 'unknown'})")
            break

        if total_count is None:
            total_count = data.get("total_count", 0)

        items = data.get("items", [])
        if not items:
            break

        for item in items:
            sampled += 1
            full_name = (item.get("full_name") or "").lower()
            if target_rank is None and full_name == repo.lower():
                target_rank = sampled
            if len(competitors) < 10 and full_name != repo.lower():
                competitors.append(
                    {
                        "full_name": item.get("full_name"),
                        "stargazers_count": item.get("stargazers_count", 0),
                        "description": item.get("description") or "",
                        "topics": item.get("topics") or [],
                        "html_url": item.get("html_url"),
                    }
                )

        if target_rank is not None and len(competitors) >= 5:
            break

    return {
        "query": query,
        "total_count": total_count,
        "sampled_results": sampled,
        "target_rank": target_rank,
        "target_found": target_rank is not None,
        "top_competitors": competitors[:5],
        "errors": errors,
    }


def summarize(results: list) -> dict:
    found = [r for r in results if r.get("target_found")]
    not_found = [r["query"] for r in results if not r.get("target_found")]
    avg_rank = None
    if found:
        avg_rank = round(sum(r["target_rank"] for r in found) / len(found), 2)
    return {
        "queries_total": len(results),
        "queries_found": len(found),
        "queries_not_found": len(not_found),
        "not_found_queries": not_found,
        "average_rank_when_found": avg_rank,
    }


def print_text(report: dict):
    print(f"\nGitHub Search Benchmark: {report.get('repo')}")
    print("=" * 60)
    summary = report.get("summary", {})
    print(
        f"Found in {summary.get('queries_found', 0)}/{summary.get('queries_total', 0)} queries | "
        f"Average rank when found: {summary.get('average_rank_when_found', 'NA')}"
    )
    if report.get("limitations"):
        print("\nLimitations:")
        for item in report["limitations"]:
            print(f"- {item}")
    print("\nQueries:")
    for item in report.get("results", []):
        rank = item["target_rank"] if item["target_rank"] is not None else "Not found"
        print(f"- {item['query']}: rank={rank}, sampled={item['sampled_results']}, total={item['total_count']}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark repository visibility across GitHub search queries.")
    parser.add_argument("--repo", help="Repository slug or URL (owner/repo). If omitted, infer from git origin.")
    parser.add_argument("--token", help="GitHub token override. Prefer env vars GITHUB_TOKEN or GH_TOKEN.")
    parser.add_argument("--query", action="append", help="Search query (repeatable).")
    parser.add_argument("--query-file", help="Path to newline-delimited query file.")
    parser.add_argument("--per-page", type=int, default=50, help="Results per page (default: 50, max: 100).")
    parser.add_argument("--max-pages", type=int, default=2, help="Max pages per query (default: 2).")
    parser.add_argument(
        "--provider",
        choices=["auto", "api", "gh"],
        default="auto",
        help="GitHub data provider mode (default: auto).",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    parser.add_argument("--output", help="Write JSON report to file path.")
    args = parser.parse_args()

    try:
        repo = resolve_repo(args.repo)
        token = get_token(args.token)
        queries = load_queries(args)
    except GitHubAPIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    per_page = max(1, min(100, args.per_page))
    max_pages = max(1, args.max_pages)

    report = {
        "timestamp_utc": utc_now_iso(),
        "repo": repo,
        "auth_context": auth_context(token=token),
        "token_present": bool(token),
        "queries": queries,
        "results": [],
        "limitations": [],
    }

    if not token:
        ctx = report["auth_context"]
        if ctx.get("gh_authenticated"):
            report["limitations"].append(
                "No GitHub token found. Using authenticated gh CLI fallback for search."
            )
        elif ctx.get("gh_available"):
            report["limitations"].append(
                "No GitHub token found and gh CLI is not authenticated. Run `gh auth login -h github.com` or set GITHUB_TOKEN/GH_TOKEN."
            )
        else:
            report["limitations"].append(
                "No GitHub token found and gh CLI is unavailable. Search may be rate-limited; set GITHUB_TOKEN/GH_TOKEN."
            )

    if not queries:
        report["limitations"].append(
            "No queries provided. Supply `--query` or `--query-file` using LLM/web-search-derived intent keywords."
        )
    else:
        for query in queries:
            result = run_query(
                repo=repo,
                query=query,
                token=token,
                per_page=per_page,
                max_pages=max_pages,
                provider=args.provider,
            )
            if result.get("errors"):
                report["limitations"].extend([f"{query}: {err}" for err in result["errors"]])
            report["results"].append(result)

    report["summary"] = summarize(report["results"])

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text(report)


if __name__ == "__main__":
    main()

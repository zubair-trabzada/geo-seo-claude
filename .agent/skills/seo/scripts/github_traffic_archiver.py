#!/usr/bin/env python3
"""
GitHub Traffic Archiver

Fetches GitHub traffic endpoints and appends timestamped snapshots to local
storage so data survives GitHub's 14-day traffic window.

Usage:
  python github_traffic_archiver.py --repo owner/repo --json
  python github_traffic_archiver.py --repo owner/repo --archive-dir .github-seo-data
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


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def append_jsonl(path: str, payload: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, separators=(",", ":")) + "\n")


def write_json(path: str, payload: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def fetch_endpoint(path: str, token: str, provider: str) -> dict:
    try:
        response = fetch_json(path, token=token, provider=provider, timeout=30)
        return {"ok": True, "data": response.get("data", {}), "rate_limit": response.get("rate_limit", {})}
    except GitHubAPIError as exc:
        return {"ok": False, "error": str(exc), "status": exc.status, "details": exc.details}


def collect_traffic(repo: str, token: str, provider: str) -> dict:
    base = f"/repos/{repo}/traffic"
    result = {
        "views": fetch_endpoint(f"{base}/views", token, provider),
        "clones": fetch_endpoint(f"{base}/clones", token, provider),
        "referrers": fetch_endpoint(f"{base}/popular/referrers", token, provider),
        "paths": fetch_endpoint(f"{base}/popular/paths", token, provider),
    }
    return result


def build_snapshot(repo: str, token: str, provider: str) -> dict:
    ctx = auth_context(token=token)
    snapshot = {
        "timestamp_utc": utc_now_iso(),
        "repo": repo,
        "auth_context": ctx,
        "token_present": bool(token),
        "endpoints": {},
        "limitations": [],
    }
    if not token:
        if ctx.get("gh_authenticated"):
            snapshot["limitations"].append(
                "No GitHub token found. Using authenticated gh CLI fallback for traffic endpoints."
            )
        elif ctx.get("gh_available"):
            snapshot["limitations"].append(
                "No GitHub token found and gh CLI is not authenticated. Traffic endpoints require auth. Run `gh auth login -h github.com` or set GITHUB_TOKEN/GH_TOKEN."
            )
        else:
            snapshot["limitations"].append(
                "No GitHub token found and gh CLI is unavailable. Traffic endpoints require auth; set GITHUB_TOKEN/GH_TOKEN."
            )

    endpoint_data = collect_traffic(repo, token, provider)
    endpoint_summary = {}

    for key, payload in endpoint_data.items():
        if payload.get("ok"):
            endpoint_summary[key] = payload.get("data")
        else:
            endpoint_summary[key] = {"error": payload.get("error"), "status": payload.get("status")}
            snapshot["limitations"].append(
                f"{key} endpoint failed: {payload.get('error')} (status: {payload.get('status', 'unknown')})"
            )

    snapshot["endpoints"] = endpoint_summary

    views = endpoint_summary.get("views", {})
    clones = endpoint_summary.get("clones", {})
    snapshot["totals"] = {
        "views_count": views.get("count"),
        "views_uniques": views.get("uniques"),
        "clones_count": clones.get("count"),
        "clones_uniques": clones.get("uniques"),
    }
    return snapshot


def print_text(snapshot: dict, archive_paths: dict):
    print(f"\nGitHub Traffic Snapshot: {snapshot.get('repo')}")
    print("=" * 60)
    print(f"Timestamp (UTC): {snapshot.get('timestamp_utc')}")
    totals = snapshot.get("totals", {})
    print(
        f"Views: {totals.get('views_count', 'NA')} (unique: {totals.get('views_uniques', 'NA')}) | "
        f"Clones: {totals.get('clones_count', 'NA')} (unique: {totals.get('clones_uniques', 'NA')})"
    )
    if snapshot.get("limitations"):
        print("\nLimitations:")
        for item in snapshot["limitations"]:
            print(f"- {item}")
    if archive_paths:
        print("\nArchive files:")
        for key, value in archive_paths.items():
            print(f"- {key}: {value}")


def main():
    parser = argparse.ArgumentParser(description="Archive GitHub traffic metrics to local history files.")
    parser.add_argument("--repo", help="Repository slug or URL (owner/repo). If omitted, infer from git origin.")
    parser.add_argument("--token", help="GitHub token override. Prefer env vars GITHUB_TOKEN or GH_TOKEN.")
    parser.add_argument("--archive-dir", default=".github-seo-data", help="Archive directory (default: .github-seo-data)")
    parser.add_argument(
        "--provider",
        choices=["auto", "api", "gh"],
        default="auto",
        help="GitHub data provider mode (default: auto).",
    )
    parser.add_argument("--no-write", action="store_true", help="Do not write archive files.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    parser.add_argument("--output", help="Write current snapshot JSON to file path.")
    args = parser.parse_args()

    try:
        repo = resolve_repo(args.repo)
        token = get_token(args.token)
        snapshot = build_snapshot(repo, token, provider=args.provider)
    except GitHubAPIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        sys.exit(130)

    archive_paths = {}
    if not args.no_write:
        ensure_dir(args.archive_dir)
        history_path = os.path.join(args.archive_dir, "traffic_history.jsonl")
        latest_path = os.path.join(args.archive_dir, "latest_traffic_snapshot.json")
        append_jsonl(history_path, snapshot)
        write_json(latest_path, snapshot)
        archive_paths["traffic_history"] = history_path
        archive_paths["latest_snapshot"] = latest_path

    if args.output:
        write_json(args.output, snapshot)

    if args.json:
        out = {"snapshot": snapshot, "archive_paths": archive_paths}
        print(json.dumps(out, indent=2))
    else:
        print_text(snapshot, archive_paths)


if __name__ == "__main__":
    main()

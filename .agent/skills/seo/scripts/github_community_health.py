#!/usr/bin/env python3
"""
GitHub Community Health Checker

Checks contribution/trust artifacts locally and via GitHub community profile API.

Usage:
  python github_community_health.py --repo owner/repo --json
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
    infer_repo_from_git,
    resolve_repo,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def local_artifacts(cwd: str) -> dict:
    return {
        "README.md": os.path.exists(os.path.join(cwd, "README.md")),
        "LICENSE": os.path.exists(os.path.join(cwd, "LICENSE")),
        "CONTRIBUTING.md": os.path.exists(os.path.join(cwd, "CONTRIBUTING.md")),
        "CODE_OF_CONDUCT.md": os.path.exists(os.path.join(cwd, "CODE_OF_CONDUCT.md")),
        "SECURITY.md": os.path.exists(os.path.join(cwd, "SECURITY.md")),
        "SUPPORT.md": os.path.exists(os.path.join(cwd, "SUPPORT.md")),
        "CITATION.cff": os.path.exists(os.path.join(cwd, "CITATION.cff")),
        ".github/ISSUE_TEMPLATE": os.path.isdir(os.path.join(cwd, ".github", "ISSUE_TEMPLATE")),
        ".github/PULL_REQUEST_TEMPLATE.md": os.path.exists(
            os.path.join(cwd, ".github", "PULL_REQUEST_TEMPLATE.md")
        ),
    }


def add_finding(findings: list, severity: str, finding: str, evidence: str, fix: str, confidence: str = "Confirmed"):
    findings.append(
        {
            "severity": severity,
            "confidence": confidence,
            "finding": finding,
            "evidence": evidence,
            "fix": fix,
        }
    )


def evaluate(repo: str, token: str, provider: str, cwd: str) -> dict:
    ctx = auth_context(token=token)
    local_repo = infer_repo_from_git(cwd=cwd)
    local_checks_enabled = bool(local_repo) and (local_repo.lower() == repo.lower())
    local = local_artifacts(cwd) if local_checks_enabled else {}
    findings = []
    limitations = []
    remote = {}
    confidence = "Confirmed"

    required = ("README.md", "LICENSE")
    recommended = (
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        ".github/ISSUE_TEMPLATE",
        ".github/PULL_REQUEST_TEMPLATE.md",
        "CITATION.cff",
    )

    if local_checks_enabled:
        for file_name in required:
            if not local.get(file_name):
                add_finding(
                    findings,
                    "Critical",
                    f"Missing required repository artifact: {file_name}.",
                    f"Local check indicates `{file_name}` is absent.",
                    f"Add `{file_name}` to satisfy baseline community trust requirements.",
                )

        for file_name in recommended:
            if not local.get(file_name):
                add_finding(
                    findings,
                    "Warning",
                    f"Missing recommended community artifact: {file_name}.",
                    f"Local check indicates `{file_name}` is absent.",
                    f"Add `{file_name}` to improve contribution readiness and trust signals.",
                )
    else:
        limitations.append(
            "Local filesystem checks skipped because target repo does not match current working repository."
        )

    if not token:
        if ctx.get("gh_authenticated"):
            limitations.append("No GitHub token provided. Using authenticated gh CLI fallback for remote profile checks.")
        elif ctx.get("gh_available"):
            limitations.append(
                "No GitHub token provided and gh CLI is not authenticated. Run `gh auth login -h github.com` or set GITHUB_TOKEN/GH_TOKEN."
            )
        else:
            limitations.append("No GitHub token provided and gh CLI is unavailable. Set GITHUB_TOKEN/GH_TOKEN.")

    try:
        payload = fetch_json(f"/repos/{repo}/community/profile", token=token, provider=provider)
        remote = payload.get("data", {})
    except GitHubAPIError as exc:
        confidence = "Likely"
        limitations.append(f"Remote community profile unavailable: {exc} (status: {exc.status or 'unknown'})")

    if remote:
        health = remote.get("health_percentage")
        files = remote.get("files", {})
        if isinstance(health, (int, float)) and health < 85:
            add_finding(
                findings,
                "Warning",
                "GitHub community profile health is below baseline target.",
                f"health_percentage={health}",
                "Add missing governance artifacts until health percentage reaches >=85.",
                confidence=confidence,
            )
        for key in ("code_of_conduct", "contributing", "issue_template", "pull_request_template", "readme", "license"):
            if not files.get(key):
                add_finding(
                    findings,
                    "Warning",
                    f"Remote community profile marks `{key}` as missing.",
                    f"GitHub API `files.{key}` is null/false.",
                    f"Add `{key}`-related file(s) so GitHub recognizes this component.",
                    confidence=confidence,
                )

    total_checks = len(required) + len(recommended)
    passed_checks = sum(1 for key in required + recommended if local.get(key)) if local_checks_enabled else 0
    local_completion = round((passed_checks / total_checks) * 100, 2) if local_checks_enabled else None

    critical_count = sum(1 for f in findings if f["severity"] == "Critical")
    warning_count = sum(1 for f in findings if f["severity"] == "Warning")
    base = local_completion if isinstance(local_completion, (int, float)) else 100
    score = max(0, int(base - (critical_count * 20) - (warning_count * 5)))

    if not findings:
        add_finding(
            findings,
            "Pass",
            "Community health baseline is satisfied.",
            "Local and remote checks did not detect major gaps.",
            "Keep artifacts current as repository evolves.",
        )

    return {
        "timestamp_utc": utc_now_iso(),
        "repo": repo,
        "provider": provider,
        "auth_context": ctx,
        "local_repo_context": {"detected_local_repo": local_repo or "", "local_checks_enabled": local_checks_enabled},
        "token_present": bool(token),
        "local_completion_percent": local_completion,
        "score": score,
        "local_artifacts": local,
        "remote_profile": {
            "health_percentage": remote.get("health_percentage"),
            "description": remote.get("description"),
            "documentation": remote.get("documentation"),
            "files": remote.get("files") if isinstance(remote.get("files"), dict) else {},
        },
        "limitations": limitations,
        "findings": findings,
    }


def print_text(report: dict):
    print(f"\nGitHub Community Health: {report.get('repo')}")
    print("=" * 60)
    print(f"Score: {report.get('score', 'NA')}/100")
    print(f"Local completion: {report.get('local_completion_percent', 0)}%")
    remote_health = report.get("remote_profile", {}).get("health_percentage")
    if remote_health is not None:
        print(f"Remote health: {remote_health}%")
    if report.get("limitations"):
        print("\nLimitations:")
        for item in report["limitations"]:
            print(f"- {item}")
    print("\nFindings:")
    for finding in report.get("findings", [])[:10]:
        print(f"- [{finding['severity']}] {finding['finding']}")


def main():
    parser = argparse.ArgumentParser(description="Check GitHub repository community health and trust artifacts.")
    parser.add_argument("--repo", help="Repository slug or URL (owner/repo). If omitted, infer from git origin.")
    parser.add_argument("--token", help="GitHub token override. Prefer env vars GITHUB_TOKEN or GH_TOKEN.")
    parser.add_argument("--cwd", default=".", help="Working directory for local artifact checks (default: .)")
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
        repo = resolve_repo(args.repo, cwd=args.cwd)
        token = get_token(args.token)
        report = evaluate(repo=repo, token=token, provider=args.provider, cwd=args.cwd)
    except GitHubAPIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        sys.exit(130)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text(report)


if __name__ == "__main__":
    main()

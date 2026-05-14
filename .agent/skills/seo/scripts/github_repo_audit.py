#!/usr/bin/env python3
"""
GitHub Repository SEO Audit

Audits repository metadata, trust signals, and community health with GitHub API
data (when token is available) plus local file fallback checks.

Usage:
  python github_repo_audit.py --repo owner/repo --json
  python github_repo_audit.py --repo owner/repo --token $GITHUB_TOKEN
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone

from github_api import (
    GitHubAPIError,
    auth_context,
    fetch_json,
    get_token,
    infer_repo_from_git,
    resolve_repo,
)

STOP_WORDS = {
    "the", "and", "for", "with", "from", "into", "this", "that", "your",
    "are", "was", "were", "been", "being", "have", "has", "had", "will",
    "would", "could", "should", "about", "over", "under", "between", "while",
    "where", "when", "which", "what", "into", "than", "then", "them", "they",
    "you", "our", "their", "its", "it's", "via", "all", "any", "not", "can",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def local_file_signals(cwd: str) -> dict:
    """Check local governance/community files."""
    checks = {
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
    return checks


def add_finding(
    findings: list,
    area: str,
    severity: str,
    confidence: str,
    finding: str,
    evidence: str,
    fix: str,
):
    findings.append(
        {
            "area": area,
            "severity": severity,
            "confidence": confidence,
            "finding": finding,
            "evidence": evidence,
            "fix": fix,
        }
    )


def score_findings(findings: list) -> dict:
    """Compute a directional score from severity counts."""
    critical = sum(1 for f in findings if f["severity"] == "Critical")
    warning = sum(1 for f in findings if f["severity"] == "Warning")
    score = max(0, 100 - (critical * 20) - (warning * 8))
    if score >= 90:
        rating = "Excellent"
    elif score >= 70:
        rating = "Good"
    elif score >= 50:
        rating = "Needs Improvement"
    elif score >= 30:
        rating = "Poor"
    else:
        rating = "Critical"
    return {"score": score, "rating": rating, "critical": critical, "warning": warning}


def _tokenize(text: str) -> list:
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [w for w in words if len(w) > 1 and w not in STOP_WORDS]


def _dedupe_keep_order(items: list) -> list:
    out = []
    seen = set()
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _format_title_token(token: str) -> str:
    mapping = {"seo": "SEO", "llm": "LLM", "ai": "AI", "api": "API", "github": "GitHub", "aeo": "AEO", "geo": "GEO"}
    return mapping.get(token.lower(), token.capitalize())


def analyze_title_strategy(repo_slug: str, metadata: dict) -> dict:
    """Generate intent-based title and slug recommendations."""
    repo_name = (metadata.get("name") or "").strip()
    if not repo_name and repo_slug:
        repo_name = repo_slug.split("/", 1)[-1]

    description = (metadata.get("description") or "").strip()
    topics = metadata.get("topics") or []

    name_tokens = _tokenize(repo_name.replace("_", " ").replace("-", " "))
    topic_tokens = []
    for topic in topics:
        topic_tokens.extend(_tokenize(topic.replace("-", " ").replace("_", " ")))

    desc_tokens = _tokenize(description)
    desc_freq = Counter(desc_tokens)
    desc_priority = [word for word, _ in desc_freq.most_common(15)]

    priority_seed = name_tokens + topic_tokens + desc_priority
    keywords = _dedupe_keep_order(priority_seed)

    if not keywords:
        keywords = _tokenize(repo_slug.replace("/", " "))

    slug_tokens = keywords[:5] if keywords else []
    if "seo" in keywords and "seo" not in slug_tokens:
        slug_tokens = ["seo"] + slug_tokens[:4]
    slug_tokens = _dedupe_keep_order(slug_tokens)
    recommended_slug = "-".join(slug_tokens) if slug_tokens else repo_name.replace("_", "-").lower()

    title_tokens = []
    for token in slug_tokens:
        if token in ("for", "and", "the"):
            continue
        title_tokens.append(token)
    title_tokens = _dedupe_keep_order(title_tokens)
    display_title = " ".join(_format_title_token(t) for t in title_tokens[:7]).strip()

    alt_titles = []
    if display_title:
        alt_titles.append(display_title)
    alt_titles = _dedupe_keep_order([t for t in alt_titles if t])

    return {
        "current_name": repo_name,
        "current_has_underscore": "_" in repo_name,
        "current_has_hyphen": "-" in repo_name,
        "search_intent_keywords": keywords[:12],
        "recommended_repo_slug": recommended_slug,
        "recommended_display_title": display_title or repo_name,
        "alternative_titles": alt_titles[:3],
        "notes": [
            "Keyword suggestions are intent-based heuristics.",
            "Search volume should be validated separately with keyword tools.",
            "Use hyphen-separated words for slug readability and token separation.",
        ],
    }


def build_audit(repo: str, token: str, cwd: str, provider: str) -> dict:
    ctx = auth_context(token=token)
    local_repo = infer_repo_from_git(cwd=cwd)
    local_checks_enabled = bool(local_repo) and (local_repo.lower() == repo.lower())
    report = {
        "timestamp_utc": utc_now_iso(),
        "repo": repo,
        "auth_context": ctx,
        "local_repo_context": {"detected_local_repo": local_repo or "", "local_checks_enabled": local_checks_enabled},
        "api_access": {"token_present": bool(token), "repo_endpoint_ok": False, "community_endpoint_ok": False},
        "limitations": [],
        "metadata": {},
        "title_analysis": {},
        "community_profile": {},
        "local_signals": local_file_signals(cwd) if local_checks_enabled else {},
        "findings": [],
    }

    repo_data = {}
    community_data = {}
    confidence = "Confirmed"

    if not token:
        if ctx.get("gh_authenticated"):
            report["limitations"].append(
                "No GitHub token found. Using authenticated gh CLI session as fallback."
            )
        elif ctx.get("gh_available"):
            report["limitations"].append(
                "No GitHub token found and gh CLI is not authenticated. Run `gh auth login -h github.com` or set GITHUB_TOKEN/GH_TOKEN."
            )
        else:
            report["limitations"].append(
                "No GitHub token found and gh CLI is unavailable. Set GITHUB_TOKEN/GH_TOKEN for reliable API access."
            )
    if not local_checks_enabled:
        report["limitations"].append(
            "Local filesystem checks skipped because target repo does not match current working repository."
        )

    try:
        repo_resp = fetch_json(f"/repos/{repo}", token=token, provider=provider)
        repo_data = repo_resp.get("data", {})
        report["api_access"]["repo_endpoint_ok"] = True
        report["api_access"]["rate_limit"] = repo_resp.get("rate_limit", {})
    except GitHubAPIError as exc:
        confidence = "Likely"
        report["limitations"].append(
            f"Repository API unavailable: {exc} (status: {exc.status or 'unknown'})"
        )

    try:
        comm_resp = fetch_json(f"/repos/{repo}/community/profile", token=token, provider=provider)
        community_data = comm_resp.get("data", {})
        report["api_access"]["community_endpoint_ok"] = True
    except GitHubAPIError as exc:
        confidence = "Likely"
        report["limitations"].append(
            f"Community profile API unavailable: {exc} (status: {exc.status or 'unknown'})"
        )

    if repo_data:
        report["metadata"] = {
            "name": repo_data.get("name"),
            "full_name": repo_data.get("full_name"),
            "description": repo_data.get("description") or "",
            "homepage": repo_data.get("homepage") or "",
            "topics": repo_data.get("topics") or [],
            "open_graph_image_url": repo_data.get("open_graph_image_url") or "",
            "archived": bool(repo_data.get("archived")),
            "fork": bool(repo_data.get("fork")),
            "stargazers_count": int(repo_data.get("stargazers_count", 0)),
            "forks_count": int(repo_data.get("forks_count", 0)),
            "watchers_count": int(repo_data.get("watchers_count", 0)),
            "open_issues_count": int(repo_data.get("open_issues_count", 0)),
            "pushed_at": repo_data.get("pushed_at"),
            "updated_at": repo_data.get("updated_at"),
            "license": (repo_data.get("license") or {}).get("spdx_id"),
        }

    if community_data:
        report["community_profile"] = {
            "health_percentage": community_data.get("health_percentage"),
            "description": community_data.get("description") or "",
            "documentation": community_data.get("documentation") or "",
            "files": community_data.get("files") or {},
        }

    findings = report["findings"]
    report["title_analysis"] = analyze_title_strategy(repo_slug=repo, metadata=report["metadata"] or {})

    # Metadata checks
    if report["metadata"]:
        md = report["metadata"]
        title_analysis = report["title_analysis"]
        description = (md.get("description") or "").strip()
        topics = md.get("topics") or []
        pushed_days = days_since(md.get("pushed_at"))

        if not description:
            add_finding(
                findings,
                "Metadata",
                "Warning",
                confidence,
                "Repository description is missing.",
                "GitHub metadata `description` is empty.",
                "Add a concise, intent-matched description that explains scope and audience.",
            )
        elif len(description) < 60:
            add_finding(
                findings,
                "Metadata",
                "Info",
                confidence,
                "Repository description is short.",
                f"Description length is {len(description)} characters.",
                "Expand description to include primary use case and distinctive value.",
            )

        if not topics:
            add_finding(
                findings,
                "Metadata",
                "Warning",
                confidence,
                "No repository topics configured.",
                "GitHub topics list is empty.",
                "Add relevant discovery topics (up to 20) for intent coverage.",
            )
        elif len(topics) > 20:
            add_finding(
                findings,
                "Metadata",
                "Critical",
                confidence,
                "Topic count exceeds GitHub topic cap.",
                f"Detected {len(topics)} topics.",
                "Reduce to 20 or fewer high-signal, non-overlapping topics.",
            )
        elif len(topics) < 5:
            add_finding(
                findings,
                "Metadata",
                "Info",
                confidence,
                "Topic coverage may be thin.",
                f"Detected {len(topics)} topics.",
                "Add additional relevant topics to cover primary user intents.",
            )

        if not md.get("homepage"):
            add_finding(
                findings,
                "Metadata",
                "Info",
                confidence,
                "Homepage URL is not set.",
                "GitHub metadata `homepage` is empty.",
                "Set homepage to documentation or project landing page if available.",
            )

        if md.get("archived"):
            add_finding(
                findings,
                "Maintenance",
                "Critical",
                confidence,
                "Repository is archived.",
                "GitHub metadata shows `archived=true`.",
                "Unarchive if active development/discovery is still a goal.",
            )

        if pushed_days is not None and pushed_days > 180:
            add_finding(
                findings,
                "Maintenance",
                "Warning",
                confidence,
                "Repository appears stale.",
                f"Last push was {pushed_days} days ago.",
                "Publish a maintenance release or documentation refresh to signal activity.",
            )

        if title_analysis.get("current_has_underscore"):
            add_finding(
                findings,
                "Metadata",
                "Warning",
                confidence,
                "Repository title/slug uses underscore separators.",
                f"Current repository name: `{title_analysis.get('current_name')}`",
                "Prefer hyphen-separated words in repository slug for clearer token separation in search indexing.",
            )

        suggested_slug = title_analysis.get("recommended_repo_slug", "")
        current_name = (title_analysis.get("current_name") or "").lower()
        if suggested_slug and current_name and suggested_slug != current_name:
            add_finding(
                findings,
                "Metadata",
                "Info",
                confidence,
                "Repository title can be better aligned to search intent keywords.",
                f"Suggested slug: `{suggested_slug}` | Suggested title: `{title_analysis.get('recommended_display_title')}`",
                "Consider renaming repository slug and updating description/topics to reflect the suggested intent keywords.",
            )
    else:
        title_analysis = report["title_analysis"]
        if title_analysis.get("current_has_underscore"):
            add_finding(
                findings,
                "Metadata",
                "Warning",
                "Likely",
                "Repository slug uses underscore separators.",
                f"Current repository name: `{title_analysis.get('current_name')}` (derived from slug)",
                "Prefer hyphen-separated words in repository slug for clearer token separation in search indexing.",
            )

        suggested_slug = title_analysis.get("recommended_repo_slug", "")
        current_name = (title_analysis.get("current_name") or "").lower()
        if suggested_slug and current_name and suggested_slug != current_name:
            add_finding(
                findings,
                "Metadata",
                "Info",
                "Likely",
                "Repository title can be better aligned to intent terms.",
                f"Suggested slug: `{suggested_slug}` | Suggested title: `{title_analysis.get('recommended_display_title')}`",
                "Review slug/title recommendations and align repository naming with high-intent keywords.",
            )

    # Community profile checks from API
    if report["community_profile"]:
        cp = report["community_profile"]
        health = cp.get("health_percentage")
        files = cp.get("files", {})
        if isinstance(health, (int, float)) and health < 85:
            add_finding(
                findings,
                "Community",
                "Warning",
                confidence,
                "Community health score is below recommended baseline.",
                f"GitHub community health is {health}%.",
                "Complete missing governance files and contribution docs to raise score.",
            )

        for key in ("code_of_conduct", "contributing", "issue_template", "pull_request_template", "readme", "license"):
            if not files.get(key):
                add_finding(
                    findings,
                    "Community",
                    "Warning",
                    confidence,
                    f"Missing community profile component: {key}.",
                    f"GitHub community profile `files.{key}` is missing.",
                    f"Add the missing `{key}` file/template in repository root or `.github/`.",
                )

    # Local fallback checks
    if local_checks_enabled:
        local = report["local_signals"]
        for required in ("README.md", "LICENSE"):
            if not local.get(required):
                add_finding(
                    findings,
                    "Community",
                    "Critical",
                    "Confirmed",
                    f"Missing required repository file: {required}.",
                    f"Local file check indicates `{required}` is absent.",
                    f"Add `{required}` to restore baseline project trust and discoverability.",
                )

        for recommended in ("CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md", ".github/ISSUE_TEMPLATE", ".github/PULL_REQUEST_TEMPLATE.md", "CITATION.cff"):
            if not local.get(recommended):
                add_finding(
                    findings,
                    "Community",
                    "Warning",
                    "Confirmed",
                    f"Missing recommended trust artifact: {recommended}.",
                    f"Local file check indicates `{recommended}` is absent.",
                    f"Add `{recommended}` to improve contribution readiness and credibility signals.",
                )

    if not findings:
        add_finding(
            findings,
            "Overall",
            "Pass",
            "Confirmed",
            "No major GitHub SEO issues detected in current scope.",
            "Metadata, community, and local trust checks met baseline.",
            "Continue weekly monitoring and query benchmark tracking.",
        )

    report["summary"] = score_findings(findings)
    return report


def print_text(report: dict):
    summary = report.get("summary", {})
    print(f"\nGitHub Repo Audit: {report.get('repo')}")
    print("=" * 60)
    print(f"Score: {summary.get('score', 'NA')}/100 ({summary.get('rating', 'Unknown')})")
    print(f"Critical: {summary.get('critical', 0)} | Warning: {summary.get('warning', 0)}")

    if report.get("limitations"):
        print("\nEnvironment limitations:")
        for item in report["limitations"]:
            print(f"- {item}")

    title_analysis = report.get("title_analysis", {})
    if title_analysis:
        print("\nTitle recommendations:")
        print(f"- Suggested slug: {title_analysis.get('recommended_repo_slug')}")
        print(f"- Suggested title: {title_analysis.get('recommended_display_title')}")
        if title_analysis.get("search_intent_keywords"):
            print(
                f"- Intent keywords: {', '.join(title_analysis['search_intent_keywords'][:8])}"
            )

    print("\nTop findings:")
    for finding in report.get("findings", [])[:10]:
        print(
            f"- [{finding['severity']}] {finding['finding']} "
            f"(confidence: {finding['confidence']})"
        )


def main():
    parser = argparse.ArgumentParser(description="GitHub repository SEO metadata and trust audit.")
    parser.add_argument("--repo", help="Repository slug or URL (owner/repo). If omitted, infer from git origin.")
    parser.add_argument("--token", help="GitHub token override. Prefer env vars GITHUB_TOKEN or GH_TOKEN.")
    parser.add_argument("--cwd", default=".", help="Working directory for local file checks (default: .)")
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
        report = build_audit(repo=repo, token=token, cwd=args.cwd, provider=args.provider)
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

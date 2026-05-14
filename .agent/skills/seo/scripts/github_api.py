#!/usr/bin/env python3
"""
Shared GitHub API helpers for repository SEO scripts.
"""

import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError


API_BASE = "https://api.github.com"
_GH_AUTH_CACHE = None


class GitHubAPIError(RuntimeError):
    """Raised when GitHub API requests fail."""

    def __init__(self, message: str, status: int = None, details: dict = None):
        super().__init__(message)
        self.status = status
        self.details = details or {}


def get_token(cli_token: str = None) -> str:
    """Resolve token from CLI override or standard environment variables."""
    if cli_token:
        return cli_token.strip()
    for env_key in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(env_key, "").strip()
        if value:
            return value
    return ""


def gh_available() -> bool:
    """Return True when GitHub CLI is available in PATH."""
    try:
        result = subprocess.run(
            ["gh", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def gh_auth_details(force_refresh: bool = False) -> dict:
    """
    Return GitHub CLI auth status.
    Notes:
    - `gh auth status` may exit 0 even with invalid token, so parse output text.
    """
    global _GH_AUTH_CACHE
    if _GH_AUTH_CACHE is not None and not force_refresh:
        return _GH_AUTH_CACHE

    details = {
        "available": False,
        "authenticated": False,
        "raw": "",
    }
    if not gh_available():
        _GH_AUTH_CACHE = details
        return details

    details["available"] = True
    try:
        result = subprocess.run(
            ["gh", "auth", "status", "-h", "github.com"],
            capture_output=True,
            text=True,
            check=False,
            timeout=12,
        )
        text = (result.stdout or "") + "\n" + (result.stderr or "")
        lower = text.lower()
        authenticated = (
            "logged in to github.com" in lower
            and "failed to log in" not in lower
            and "not logged into" not in lower
            and "token is invalid" not in lower
        )
        details["authenticated"] = authenticated
        details["raw"] = text.strip()
    except Exception as exc:
        details["raw"] = str(exc)

    _GH_AUTH_CACHE = details
    return details


def auth_context(token: str = "") -> dict:
    """Return auth context used by scripts for messaging and fallback decisions."""
    gh = gh_auth_details()
    mode = "token" if bool(token) else ("gh" if gh.get("authenticated") else "unauthenticated")
    return {
        "token_present": bool(token),
        "gh_available": gh.get("available", False),
        "gh_authenticated": gh.get("authenticated", False),
        "mode": mode,
    }


def normalize_repo_slug(value: str) -> str:
    """Normalize a repo identifier to owner/repo format."""
    if not value:
        return ""

    text = value.strip()
    text = re.sub(r"\.git$", "", text)

    if text.startswith("git@github.com:"):
        text = text.split(":", 1)[1]
    elif text.startswith(("https://github.com/", "http://github.com/")):
        parsed = urllib.parse.urlparse(text)
        text = parsed.path.strip("/")

    parts = [p for p in text.split("/") if p]
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return ""


def infer_repo_from_git(cwd: str = None) -> str:
    """Infer owner/repo from local git origin URL."""
    try:
        output = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return ""
    return normalize_repo_slug(output)


def resolve_repo(repo: str = None, cwd: str = None) -> str:
    """Resolve repository slug from explicit value or local git origin."""
    slug = normalize_repo_slug(repo or "")
    if slug:
        return slug
    inferred = infer_repo_from_git(cwd=cwd)
    if inferred:
        return inferred
    raise GitHubAPIError(
        "Could not resolve repository slug. Use --repo owner/repo or run inside a git repo with origin configured."
    )


def parse_repo_slug(repo: str) -> tuple:
    """Return (owner, repo_name)."""
    slug = normalize_repo_slug(repo)
    parts = slug.split("/")
    if len(parts) != 2:
        raise GitHubAPIError(f"Invalid repository slug: {repo}")
    return parts[0], parts[1]


def _headers(token: str = "", accept: str = "", content_type: str = "application/json") -> dict:
    headers = {
        "User-Agent": "SEOSkill-GitHubAPI/1.0",
        "Accept": accept or "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if content_type:
        headers["Content-Type"] = content_type
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _build_url(path: str, params: dict = None) -> str:
    url = path if path.startswith("http") else f"{API_BASE}{path}"
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{query}"
    return url


def rest_json(
    path: str,
    token: str = "",
    method: str = "GET",
    params: dict = None,
    body: dict = None,
    accept: str = "",
    timeout: int = 20,
    retries: int = 2,
    max_sleep_seconds: int = 30,
) -> dict:
    """
    Execute a REST request and return parsed JSON plus metadata.
    Raises GitHubAPIError on terminal failures.
    """
    url = _build_url(path, params=params)
    payload = None
    if body is not None:
        payload = json.dumps(body).encode("utf-8")

    attempt = 0
    while attempt <= retries:
        request = urllib.request.Request(
            url,
            data=payload,
            headers=_headers(token=token, accept=accept),
            method=method.upper(),
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace").strip()
                data = json.loads(raw) if raw else {}
                return {
                    "data": data,
                    "status": getattr(resp, "status", 200),
                    "rate_limit": {
                        "limit": resp.headers.get("X-RateLimit-Limit"),
                        "remaining": resp.headers.get("X-RateLimit-Remaining"),
                        "reset": resp.headers.get("X-RateLimit-Reset"),
                    },
                }
        except HTTPError as exc:
            response_text = exc.read().decode("utf-8", errors="replace").strip()
            try:
                payload_json = json.loads(response_text) if response_text else {}
            except Exception:
                payload_json = {"raw": response_text}

            status = exc.code
            remaining = exc.headers.get("X-RateLimit-Remaining")
            reset = exc.headers.get("X-RateLimit-Reset")

            can_retry = attempt < retries
            if can_retry and status in (429, 500, 502, 503, 504):
                sleep_seconds = min(max_sleep_seconds, 2 ** attempt)
                time.sleep(max(1, sleep_seconds))
                attempt += 1
                continue

            if can_retry and status == 403 and remaining == "0" and reset:
                try:
                    reset_ts = int(reset)
                    wait_for = max(1, min(max_sleep_seconds, reset_ts - int(time.time()) + 1))
                except Exception:
                    wait_for = 2 ** attempt
                time.sleep(wait_for)
                attempt += 1
                continue

            message = payload_json.get("message", f"GitHub API error: HTTP {status}")
            raise GitHubAPIError(message=message, status=status, details=payload_json)
        except URLError as exc:
            if attempt < retries:
                time.sleep(max(1, 2 ** attempt))
                attempt += 1
                continue
            raise GitHubAPIError(f"Network error while calling GitHub API: {exc}") from exc

    raise GitHubAPIError("GitHub API request retries exhausted.")


def graphql_json(query: str, variables: dict = None, token: str = "", timeout: int = 20, retries: int = 2) -> dict:
    """Execute a GraphQL query and return data."""
    result = rest_json(
        "/graphql",
        token=token,
        method="POST",
        body={"query": query, "variables": variables or {}},
        timeout=timeout,
        retries=retries,
    )
    payload = result.get("data", {})
    if payload.get("errors"):
        raise GitHubAPIError("GraphQL query failed", details={"errors": payload.get("errors")})
    return payload.get("data", {})


def gh_api_json(
    path: str,
    method: str = "GET",
    params: dict = None,
    body: dict = None,
    timeout: int = 25,
) -> dict:
    """
    Call GitHub API through `gh api`.
    Returns response payload dictionary.
    """
    if not gh_available():
        raise GitHubAPIError("GitHub CLI (`gh`) is not available.")

    endpoint = path
    if endpoint.startswith(API_BASE):
        endpoint = endpoint.replace(API_BASE, "", 1)
    endpoint = endpoint.lstrip("/")

    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        sep = "&" if "?" in endpoint else "?"
        endpoint = f"{endpoint}{sep}{query}"

    cmd = ["gh", "api", endpoint, "--method", method.upper()]
    input_data = None
    if body is not None:
        cmd += ["--input", "-"]
        input_data = json.dumps(body)

    try:
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitHubAPIError(f"gh api timed out after {timeout}s") from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").strip() or "Unknown gh api failure"
        raise GitHubAPIError(f"gh api error: {stderr}")

    payload = (result.stdout or "").strip()
    if not payload:
        return {}
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise GitHubAPIError("gh api returned non-JSON output.") from exc


def fetch_json(
    path: str,
    token: str = "",
    method: str = "GET",
    params: dict = None,
    body: dict = None,
    accept: str = "",
    timeout: int = 20,
    retries: int = 2,
    provider: str = "auto",
) -> dict:
    """
    Unified API accessor.

    provider modes:
    - api: use direct REST API only.
    - gh: use gh api only.
    - auto: try REST API first when token exists, then fallback to gh api.
    """
    mode = (provider or "auto").lower()
    if mode not in ("auto", "api", "gh"):
        raise GitHubAPIError(f"Invalid provider mode: {provider}")

    if mode == "api":
        return rest_json(
            path=path,
            token=token,
            method=method,
            params=params,
            body=body,
            accept=accept,
            timeout=timeout,
            retries=retries,
        )

    if mode == "gh":
        data = gh_api_json(path=path, method=method, params=params, body=body, timeout=timeout)
        return {"data": data, "status": 200, "rate_limit": {}}

    # auto mode
    ctx = auth_context(token=token)
    errors = []

    def try_rest(use_token: str):
        return rest_json(
            path=path,
            token=use_token,
            method=method,
            params=params,
            body=body,
            accept=accept,
            timeout=timeout,
            retries=retries,
        )

    def try_gh():
        data = gh_api_json(path=path, method=method, params=params, body=body, timeout=timeout)
        return {"data": data, "status": 200, "rate_limit": {}}

    attempts = []
    if ctx["token_present"]:
        attempts.append(("api(token)", lambda: try_rest(token)))
        if ctx["gh_available"]:
            attempts.append(("gh", try_gh))
        attempts.append(("api(public)", lambda: try_rest("")))
    else:
        if ctx["gh_authenticated"]:
            attempts.append(("gh", try_gh))
            attempts.append(("api(public)", lambda: try_rest("")))
        else:
            attempts.append(("api(public)", lambda: try_rest("")))
            if ctx["gh_available"]:
                attempts.append(("gh", try_gh))

    for label, fn in attempts:
        try:
            return fn()
        except GitHubAPIError as exc:
            errors.append(f"{label}: {exc}")
            continue

    detail = " | ".join(errors) if errors else "No provider attempts available."
    raise GitHubAPIError(f"All provider attempts failed. {detail}")

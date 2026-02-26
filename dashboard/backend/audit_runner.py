#!/usr/bin/env python3
"""
audit_runner.py — Orchestrates GEO audit by calling the individual analysis scripts
as subprocesses and combining their results into the canonical geo-audit-data schema.

Each script is invoked via subprocess so that their own dependency sets (requests,
beautifulsoup4, reportlab, etc.) are resolved in the current Python environment
without needing to import them directly into the FastAPI process.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default weight mapping for geo_score computation
# ---------------------------------------------------------------------------
GEO_SCORE_WEIGHTS: dict[str, float] = {
    "ai_citability": 0.25,
    "brand_authority": 0.20,
    "content_eeat": 0.20,
    "technical": 0.15,
    "schema": 0.10,
    "platform_optimization": 0.10,
}


def compute_geo_score(scores: dict[str, Any]) -> float:
    """Compute a weighted GEO score from a sub-score dictionary.

    Args:
        scores: Mapping of score dimension names to numeric values (0-100).
                Keys are expected to match the GEO_SCORE_WEIGHTS mapping; any
                unrecognised keys are silently ignored.

    Returns:
        Weighted average as a float in the range 0–100, rounded to one decimal
        place.  Returns 0.0 if no recognised dimensions are present.
    """
    total_weight: float = 0.0
    weighted_sum: float = 0.0

    for dimension, weight in GEO_SCORE_WEIGHTS.items():
        value = scores.get(dimension)
        if value is not None:
            try:
                weighted_sum += float(value) * weight
                total_weight += weight
            except (TypeError, ValueError):
                logger.warning(
                    "Non-numeric value for dimension '%s': %r — skipping.",
                    dimension,
                    value,
                )

    if total_weight == 0.0:
        return 0.0

    # Normalise to full scale in case some dimensions were missing
    raw = weighted_sum / total_weight
    return round(max(0.0, min(100.0, raw)), 1)


# ---------------------------------------------------------------------------
# Subprocess helpers
# ---------------------------------------------------------------------------

def _run_script(
    python_executable: str,
    script_path: str,
    args: list[str],
    timeout: int = 120,
) -> dict[str, Any]:
    """Run a Python script as a subprocess and parse its stdout as JSON.

    Args:
        python_executable: Path to the Python interpreter to use.
        script_path: Absolute path to the script file.
        args: CLI arguments to pass after the script path.
        timeout: Maximum number of seconds to wait for the subprocess.

    Returns:
        Parsed JSON dict from the script's stdout.

    Raises:
        RuntimeError: If the subprocess returns a non-zero exit code or stdout
                      cannot be decoded as valid JSON.
    """
    cmd = [python_executable, script_path] + args
    logger.info("Running subprocess: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,  # We handle the return code ourselves for richer errors
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Script '{os.path.basename(script_path)}' timed out after {timeout}s"
        ) from exc
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Script not found or Python executable missing: {exc}"
        ) from exc

    if result.returncode != 0:
        stderr_snippet = (result.stderr or "").strip()[:500]
        raise RuntimeError(
            f"Script '{os.path.basename(script_path)}' exited with code "
            f"{result.returncode}. stderr: {stderr_snippet}"
        )

    stdout = (result.stdout or "").strip()
    if not stdout:
        raise RuntimeError(
            f"Script '{os.path.basename(script_path)}' produced no output."
        )

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        snippet = stdout[:300]
        raise RuntimeError(
            f"Script '{os.path.basename(script_path)}' output is not valid JSON: "
            f"{exc}. Output snippet: {snippet}"
        ) from exc


# ---------------------------------------------------------------------------
# Score extraction helpers
# ---------------------------------------------------------------------------

def _extract_citability_scores(citability_data: dict[str, Any]) -> dict[str, Any]:
    """Extract relevant score fields from citability_scorer.py output.

    The citability scorer returns per-block analysis.  We derive aggregate
    scores from the ``average_citability_score`` field and infer proxy values
    for content_eeat and platform_optimization from the grade distribution.
    """
    avg = citability_data.get("average_citability_score", 0)
    grade_dist: dict[str, int] = citability_data.get("grade_distribution", {})
    total_blocks: int = citability_data.get("total_blocks_analyzed", 1) or 1

    # content_eeat — proportion of A/B grade blocks scaled to 100
    eeat_blocks = grade_dist.get("A", 0) + grade_dist.get("B", 0)
    content_eeat = round((eeat_blocks / total_blocks) * 100, 1)

    # platform_optimization — inferred from optimal-length passage proportion
    optimal_count: int = citability_data.get("optimal_length_passages", 0)
    platform_optimization = round(min((optimal_count / total_blocks) * 100, 100), 1)

    return {
        "ai_citability": round(float(avg), 1),
        "content_eeat": content_eeat,
        "platform_optimization": platform_optimization,
    }


def _extract_brand_scores(brand_data: dict[str, Any]) -> dict[str, Any]:
    """Extract a brand_authority score from brand_scanner.py output.

    The brand scanner is primarily qualitative (providing instructions and
    recommendations rather than numeric scores).  We build a heuristic score
    from the confirmed boolean presence flags it does populate.
    """
    platforms: dict[str, Any] = brand_data.get("platforms", {})

    presence_flags = [
        platforms.get("wikipedia", {}).get("has_wikipedia_page", False),
        platforms.get("wikipedia", {}).get("has_wikidata_entry", False),
    ]

    confirmed_count = sum(1 for f in presence_flags if f is True)
    # Start with a baseline of 20 (brand scanner ran successfully), add up to 40
    # for confirmed presences, then add 40 points headroom for manual evaluation.
    brand_authority = min(20 + confirmed_count * 20, 60)

    return {"brand_authority": float(brand_authority)}


def _extract_technical_schema_scores(
    citability_data: dict[str, Any],
) -> dict[str, Any]:
    """Derive proxy technical and schema scores from citability data.

    In the absence of a dedicated technical/schema analyser subprocess the
    audit runner uses structural signals from the citability output as a
    stand-in.  The frontend can supplement these with manual scores later.
    """
    total_blocks: int = citability_data.get("total_blocks_analyzed", 1) or 1
    grade_dist: dict[str, int] = citability_data.get("grade_distribution", {})

    # technical — percentage of non-F blocks indicates parseable, structured content
    non_f_blocks = total_blocks - grade_dist.get("F", 0)
    technical = round(min((non_f_blocks / total_blocks) * 100, 100), 1)

    # schema — use C-or-better as a proxy for structured content readiness
    schema_blocks = (
        grade_dist.get("A", 0)
        + grade_dist.get("B", 0)
        + grade_dist.get("C", 0)
    )
    schema = round(min((schema_blocks / total_blocks) * 100, 100), 1)

    return {"technical": technical, "schema": schema}


def _build_platform_scores(citability_data: dict[str, Any]) -> dict[str, Any]:
    """Build per-AI-platform score estimates from citability data.

    In the absence of live platform polling, we distribute the citability
    score across known AI platforms with small offsets that reflect each
    platform's known content preferences.
    """
    avg: float = float(citability_data.get("average_citability_score", 0))
    return {
        "Google AI Overviews": round(avg * 1.10, 1),   # favours structured text
        "ChatGPT": round(avg * 0.95, 1),
        "Perplexity": round(avg * 0.90, 1),             # citation-heavy platform
        "Bing Copilot": round(avg * 1.00, 1),
    }


def _build_findings(
    citability_data: dict[str, Any],
    brand_data: dict[str, Any],
    scores: dict[str, Any],
) -> list[dict[str, Any]]:
    """Produce a list of audit findings from the combined data."""
    findings: list[dict[str, Any]] = []

    # Low overall citability
    ai_score = scores.get("ai_citability", 0)
    if ai_score < 40:
        findings.append(
            {
                "severity": "critical",
                "title": "Low AI Citability Score",
                "description": (
                    f"Average passage citability is {ai_score}/100. "
                    "Content blocks are unlikely to be selected by AI models as citations. "
                    "Focus on answer-block quality, optimal word counts (134-167 words), "
                    "and statistical density."
                ),
            }
        )
    elif ai_score < 60:
        findings.append(
            {
                "severity": "warning",
                "title": "Moderate AI Citability Score",
                "description": (
                    f"Average passage citability is {ai_score}/100. "
                    "There is meaningful room to improve citation readiness through "
                    "better content structure and richer statistics."
                ),
            }
        )

    # Low-quality passage proportion
    grade_dist: dict[str, int] = citability_data.get("grade_distribution", {})
    total_blocks = citability_data.get("total_blocks_analyzed", 1) or 1
    f_ratio = grade_dist.get("F", 0) / total_blocks
    if f_ratio > 0.5:
        findings.append(
            {
                "severity": "critical",
                "title": "Majority of Content Blocks Grade F",
                "description": (
                    f"{round(f_ratio * 100)}% of analysed content blocks score below 35/100 "
                    "(Grade F).  Rewrite these sections using the BLUF (bottom line up front) "
                    "technique, adding definitions, statistics, and named sources."
                ),
            }
        )

    # Missing Wikipedia presence
    wikipedia = brand_data.get("platforms", {}).get("wikipedia", {})
    if not wikipedia.get("has_wikipedia_page", False):
        findings.append(
            {
                "severity": "warning",
                "title": "No Wikipedia Presence Detected",
                "description": (
                    "The brand does not appear to have a Wikipedia article. "
                    "Wikipedia is a primary training source for most major LLMs. "
                    "Build notability through press coverage to qualify for a Wikipedia entry."
                ),
            }
        )

    # Low optimal-length passages
    optimal = citability_data.get("optimal_length_passages", 0)
    if optimal == 0:
        findings.append(
            {
                "severity": "warning",
                "title": "No Optimal-Length Passages Found",
                "description": (
                    "No content blocks in the 134-167 word range were detected. "
                    "AI models preferentially cite self-contained passages of this length. "
                    "Restructure key sections to hit this target."
                ),
            }
        )

    return findings


def _build_recommendations(
    scores: dict[str, Any],
    brand_data: dict[str, Any],
) -> tuple[list[str], list[str], list[str]]:
    """Return (quick_wins, medium_term, strategic) recommendation lists."""
    quick_wins: list[str] = []
    medium_term: list[str] = []
    strategic: list[str] = []

    if scores.get("ai_citability", 100) < 60:
        quick_wins.append(
            "Rewrite the top 3 content sections using answer-block format: "
            "lead with the direct answer, add a statistic, keep to 134-167 words."
        )

    if scores.get("schema", 100) < 50:
        quick_wins.append(
            "Add JSON-LD structured data (Organization, WebPage, FAQPage) to all key pages."
        )

    if scores.get("technical", 100) < 50:
        quick_wins.append(
            "Review robots.txt to ensure AI crawlers (GPTBot, ClaudeBot, PerplexityBot) "
            "are allowed."
        )

    # Medium term
    wikipedia = brand_data.get("platforms", {}).get("wikipedia", {})
    if not wikipedia.get("has_wikidata_entry", False):
        medium_term.append(
            "Create a Wikidata entry and add sameAs schema markup linking to it."
        )

    medium_term.append(
        "Publish an llms.txt file at the site root to guide AI crawler behaviour."
    )
    medium_term.append(
        "Build a YouTube content library with educational videos — YouTube shows the "
        "highest correlation (0.737) with AI citation frequency."
    )

    # Strategic
    strategic.append(
        "Develop a brand mention programme across Reddit, LinkedIn, and industry forums "
        "to increase third-party citation signals."
    )
    strategic.append(
        "Commission or publish original research/data to generate citable statistics "
        "that AI models will reference."
    )
    strategic.append(
        "Pursue earned media coverage in authoritative publications to establish "
        "Wikipedia notability and strengthen E-E-A-T signals."
    )

    return quick_wins, medium_term, strategic


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_full_audit(
    url: str,
    brand_name: str,
    competitors: list[str],
    scripts_dir: str = "../../scripts",
) -> dict[str, Any]:
    """Run a full GEO audit against *url* and return the combined result dict.

    Orchestrates calls to:
    * ``citability_scorer.py`` — content citability analysis
    * ``brand_scanner.py`` — brand platform presence
    * ``competitor_analyzer.py`` — competitor comparison (if competitors given)

    All subprocesses are called with the same Python interpreter that is
    currently executing this module so that installed packages are available.

    Args:
        url: The target website URL to audit.
        brand_name: Human-readable brand name (used for brand_scanner.py).
        competitors: Optional list of competitor URLs for gap analysis.
        scripts_dir: Path (absolute or relative to this file) to the directory
                     containing the analysis scripts.  Defaults to
                     ``../../scripts`` which resolves correctly when this module
                     lives at ``dashboard/backend/``.

    Returns:
        Dict conforming to the geo-audit-data.json schema.
    """
    python_exe = sys.executable

    # Resolve scripts_dir relative to this file's location if not absolute
    if not os.path.isabs(scripts_dir):
        base = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.normpath(os.path.join(base, scripts_dir))

    logger.info(
        "Starting full GEO audit — url=%s, brand=%s, scripts_dir=%s",
        url,
        brand_name,
        scripts_dir,
    )

    errors: list[str] = []

    # ------------------------------------------------------------------
    # 1. Citability scorer
    # ------------------------------------------------------------------
    citability_data: dict[str, Any] = {}
    citability_path = os.path.join(scripts_dir, "citability_scorer.py")
    try:
        citability_data = _run_script(python_exe, citability_path, [url], timeout=120)
        logger.info("citability_scorer completed successfully.")
    except RuntimeError as exc:
        msg = f"citability_scorer failed: {exc}"
        logger.error(msg)
        errors.append(msg)
        citability_data = {
            "url": url,
            "total_blocks_analyzed": 0,
            "average_citability_score": 0,
            "optimal_length_passages": 0,
            "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
            "top_5_citable": [],
            "bottom_5_citable": [],
            "all_blocks": [],
            "_error": str(exc),
        }

    # ------------------------------------------------------------------
    # 2. Brand scanner
    # ------------------------------------------------------------------
    brand_data: dict[str, Any] = {}
    brand_path = os.path.join(scripts_dir, "brand_scanner.py")
    try:
        brand_args = [brand_name]
        # Extract domain from URL for the optional second argument
        from urllib.parse import urlparse as _urlparse
        parsed = _urlparse(url)
        domain = parsed.netloc or ""
        if domain:
            brand_args.append(domain)
        brand_data = _run_script(python_exe, brand_path, brand_args, timeout=60)
        logger.info("brand_scanner completed successfully.")
    except RuntimeError as exc:
        msg = f"brand_scanner failed: {exc}"
        logger.error(msg)
        errors.append(msg)
        brand_data = {
            "brand_name": brand_name,
            "platforms": {},
            "_error": str(exc),
        }

    # ------------------------------------------------------------------
    # 3. Competitor analyzer (optional)
    # ------------------------------------------------------------------
    competitor_data: dict[str, Any] | None = None
    if competitors:
        comp_path = os.path.join(scripts_dir, "competitor_analyzer.py")
        comp_args = [url] + competitors[:5]  # cap at 5 as per script constant
        try:
            competitor_data = _run_script(python_exe, comp_path, comp_args, timeout=300)
            logger.info("competitor_analyzer completed successfully.")
        except RuntimeError as exc:
            msg = f"competitor_analyzer failed: {exc}"
            logger.error(msg)
            errors.append(msg)
            competitor_data = {"_error": str(exc)}

    # ------------------------------------------------------------------
    # 4. Aggregate scores
    # ------------------------------------------------------------------
    scores: dict[str, Any] = {}

    citability_scores = _extract_citability_scores(citability_data)
    scores.update(citability_scores)

    brand_scores = _extract_brand_scores(brand_data)
    scores.update(brand_scores)

    tech_schema_scores = _extract_technical_schema_scores(citability_data)
    scores.update(tech_schema_scores)

    geo_score = compute_geo_score(scores)
    platform_scores = _build_platform_scores(citability_data)

    # ------------------------------------------------------------------
    # 5. Findings and recommendations
    # ------------------------------------------------------------------
    findings = _build_findings(citability_data, brand_data, scores)
    quick_wins, medium_term, strategic = _build_recommendations(scores, brand_data)

    # ------------------------------------------------------------------
    # 6. Build canonical output dict
    # ------------------------------------------------------------------
    result: dict[str, Any] = {
        "url": url,
        "brand_name": brand_name,
        "date": date.today().isoformat(),
        "geo_score": geo_score,
        "scores": scores,
        "platforms": platform_scores,
        "executive_summary": (
            f"{brand_name} achieved a GEO score of {geo_score}/100. "
            f"AI citability is {scores.get('ai_citability', 0)}/100 with "
            f"brand authority at {scores.get('brand_authority', 0)}/100. "
            f"{len(findings)} findings identified across content, brand, "
            "and technical dimensions."
        ),
        "findings": findings,
        "quick_wins": quick_wins,
        "medium_term": medium_term,
        "strategic": strategic,
        "crawler_access": {},  # Populated by future technical scanner
        # Raw data from sub-scripts for downstream use / debugging
        "_raw": {
            "citability": citability_data,
            "brand": brand_data,
            "competitors": competitor_data,
        },
    }

    if errors:
        result["_errors"] = errors
        logger.warning("Audit completed with %d error(s): %s", len(errors), errors)
    else:
        logger.info("Audit completed successfully for %s — score: %s", url, geo_score)

    return result

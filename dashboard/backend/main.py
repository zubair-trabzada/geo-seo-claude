#!/usr/bin/env python3
"""
main.py — FastAPI application for the GEO Dashboard backend.

Provides endpoints for:
* Running on-demand GEO audits (async, via BackgroundTasks)
* Polling audit job status
* Triggering scheduled audits for a specific client
* Generating PDF reports from audit data

Start the server with:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import uuid
from datetime import datetime
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from audit_runner import run_full_audit

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv()

SCRIPTS_DIR: str = os.getenv(
    "GEO_SCRIPTS_DIR",
    os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
    ),
)

FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="GEO Dashboard API",
    description=(
        "Backend service for the GEO Dashboard platform. "
        "Runs citability, brand, and competitor analysis pipelines "
        "and exposes the results to the Next.js frontend."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory job store
# Each entry: {job_id: str, status: str, result: dict|None, error: str|None,
#              created_at: str, completed_at: str|None}
# ---------------------------------------------------------------------------
_jobs: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class AuditRunRequest(BaseModel):
    """Request body for POST /audit/run."""

    url: str = Field(..., description="Target website URL to audit.")
    brand_name: str = Field(..., description="Human-readable brand/company name.")
    competitors: list[str] = Field(
        default_factory=list,
        description="Optional list of competitor URLs for gap analysis (max 5).",
    )


class AuditRunResponse(BaseModel):
    """Immediate response returned when an audit job is accepted."""

    job_id: str
    status: str
    message: str


class AuditStatusResponse(BaseModel):
    """Response for GET /audit/status/{job_id}."""

    job_id: str
    status: str  # "pending" | "running" | "complete" | "error"
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str | None = None
    completed_at: str | None = None


class SchedulerTriggerResponse(BaseModel):
    """Response for POST /scheduler/trigger/{client_id}."""

    client_id: str
    triggered: bool
    message: str


class PDFGenerateRequest(BaseModel):
    """Request body for POST /pdf/generate."""

    audit_data: dict[str, Any] = Field(
        ..., description="Full audit data dict matching the geo-audit-data schema."
    )
    output_path: str = Field(
        ...,
        description="Filesystem path where the generated PDF should be saved.",
    )


class PDFGenerateResponse(BaseModel):
    """Response for POST /pdf/generate."""

    success: bool
    output_path: str
    message: str


# ---------------------------------------------------------------------------
# Background task helpers
# ---------------------------------------------------------------------------

def _execute_audit(
    job_id: str,
    url: str,
    brand_name: str,
    competitors: list[str],
) -> None:
    """Background task that runs the full audit and updates the job store.

    This function is intentionally synchronous because the underlying
    ``run_full_audit`` call blocks on subprocess I/O.  FastAPI's
    ``BackgroundTasks`` executes it in a thread pool, keeping the event loop
    free for other requests.

    Args:
        job_id: Unique job identifier used as the key in ``_jobs``.
        url: Target URL passed to ``run_full_audit``.
        brand_name: Brand name passed to ``run_full_audit``.
        competitors: Competitor URLs passed to ``run_full_audit``.
    """
    _jobs[job_id]["status"] = "running"
    logger.info("Audit job %s started — url=%s", job_id, url)

    try:
        result = run_full_audit(
            url=url,
            brand_name=brand_name,
            competitors=competitors,
            scripts_dir=SCRIPTS_DIR,
        )
        _jobs[job_id].update(
            {
                "status": "complete",
                "result": result,
                "error": None,
                "completed_at": datetime.utcnow().isoformat() + "Z",
            }
        )
        logger.info(
            "Audit job %s completed — geo_score=%s",
            job_id,
            result.get("geo_score"),
        )
    except Exception as exc:  # pylint: disable=broad-except
        error_msg = f"{type(exc).__name__}: {exc}"
        _jobs[job_id].update(
            {
                "status": "error",
                "result": None,
                "error": error_msg,
                "completed_at": datetime.utcnow().isoformat() + "Z",
            }
        )
        logger.exception("Audit job %s failed: %s", job_id, error_msg)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", summary="Health check")
async def health_check() -> dict[str, str]:
    """Return a simple health check payload.

    Used by load balancers, Docker health checks, and the frontend to verify
    the API is reachable before making substantive requests.
    """
    return {"status": "ok", "service": "GEO Dashboard API"}


@app.post(
    "/audit/run",
    response_model=AuditRunResponse,
    status_code=202,
    summary="Start a GEO audit",
)
async def start_audit(
    body: AuditRunRequest,
    background_tasks: BackgroundTasks,
) -> AuditRunResponse:
    """Accept an audit request and start it in the background.

    Returns immediately with a ``job_id`` that the client can poll via
    ``GET /audit/status/{job_id}``.

    The audit pipeline runs:
    1. ``citability_scorer.py`` — per-passage AI citability analysis
    2. ``brand_scanner.py`` — brand presence across AI-indexed platforms
    3. ``competitor_analyzer.py`` (if competitors provided) — gap analysis
    """
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "result": None,
        "error": None,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "completed_at": None,
        "url": body.url,
        "brand_name": body.brand_name,
    }

    background_tasks.add_task(
        _execute_audit,
        job_id=job_id,
        url=body.url,
        brand_name=body.brand_name,
        competitors=body.competitors,
    )

    logger.info(
        "Audit job %s created and queued — url=%s brand=%s competitors=%d",
        job_id,
        body.url,
        body.brand_name,
        len(body.competitors),
    )

    return AuditRunResponse(
        job_id=job_id,
        status="pending",
        message="Audit started. Poll /audit/status/{job_id} for results.",
    )


@app.get(
    "/audit/status/{job_id}",
    response_model=AuditStatusResponse,
    summary="Poll audit job status",
)
async def get_audit_status(job_id: str) -> AuditStatusResponse:
    """Return the current status and result (if complete) for an audit job.

    Status values:
    * ``pending`` — job is queued but not yet started
    * ``running`` — subprocesses are executing
    * ``complete`` — all scripts finished; ``result`` contains the audit data
    * ``error`` — one or more scripts failed fatally; ``error`` contains details
    """
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found.",
        )

    return AuditStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        result=job.get("result"),
        error=job.get("error"),
        created_at=job.get("created_at"),
        completed_at=job.get("completed_at"),
    )


@app.post(
    "/scheduler/trigger/{client_id}",
    response_model=SchedulerTriggerResponse,
    summary="Manually trigger a scheduled audit for a client",
)
async def trigger_scheduled_audit(client_id: str) -> SchedulerTriggerResponse:
    """Manually kick off a scheduled audit for the given *client_id*.

    Looks up the client record in the SQLite database (via the scheduler
    module) and POSTs to ``/audit/run`` on behalf of that client.

    The Next.js frontend can call this endpoint to provide a "Run Now" button
    in the client management UI without needing direct access to the scheduler
    process.
    """
    # Import here to avoid a hard dependency at module load time; the scheduler
    # module requires sqlite3 and the DB file to be present.
    try:
        from scheduler import trigger_now  # noqa: PLC0415
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Scheduler module could not be imported: {exc}",
        ) from exc

    try:
        triggered = trigger_now(client_id=client_id)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to trigger audit for client '%s': %s", client_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger audit: {exc}",
        ) from exc

    if triggered:
        return SchedulerTriggerResponse(
            client_id=client_id,
            triggered=True,
            message=f"Audit triggered successfully for client '{client_id}'.",
        )

    raise HTTPException(
        status_code=404,
        detail=f"Client '{client_id}' not found or is inactive.",
    )


@app.post(
    "/pdf/generate",
    response_model=PDFGenerateResponse,
    summary="Generate a PDF report from audit data",
)
async def generate_pdf(body: PDFGenerateRequest) -> PDFGenerateResponse:
    """Write *audit_data* to a temporary JSON file and invoke
    ``generate_pdf_report.py`` as a subprocess to produce the PDF.

    The generated PDF is written to ``output_path``.  The caller is
    responsible for ensuring the parent directory exists and is writable.
    """
    import json as _json
    import tempfile

    # Write audit_data to a temp JSON file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        _json.dump(body.audit_data, tmp, default=str)
        tmp_path = tmp.name

    script_path = os.path.join(SCRIPTS_DIR, "generate_pdf_report.py")

    try:
        result = subprocess.run(
            [sys.executable, script_path, tmp_path, body.output_path],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        os.unlink(tmp_path)
        raise HTTPException(
            status_code=504,
            detail="PDF generation timed out after 120 seconds.",
        ) from exc
    except FileNotFoundError as exc:
        os.unlink(tmp_path)
        raise HTTPException(
            status_code=500,
            detail=f"generate_pdf_report.py not found at {script_path}: {exc}",
        ) from exc
    finally:
        # Always clean up the temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()[:500]
        logger.error("PDF generation failed (rc=%d): %s", result.returncode, stderr)
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {stderr}",
        )

    logger.info("PDF generated successfully at %s", body.output_path)
    return PDFGenerateResponse(
        success=True,
        output_path=body.output_path,
        message=f"PDF report saved to '{body.output_path}'.",
    )

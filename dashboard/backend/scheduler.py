#!/usr/bin/env python3
"""
scheduler.py — Weekly GEO audit scheduler for the dashboard platform.

Reads client records from the SQLite database, POSTs audit jobs to the
FastAPI backend, and writes alert / milestone records back to the DB.

Usage (run directly to start the weekly loop):
    python scheduler.py

Or import and call individual functions from other modules:
    from scheduler import trigger_now, run_scheduled_audits
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from typing import Any

import httpx
import schedule

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Database path — two directories above the backend folder by default
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH: str = os.getenv(
    "GEO_DB_PATH",
    os.path.normpath(os.path.join(_BACKEND_DIR, "..", "..", "dashboard", "geo_dashboard.db")),
)

API_BASE_URL: str = os.getenv("GEO_API_BASE_URL", "http://localhost:8000")

# How long (seconds) to wait for the audit to complete when polling
POLL_TIMEOUT_SECONDS: int = int(os.getenv("GEO_POLL_TIMEOUT", "600"))
POLL_INTERVAL_SECONDS: int = int(os.getenv("GEO_POLL_INTERVAL", "10"))

# Score drop threshold that triggers an alert
ALERT_SCORE_DROP_THRESHOLD: float = 5.0


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _get_connection() -> sqlite3.Connection:
    """Open and return a sqlite3 connection to the dashboard database.

    The database file is created automatically if it does not yet exist.
    Row factory is set to ``sqlite3.Row`` so callers get dict-like rows.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create the minimum required tables if they do not already exist."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id          TEXT    PRIMARY KEY,
            name        TEXT    NOT NULL,
            url         TEXT    NOT NULL,
            brand_name  TEXT    NOT NULL,
            competitors TEXT    DEFAULT '[]',   -- JSON array of URLs
            active      INTEGER DEFAULT 1,       -- 1 = active, 0 = paused
            last_audit  TEXT,                    -- ISO-8601 timestamp
            last_score  REAL
        );

        CREATE TABLE IF NOT EXISTS audits (
            id          TEXT    PRIMARY KEY,
            client_id   TEXT    NOT NULL REFERENCES clients(id),
            job_id      TEXT,
            status      TEXT    DEFAULT 'pending',
            geo_score   REAL,
            raw_data    TEXT,   -- JSON
            created_at  TEXT    NOT NULL,
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id   TEXT    NOT NULL REFERENCES clients(id),
            type        TEXT    NOT NULL,   -- 'score_drop' | 'milestone'
            message     TEXT    NOT NULL,
            details     TEXT,              -- JSON
            created_at  TEXT    NOT NULL,
            acknowledged INTEGER DEFAULT 0
        );
        """
    )
    conn.commit()


def _get_active_clients(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return all active client rows from the database."""
    cursor = conn.execute("SELECT * FROM clients WHERE active = 1")
    return cursor.fetchall()


def _insert_alert(
    conn: sqlite3.Connection,
    client_id: str,
    alert_type: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Insert an alert record into the alerts table."""
    conn.execute(
        """
        INSERT INTO alerts (client_id, type, message, details, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            client_id,
            alert_type,
            message,
            json.dumps(details or {}),
            datetime.utcnow().isoformat() + "Z",
        ),
    )
    conn.commit()
    logger.info("Alert inserted — client=%s type=%s: %s", client_id, alert_type, message)


def _update_client_last_audit(
    conn: sqlite3.Connection,
    client_id: str,
    geo_score: float,
) -> None:
    """Update a client's last_audit timestamp and last_score."""
    conn.execute(
        """
        UPDATE clients
        SET last_audit = ?, last_score = ?
        WHERE id = ?
        """,
        (datetime.utcnow().isoformat() + "Z", geo_score, client_id),
    )
    conn.commit()


def _save_audit_result(
    conn: sqlite3.Connection,
    client_id: str,
    job_id: str,
    geo_score: float,
    raw_data: dict[str, Any],
) -> None:
    """Persist a completed audit result to the audits table."""
    audit_id = f"{client_id}_{job_id[:8]}"
    conn.execute(
        """
        INSERT OR REPLACE INTO audits
            (id, client_id, job_id, status, geo_score, raw_data, created_at, completed_at)
        VALUES (?, ?, ?, 'complete', ?, ?, ?, ?)
        """,
        (
            audit_id,
            client_id,
            job_id,
            geo_score,
            json.dumps(raw_data, default=str),
            raw_data.get("date", datetime.utcnow().isoformat() + "Z"),
            datetime.utcnow().isoformat() + "Z",
        ),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Alert and milestone detection
# ---------------------------------------------------------------------------

def check_for_alerts(
    client_id: str,
    new_score: float,
    prev_score: float,
) -> None:
    """Insert a score-drop alert if the GEO score has fallen by more than the threshold.

    Args:
        client_id: The client whose scores are being compared.
        new_score: The GEO score from the latest completed audit.
        prev_score: The GEO score from the most recent previous audit.
    """
    drop = prev_score - new_score
    if drop > ALERT_SCORE_DROP_THRESHOLD:
        message = (
            f"GEO score dropped {drop:.1f} points "
            f"(from {prev_score:.1f} to {new_score:.1f})."
        )
        details = {
            "previous_score": prev_score,
            "new_score": new_score,
            "drop": drop,
            "threshold": ALERT_SCORE_DROP_THRESHOLD,
        }
        try:
            conn = _get_connection()
            _ensure_schema(conn)
            _insert_alert(conn, client_id, "score_drop", message, details)
        except sqlite3.Error as exc:
            logger.error(
                "Failed to insert score-drop alert for client '%s': %s",
                client_id,
                exc,
            )
        finally:
            conn.close()
    else:
        logger.debug(
            "No score-drop alert needed for client '%s' (prev=%.1f, new=%.1f).",
            client_id,
            prev_score,
            new_score,
        )


def check_for_milestones(
    client_id: str,
    old_raw_data: dict[str, Any],
    new_raw_data: dict[str, Any],
) -> None:
    """Detect positive milestones between two audit snapshots and record alerts.

    Checks for:
    * New AI platform citations (platforms dict entries that are non-zero
      in new data but were zero/absent in old data)
    * Overall GEO score improvements >= 5 points
    * Individual sub-score improvements >= 10 points

    Args:
        client_id: The client whose data is being compared.
        old_raw_data: Audit result dict from the previous run.
        new_raw_data: Audit result dict from the latest run.
    """
    milestones: list[dict[str, Any]] = []

    # --- GEO score improvement ---
    old_geo = float(old_raw_data.get("geo_score", 0))
    new_geo = float(new_raw_data.get("geo_score", 0))
    if new_geo - old_geo >= 5.0:
        milestones.append(
            {
                "type": "score_improvement",
                "message": (
                    f"GEO score improved by {new_geo - old_geo:.1f} points "
                    f"({old_geo:.1f} → {new_geo:.1f})."
                ),
                "details": {"old_score": old_geo, "new_score": new_geo},
            }
        )

    # --- Sub-score improvements ---
    old_scores: dict[str, Any] = old_raw_data.get("scores", {})
    new_scores: dict[str, Any] = new_raw_data.get("scores", {})
    for dimension, new_val in new_scores.items():
        old_val = old_scores.get(dimension, 0)
        try:
            improvement = float(new_val) - float(old_val)
        except (TypeError, ValueError):
            continue
        if improvement >= 10.0:
            milestones.append(
                {
                    "type": "subscore_improvement",
                    "message": (
                        f"{dimension.replace('_', ' ').title()} improved by "
                        f"{improvement:.1f} points ({float(old_val):.1f} → {float(new_val):.1f})."
                    ),
                    "details": {
                        "dimension": dimension,
                        "old": float(old_val),
                        "new": float(new_val),
                    },
                }
            )

    # --- New platform citations ---
    old_platforms: dict[str, Any] = old_raw_data.get("platforms", {})
    new_platforms: dict[str, Any] = new_raw_data.get("platforms", {})
    for platform, new_val in new_platforms.items():
        old_val = float(old_platforms.get(platform, 0))
        try:
            nv = float(new_val)
        except (TypeError, ValueError):
            continue
        if old_val == 0 and nv > 0:
            milestones.append(
                {
                    "type": "new_platform_citation",
                    "message": (
                        f"New citation signal detected on {platform} "
                        f"(score: {nv:.1f})."
                    ),
                    "details": {"platform": platform, "score": nv},
                }
            )

    if not milestones:
        logger.debug("No milestones detected for client '%s'.", client_id)
        return

    # Persist each milestone as an alert record
    try:
        conn = _get_connection()
        _ensure_schema(conn)
        for milestone in milestones:
            _insert_alert(
                conn,
                client_id,
                "milestone",
                milestone["message"],
                milestone.get("details"),
            )
    except sqlite3.Error as exc:
        logger.error(
            "Failed to persist milestone alerts for client '%s': %s",
            client_id,
            exc,
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# API interaction helpers
# ---------------------------------------------------------------------------

def _post_audit_run(url: str, brand_name: str, competitors: list[str]) -> str:
    """POST to /audit/run and return the job_id.

    Args:
        url: Target URL for the audit.
        brand_name: Brand name to pass to the API.
        competitors: Competitor URLs.

    Returns:
        job_id string from the API response.

    Raises:
        RuntimeError: If the API call fails or returns an unexpected response.
    """
    endpoint = f"{API_BASE_URL}/audit/run"
    payload = {"url": url, "brand_name": brand_name, "competitors": competitors}

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(endpoint, json=payload)
        resp.raise_for_status()
        data = resp.json()
        job_id: str = data["job_id"]
        logger.info("Audit job accepted — job_id=%s url=%s", job_id, url)
        return job_id
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Failed to POST to {endpoint}: {exc}") from exc
    except (KeyError, ValueError) as exc:
        raise RuntimeError(f"Unexpected API response: {exc}") from exc


def _poll_job_until_complete(job_id: str) -> dict[str, Any]:
    """Poll GET /audit/status/{job_id} until the job is complete or errors out.

    Args:
        job_id: The job identifier returned by /audit/run.

    Returns:
        The ``result`` dict from a completed job.

    Raises:
        RuntimeError: If the job errors, or if the poll timeout is exceeded.
    """
    endpoint = f"{API_BASE_URL}/audit/status/{job_id}"
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(endpoint)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            logger.warning("Poll request failed for job %s: %s — retrying.", job_id, exc)
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        status = data.get("status")
        logger.debug("Job %s status: %s", job_id, status)

        if status == "complete":
            return data.get("result") or {}
        if status == "error":
            error_msg = data.get("error", "Unknown error")
            raise RuntimeError(f"Audit job {job_id} failed: {error_msg}")

        time.sleep(POLL_INTERVAL_SECONDS)

    raise RuntimeError(
        f"Audit job {job_id} did not complete within {POLL_TIMEOUT_SECONDS}s."
    )


# ---------------------------------------------------------------------------
# Core scheduled audit logic
# ---------------------------------------------------------------------------

def run_scheduled_audits() -> None:
    """Iterate all active clients and run a GEO audit for each.

    For each active client:
    1. POST to /audit/run to create a background job.
    2. Poll /audit/status/{job_id} until the job completes.
    3. Persist the result to the DB.
    4. Check for alerts (score drops) and milestones.
    5. Update the client's last_audit and last_score fields.

    Errors for individual clients are logged but do not abort the loop.
    """
    logger.info("Starting scheduled audit run — %s", datetime.utcnow().isoformat())

    try:
        conn = _get_connection()
        _ensure_schema(conn)
        clients = _get_active_clients(conn)
    except sqlite3.Error as exc:
        logger.error("Cannot read clients from database: %s", exc)
        return
    finally:
        conn.close()

    if not clients:
        logger.info("No active clients found — nothing to do.")
        return

    logger.info("Found %d active client(s).", len(clients))

    for client in clients:
        client_id = client["id"]
        url = client["url"]
        brand_name = client["brand_name"]
        prev_score: float = float(client["last_score"] or 0)

        try:
            competitors_raw = client["competitors"] or "[]"
            competitors: list[str] = json.loads(competitors_raw)
        except (json.JSONDecodeError, TypeError):
            competitors = []

        logger.info(
            "Running audit for client '%s' (%s) — prev_score=%.1f",
            client_id,
            url,
            prev_score,
        )

        try:
            job_id = _post_audit_run(url, brand_name, competitors)
            result = _poll_job_until_complete(job_id)
        except RuntimeError as exc:
            logger.error("Audit failed for client '%s': %s", client_id, exc)
            continue

        new_score: float = float(result.get("geo_score", 0))

        # Persist to DB
        try:
            conn = _get_connection()
            _ensure_schema(conn)
            _save_audit_result(conn, client_id, job_id, new_score, result)
            _update_client_last_audit(conn, client_id, new_score)
        except sqlite3.Error as exc:
            logger.error(
                "Failed to save audit result for client '%s': %s",
                client_id,
                exc,
            )
        finally:
            conn.close()

        # Check for regressions and improvements
        if prev_score > 0:
            check_for_alerts(client_id, new_score, prev_score)

        # Retrieve previous raw data for milestone comparison
        try:
            conn = _get_connection()
            row = conn.execute(
                """
                SELECT raw_data FROM audits
                WHERE client_id = ?
                ORDER BY completed_at DESC
                LIMIT 1 OFFSET 1
                """,
                (client_id,),
            ).fetchone()
        except sqlite3.Error:
            row = None
        finally:
            conn.close()

        if row and row["raw_data"]:
            try:
                old_raw = json.loads(row["raw_data"])
                check_for_milestones(client_id, old_raw, result)
            except (json.JSONDecodeError, TypeError) as exc:
                logger.warning(
                    "Could not parse previous audit data for milestones — client '%s': %s",
                    client_id,
                    exc,
                )

        logger.info(
            "Audit completed for client '%s' — new_score=%.1f",
            client_id,
            new_score,
        )

    logger.info("Scheduled audit run finished.")


# ---------------------------------------------------------------------------
# Manual trigger
# ---------------------------------------------------------------------------

def trigger_now(client_id: str | None = None) -> bool:
    """Manually trigger an audit for a specific client or all active clients.

    This function is intended to be called from the FastAPI
    ``POST /scheduler/trigger/{client_id}`` endpoint or from the command line.

    Args:
        client_id: If provided, only audit this specific client.
                   If ``None``, audit all active clients (equivalent to
                   ``run_scheduled_audits``).

    Returns:
        ``True`` if the audit was triggered successfully, ``False`` if the
        specified client was not found or is inactive.
    """
    if client_id is None:
        run_scheduled_audits()
        return True

    # Look up the specific client
    try:
        conn = _get_connection()
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT * FROM clients WHERE id = ? AND active = 1",
            (client_id,),
        ).fetchone()
    except sqlite3.Error as exc:
        logger.error("DB error looking up client '%s': %s", client_id, exc)
        raise
    finally:
        conn.close()

    if row is None:
        logger.warning(
            "trigger_now: client '%s' not found or inactive.", client_id
        )
        return False

    url = row["url"]
    brand_name = row["brand_name"]
    prev_score: float = float(row["last_score"] or 0)

    try:
        competitors_raw = row["competitors"] or "[]"
        competitors: list[str] = json.loads(competitors_raw)
    except (json.JSONDecodeError, TypeError):
        competitors = []

    logger.info(
        "Manual trigger for client '%s' (%s).", client_id, url
    )

    try:
        job_id = _post_audit_run(url, brand_name, competitors)
        result = _poll_job_until_complete(job_id)
    except RuntimeError as exc:
        logger.error(
            "Manual trigger audit failed for client '%s': %s", client_id, exc
        )
        raise

    new_score: float = float(result.get("geo_score", 0))

    try:
        conn = _get_connection()
        _ensure_schema(conn)
        _save_audit_result(conn, client_id, job_id, new_score, result)
        _update_client_last_audit(conn, client_id, new_score)
    except sqlite3.Error as exc:
        logger.error(
            "Failed to save manual trigger result for client '%s': %s",
            client_id,
            exc,
        )
    finally:
        conn.close()

    if prev_score > 0:
        check_for_alerts(client_id, new_score, prev_score)

    logger.info(
        "Manual trigger complete for client '%s' — score=%.1f",
        client_id,
        new_score,
    )
    return True


# ---------------------------------------------------------------------------
# Main — weekly schedule loop
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("GEO Dashboard Scheduler starting up.")
    logger.info("Database: %s", DB_PATH)
    logger.info("API base URL: %s", API_BASE_URL)

    # Ensure the DB schema exists before scheduling
    try:
        _conn = _get_connection()
        _ensure_schema(_conn)
        _conn.close()
        logger.info("Database schema verified.")
    except sqlite3.Error as _exc:
        logger.critical("Cannot initialise database: %s", _exc)
        raise SystemExit(1) from _exc

    # Run once immediately on startup so operators get an initial result
    run_scheduled_audits()

    # Schedule weekly on Monday at 02:00 UTC
    schedule.every().monday.at("02:00").do(run_scheduled_audits)
    logger.info("Scheduler running — next run: every Monday at 02:00 UTC.")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute — low overhead

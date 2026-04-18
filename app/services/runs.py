"""Run logging service.

Every tool invocation funnels through ``log_run()`` so we get a consistent
record of what was called, with what input, how long it took, and what came
back. Per ADR 005 the call is explicit — each router calls this directly.

Design notes:
- Logging happens *after* the tool runs, so we capture duration and final
  status in one go.
- Input is hashed with SHA-256 so we can deduplicate identical inputs (and
  match repeat runs) without relying on the full JSON payload.
- Failures are still logged: status='error', error_message populated. An
  invisible failure is the worst kind.
- The function is best-effort: if the DB write fails, we log the problem but
  don't break the user-facing response. The app should remain usable even
  if persistence is down.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Run, User

logger = logging.getLogger(__name__)


# Conservative upper bound on the size of payloads stored as JSON.
# Protects the DB from accidentally huge inputs (e.g. a 10 MB pasted PDF).
_MAX_PAYLOAD_CHARS = 50_000


def log_run(
    db: Session,
    *,
    tool_name: str,
    input_payload: dict[str, Any] | None,
    output_payload: dict[str, Any] | None,
    duration_ms: int,
    status: str = "success",
    error_message: str | None = None,
    user_id: int | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> Run | None:
    """Persist a record of a tool invocation.

    Returns the created Run (or None if the insert failed). Does not raise —
    DB errors are logged and swallowed so the caller's response path stays
    intact.
    """
    try:
        run = Run(
            user_id=user_id or _default_user_id(db),
            tool_name=tool_name,
            input_hash=_hash_payload(input_payload),
            input_json=_truncate_payload(input_payload),
            output_json=_truncate_payload(output_payload),
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            status=status,
            error_message=(error_message[:2000] if error_message else None),
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    except Exception as exc:
        # Don't let logging failures break the user-facing response.
        logger.warning("Failed to log run: %s", exc, exc_info=True)
        db.rollback()
        return None


# ── Internal helpers ─────────────────────────────────────────────────────────


def _default_user_id(db: Session) -> int | None:
    """Return the ID of the built-in guest user, or None if absent.

    Authenticated users will be resolved from request context once Fase 2
    introduces auth. Until then every run is attributed to ``guest``.
    """
    guest = db.scalar(select(User).where(User.role == "guest").limit(1))
    return guest.id if guest else None


def _hash_payload(payload: dict[str, Any] | None) -> str:
    """SHA-256 of a canonical JSON serialisation of the payload.

    Canonical = keys sorted + compact separators, so the same logical input
    always hashes to the same value regardless of dict insertion order.
    """
    if payload is None:
        return ""
    try:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
    except (TypeError, ValueError):
        canonical = repr(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _truncate_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return the payload unchanged, or a small marker if it's too large.

    We prefer a marker over silently storing half a payload — it's easier to
    notice that we lost data than to debug subtly corrupted records.
    """
    if payload is None:
        return None
    try:
        serialised = json.dumps(payload, default=str)
    except (TypeError, ValueError):
        return {"_error": "payload not JSON-serialisable"}

    if len(serialised) <= _MAX_PAYLOAD_CHARS:
        return payload
    return {
        "_truncated": True,
        "_original_size_bytes": len(serialised),
        "_preview": serialised[:500],
    }

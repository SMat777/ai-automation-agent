"""Context-manager that wraps an endpoint's work and logs a Run row.

Keeps the logging boilerplate (timer + try/except/finally + log_run call)
in one place so routers stay short. Example::

    @router.post("/analyze")
    def analyze(req, db: Session = Depends(get_db)) -> ToolResponse:
        with track_run(db, tool_name="analyze", input_payload=req.model_dump()) as tr:
            result = handle_analyze(req.text, focus=req.focus)
            tr.output = result
        return ToolResponse(success=True, data=result)

Per ADR 005 the logging is still explicit (each endpoint opens the context
manager by name) — we just move the repetitive scaffolding out of the way.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.services.runs import log_run

logger = logging.getLogger(__name__)


@dataclass
class _Tracker:
    """Mutable handle the with-block uses to communicate back to the wrapper."""

    output: dict[str, Any] | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    extra_input: dict[str, Any] = field(default_factory=dict)


@contextmanager
def track_run(
    db: Session,
    *,
    tool_name: str,
    input_payload: dict[str, Any] | None,
    user_id: int | None = None,
):
    """Yield a _Tracker; log a Run when the block exits (success or error).

    If the block raises, the run is logged with status='error' and the
    exception's string representation is used as the error message. The
    exception is then re-raised so FastAPI's error handling takes over —
    logging does not swallow errors.
    """
    start = time.perf_counter()
    tracker = _Tracker()

    try:
        yield tracker
        status = "success"
        error_message: str | None = None
    except Exception as exc:
        status = "error"
        error_message = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)
        payload = {**(input_payload or {}), **tracker.extra_input} or None
        log_run(
            db,
            tool_name=tool_name,
            input_payload=payload,
            output_payload=tracker.output,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            user_id=user_id,
            input_tokens=tracker.input_tokens,
            output_tokens=tracker.output_tokens,
        )

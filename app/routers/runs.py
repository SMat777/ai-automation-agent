"""Run history endpoint.

Backs the UI's run-history sidebar. Supports pagination and simple filtering;
more sophisticated search (full-text on payloads, date ranges, tool combos)
can be added when the UI needs it — not before.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Run
from app.models._helpers import utcnow

router = APIRouter(tags=["runs"])

StatusFilter = Literal["all", "success", "error"]
SinceFilter = Literal["all", "today", "week", "month"]

# Caps on pagination so a malicious or buggy client cannot ask for a million
# rows at once. The UI asks for 20-50 at a time; 200 is generous.
_MAX_LIMIT = 200
_DEFAULT_LIMIT = 50


class RunSummary(BaseModel):
    """Lightweight projection of Run — enough for the sidebar list."""

    id: int
    tool_name: str
    status: str
    duration_ms: int
    created_at: datetime
    error_message: str | None = None


class RunDetail(RunSummary):
    """Full projection — returned when the UI expands a run to replay it."""

    input_json: dict[str, Any] | None = None
    output_json: dict[str, Any] | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class RunsListResponse(BaseModel):
    """Paginated list response."""

    items: list[RunSummary]
    total: int
    limit: int
    offset: int


@router.get("/runs", response_model=RunsListResponse)
def list_runs(
    db: Session = Depends(get_db),
    limit: int = Query(_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    offset: int = Query(0, ge=0),
    tool: str | None = Query(None, description="Filter to a single tool name"),
    status: StatusFilter = Query("all", description="Filter by status"),
    since: SinceFilter = Query("all", description="Time window filter"),
) -> RunsListResponse:
    """Return the most recent runs, newest first.

    The UI calls this on page load and after any run completes. Keep the
    payload small — use GET /api/runs/{id} for the full input/output.
    """
    query = select(Run).order_by(Run.created_at.desc(), Run.id.desc())
    count_query = select(func.count()).select_from(Run)

    # Apply filters to both the list and the total count.
    if tool:
        query = query.where(Run.tool_name == tool)
        count_query = count_query.where(Run.tool_name == tool)
    if status != "all":
        query = query.where(Run.status == status)
        count_query = count_query.where(Run.status == status)
    if since != "all":
        cutoff = _cutoff_for(since)
        query = query.where(Run.created_at >= cutoff)
        count_query = count_query.where(Run.created_at >= cutoff)

    total = db.scalar(count_query) or 0
    rows = db.scalars(query.limit(limit).offset(offset)).all()

    return RunsListResponse(
        items=[RunSummary.model_validate(r, from_attributes=True) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: int, db: Session = Depends(get_db)) -> RunDetail:
    """Return a single run with full input/output payloads."""
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return RunDetail.model_validate(run, from_attributes=True)


def _cutoff_for(since: SinceFilter) -> datetime:
    """Return the UTC datetime below which runs are excluded."""
    now = utcnow()
    # Strip tzinfo for SQLite comparison compatibility (our created_at column
    # stores naive UTC in SQLite and aware UTC in Postgres — using replace()
    # here picks the intersection that works for both).
    naive_now = now.replace(tzinfo=None)

    if since == "today":
        return naive_now.replace(hour=0, minute=0, second=0, microsecond=0)
    if since == "week":
        return naive_now - timedelta(days=7)
    if since == "month":
        return naive_now - timedelta(days=30)
    return datetime.min

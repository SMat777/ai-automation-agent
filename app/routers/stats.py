"""Stats endpoint — aggregated metrics for the observability dashboard."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter

from app.services.cost import calculate_cost

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats")
def get_stats() -> dict[str, Any]:
    """Return aggregated platform statistics."""
    return _query_stats()


def _query_stats() -> dict[str, Any]:
    """Query the database for aggregated metrics."""
    try:
        from app.db.database import SessionLocal  # noqa: PLC0415
        from app.models.run import Run  # noqa: PLC0415
        from sqlalchemy import func  # noqa: PLC0415

        with SessionLocal() as session:
            # Total runs
            total_runs = session.query(func.count(Run.id)).scalar() or 0

            # Runs today
            today_start = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0,
            )
            runs_today = (
                session.query(func.count(Run.id))
                .filter(Run.created_at >= today_start)
                .scalar()
                or 0
            )

            # Error count
            error_count = (
                session.query(func.count(Run.id))
                .filter(Run.status == "error")
                .scalar()
                or 0
            )

            # Average duration
            avg_duration = (
                session.query(func.avg(Run.duration_ms))
                .filter(Run.duration_ms.isnot(None))
                .scalar()
                or 0
            )

            # Total cost
            runs_with_tokens = (
                session.query(Run.input_tokens, Run.output_tokens)
                .filter(Run.input_tokens.isnot(None))
                .all()
            )
            total_cost = sum(
                calculate_cost(r.input_tokens or 0, r.output_tokens or 0)
                for r in runs_with_tokens
            )

            # Runs by tool
            tool_counts = (
                session.query(Run.tool_name, func.count(Run.id))
                .group_by(Run.tool_name)
                .all()
            )
            runs_by_tool = {name: count for name, count in tool_counts}

            # Runs by day (last 7 days)
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            daily_counts = (
                session.query(
                    func.date(Run.created_at).label("date"),
                    func.count(Run.id).label("count"),
                )
                .filter(Run.created_at >= week_ago)
                .group_by(func.date(Run.created_at))
                .order_by(func.date(Run.created_at))
                .all()
            )
            runs_by_day = [
                {"date": str(row.date), "count": row.count}
                for row in daily_counts
            ]

            return {
                "total_runs": total_runs,
                "runs_today": runs_today,
                "error_count": error_count,
                "avg_duration_ms": round(avg_duration),
                "total_cost_usd": round(total_cost, 4),
                "runs_by_tool": runs_by_tool,
                "runs_by_day": runs_by_day,
            }

    except Exception:
        # Fallback if DB isn't initialized
        return {
            "total_runs": 0,
            "runs_today": 0,
            "error_count": 0,
            "avg_duration_ms": 0,
            "total_cost_usd": 0.0,
            "runs_by_tool": {},
            "runs_by_day": [],
        }

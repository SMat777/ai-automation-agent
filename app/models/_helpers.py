"""Private helpers shared between model modules."""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Timezone-aware UTC now — replacement for deprecated datetime.utcnow().

    Used as SQLAlchemy column default so created_at columns always have
    explicit timezone info (important once we deploy to Postgres where
    naive vs aware datetimes are treated differently).
    """
    return datetime.now(UTC)

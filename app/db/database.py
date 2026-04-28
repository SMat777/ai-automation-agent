"""Database engine and session factory.

The engine is configured once at import time based on ``settings.database_url``.
FastAPI endpoints receive a Session via the ``get_db`` dependency — it ensures
every request gets its own session and that it is closed even if the endpoint
raises.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()


def _build_engine() -> Engine:
    """Construct the SQLAlchemy engine with dialect-appropriate options."""
    connect_args: dict[str, Any] = {}
    engine_kwargs: dict[str, Any] = {}

    if settings.is_sqlite:
        # SQLite's default is a single connection per process; allowing the
        # same connection across FastAPI's worker threads requires this flag.
        connect_args["check_same_thread"] = False
    else:
        # Production defaults for Postgres — modest pool to start.
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 10
        engine_kwargs["pool_pre_ping"] = True

    return create_engine(
        settings.database_url,
        connect_args=connect_args,
        **engine_kwargs,
    )


engine: Engine = _build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request.

    Usage in a router::

        @router.post("/thing")
        def create_thing(req: ThingRequest, db: Session = Depends(get_db)):
            ...

    The session is closed automatically when the request finishes, even if
    the endpoint raises an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

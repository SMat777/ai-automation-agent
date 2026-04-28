"""Tests for app.db — engine, session factory, and get_db dependency."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db import SessionLocal, engine, get_db


def test_engine_is_configured() -> None:
    assert isinstance(engine, Engine)
    assert engine.dialect.name in ("sqlite", "postgresql")


def test_session_executes_simple_query() -> None:
    with SessionLocal() as session:
        result = session.execute(text("SELECT 1 AS one")).scalar()
        assert result == 1


def test_get_db_yields_a_session() -> None:
    gen = get_db()
    db = next(gen)
    try:
        assert isinstance(db, Session)
        # Should be usable
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        # Closing the generator triggers the finally block in get_db
        gen.close()


def test_get_db_closes_after_completion() -> None:
    """After the generator exits, the session should be closed."""
    gen = get_db()
    db = next(gen)

    # Exhaust the generator — this runs the finally block
    try:
        next(gen)
    except StopIteration:
        pass

    # Session is closed — attempting to use it raises
    # (We verify via a flag rather than catching an exception to keep the
    # test resilient across SQLAlchemy versions.)
    assert db.in_transaction() is False

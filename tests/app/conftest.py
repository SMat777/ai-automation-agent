"""Shared pytest fixtures for app-level tests.

The ``db_session`` fixture provides an in-memory SQLite database with all
tables created fresh per test — so each test is isolated and fast.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app import models  # noqa: F401 — registers models on Base.metadata


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Return a fresh in-memory DB session; schema recreated per test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()

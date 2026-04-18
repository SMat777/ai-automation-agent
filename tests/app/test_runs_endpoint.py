"""Integration tests for GET /api/runs and GET /api/runs/{id}."""

from __future__ import annotations

from collections.abc import Generator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.db.base import Base
from app.main import app
from app import models  # noqa: F401 — registers models on Base.metadata
from app.models import Run, User
from app.models._helpers import utcnow


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def client_with_seeded_db() -> Generator[tuple[TestClient, Session], None, None]:
    """TestClient + session sharing an in-memory SQLite DB with demo runs."""
    # StaticPool keeps all FastAPI worker threads on the same SQLite
    # connection — otherwise each thread gets its own empty in-memory DB.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    # Seed: guest + a small set of runs spanning tools, statuses, times.
    session = TestSession()
    guest = User(display_name="Guest", role="guest")
    session.add(guest)
    session.commit()

    now = utcnow().replace(tzinfo=None)
    seeds = [
        ("analyze", "success", 5, now - timedelta(minutes=5)),
        ("extract", "success", 12, now - timedelta(minutes=30)),
        ("summarize", "success", 45, now - timedelta(hours=3)),
        ("pipeline", "error", 100, now - timedelta(days=2)),
        ("process", "success", 250, now - timedelta(days=10)),
        ("chat", "success", 1500, now - timedelta(days=45)),
    ]
    for tool_name, status, duration, created in seeds:
        session.add(Run(
            user_id=guest.id,
            tool_name=tool_name,
            input_hash=tool_name + str(duration).zfill(6),
            input_json={"demo": True},
            output_json={"demo": True},
            duration_ms=duration,
            status=status,
            error_message=("boom" if status == "error" else None),
            created_at=created,
        ))
    session.commit()

    # Override get_db so the endpoint uses our test session
    def _override_get_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app), session
    finally:
        app.dependency_overrides.clear()
        session.close()
        engine.dispose()


# ── GET /api/runs (list) ─────────────────────────────────────────────────────


class TestListRuns:
    def test_returns_all_runs_newest_first(self, client_with_seeded_db) -> None:
        client, _ = client_with_seeded_db
        resp = client.get("/api/runs")
        assert resp.status_code == 200
        data = resp.json()

        assert data["total"] == 6
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert len(data["items"]) == 6
        # Newest first
        assert data["items"][0]["tool_name"] == "analyze"
        assert data["items"][-1]["tool_name"] == "chat"

    def test_pagination(self, client_with_seeded_db) -> None:
        client, _ = client_with_seeded_db
        resp = client.get("/api/runs?limit=2&offset=0")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 2

        resp2 = client.get("/api/runs?limit=2&offset=2")
        page2 = resp2.json()["items"]
        assert len(page2) == 2
        # Non-overlapping
        assert page2[0]["id"] != resp.json()["items"][0]["id"]

    def test_rejects_limit_over_max(self, client_with_seeded_db) -> None:
        client, _ = client_with_seeded_db
        resp = client.get("/api/runs?limit=1000")
        assert resp.status_code == 422  # Query validation

    def test_filter_by_tool(self, client_with_seeded_db) -> None:
        client, _ = client_with_seeded_db
        resp = client.get("/api/runs?tool=analyze")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["tool_name"] == "analyze"

    def test_filter_by_status_error(self, client_with_seeded_db) -> None:
        client, _ = client_with_seeded_db
        resp = client.get("/api/runs?status=error")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "error"
        assert data["items"][0]["error_message"] == "boom"

    def test_filter_by_status_success(self, client_with_seeded_db) -> None:
        client, _ = client_with_seeded_db
        resp = client.get("/api/runs?status=success")
        assert resp.json()["total"] == 5

    def test_filter_since_today(self, client_with_seeded_db) -> None:
        client, _ = client_with_seeded_db
        resp = client.get("/api/runs?since=today")
        # Seeds within last 5 minutes and 30 minutes and 3 hours are all "today"
        assert resp.json()["total"] >= 2

    def test_filter_since_week(self, client_with_seeded_db) -> None:
        client, _ = client_with_seeded_db
        resp = client.get("/api/runs?since=week")
        # Excludes the 10-day-old and 45-day-old rows
        assert resp.json()["total"] == 4

    def test_filter_since_month(self, client_with_seeded_db) -> None:
        client, _ = client_with_seeded_db
        resp = client.get("/api/runs?since=month")
        # Excludes only the 45-day-old row
        assert resp.json()["total"] == 5

    def test_combined_filters(self, client_with_seeded_db) -> None:
        client, _ = client_with_seeded_db
        resp = client.get("/api/runs?status=success&tool=chat")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["tool_name"] == "chat"


# ── GET /api/runs/{id} (detail) ──────────────────────────────────────────────


class TestGetRun:
    def test_returns_full_detail(self, client_with_seeded_db) -> None:
        client, session = client_with_seeded_db
        some_run = session.query(Run).first()
        assert some_run is not None

        resp = client.get(f"/api/runs/{some_run.id}")
        assert resp.status_code == 200
        data = resp.json()

        assert data["id"] == some_run.id
        assert data["tool_name"] == some_run.tool_name
        assert data["input_json"] == {"demo": True}
        assert data["output_json"] == {"demo": True}

    def test_returns_404_for_missing(self, client_with_seeded_db) -> None:
        client, _ = client_with_seeded_db
        resp = client.get("/api/runs/99999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

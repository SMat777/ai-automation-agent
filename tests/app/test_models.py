"""Tests for ORM models: User, Run, AuditLog.

Verifies table structure, defaults, foreign-key relationships, and cascade
behaviour. These tests run against an in-memory SQLite DB — see conftest.py.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import AuditLog, Run, User


class TestUser:
    def test_create_user_with_defaults(self, db_session: Session) -> None:
        user = User(email="alice@test.dk")
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "alice@test.dk"
        assert user.role == "user"  # default
        assert user.password_hash is None  # nullable until Fase 2
        assert isinstance(user.created_at, datetime)

    def test_email_is_unique(self, db_session: Session) -> None:
        db_session.add(User(email="dup@test.dk"))
        db_session.commit()

        db_session.add(User(email="dup@test.dk"))
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_guest_user_without_email(self, db_session: Session) -> None:
        """Email is nullable so the built-in guest user works."""
        guest = User(display_name="Guest", role="guest")
        db_session.add(guest)
        db_session.commit()

        assert guest.id is not None
        assert guest.email is None
        assert guest.role == "guest"

    def test_repr_is_readable(self, db_session: Session) -> None:
        user = User(email="readable@test.dk")
        db_session.add(user)
        db_session.commit()

        repr_str = repr(user)
        assert "User" in repr_str
        assert "readable@test.dk" in repr_str


class TestRun:
    def test_create_run_linked_to_user(self, db_session: Session) -> None:
        user = User(email="runner@test.dk")
        db_session.add(user)
        db_session.commit()

        run = Run(
            user_id=user.id,
            tool_name="analyze",
            input_hash="a" * 64,
            input_json={"text": "hello"},
            output_json={"document_type": "email"},
            duration_ms=127,
        )
        db_session.add(run)
        db_session.commit()

        assert run.id is not None
        assert run.user_id == user.id
        assert run.status == "success"  # default
        assert run.tool_name == "analyze"

    def test_run_without_user_allowed(self, db_session: Session) -> None:
        """Anonymous runs are allowed (user_id is nullable)."""
        run = Run(tool_name="analyze", input_hash="b" * 64, duration_ms=50)
        db_session.add(run)
        db_session.commit()

        assert run.id is not None
        assert run.user_id is None

    def test_json_columns_roundtrip(self, db_session: Session) -> None:
        """JSON columns survive a round-trip to the DB and back."""
        payload = {"nested": {"key": "value", "count": 42, "items": [1, 2, 3]}}

        run = Run(
            tool_name="extract",
            input_hash="c" * 64,
            input_json=payload,
            duration_ms=0,
        )
        db_session.add(run)
        db_session.commit()
        run_id = run.id
        db_session.expunge_all()  # clear session cache

        reloaded = db_session.get(Run, run_id)
        assert reloaded is not None
        assert reloaded.input_json == payload

    def test_user_runs_relationship(self, db_session: Session) -> None:
        user = User(email="multi@test.dk")
        db_session.add(user)
        db_session.commit()

        for i in range(3):
            db_session.add(Run(
                user_id=user.id,
                tool_name=f"tool_{i}",
                input_hash=str(i) * 64,
                duration_ms=i * 10,
            ))
        db_session.commit()

        assert len(user.runs) == 3
        assert {r.tool_name for r in user.runs} == {"tool_0", "tool_1", "tool_2"}

    def test_cascade_delete_removes_runs(self, db_session: Session) -> None:
        """Deleting a user cascades to their runs (GDPR-style deletion)."""
        user = User(email="goodbye@test.dk")
        db_session.add(user)
        db_session.commit()

        db_session.add(Run(
            user_id=user.id,
            tool_name="analyze",
            input_hash="d" * 64,
            duration_ms=10,
        ))
        db_session.commit()

        assert db_session.scalar(select(Run).where(Run.user_id == user.id)) is not None

        db_session.delete(user)
        db_session.commit()

        # Run should be gone via cascade
        remaining = db_session.scalars(select(Run)).all()
        assert len(remaining) == 0


class TestAuditLog:
    def test_audit_entry_basic(self, db_session: Session) -> None:
        user = User(email="auditor@test.dk")
        db_session.add(user)
        db_session.commit()

        entry = AuditLog(
            user_id=user.id,
            action="login",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )
        db_session.add(entry)
        db_session.commit()

        assert entry.id is not None
        assert entry.action == "login"
        assert isinstance(entry.created_at, datetime)

    def test_audit_entry_without_user(self, db_session: Session) -> None:
        """Audit entries can be anonymous (failed logins, system events)."""
        entry = AuditLog(action="login.failed", ip_address="1.2.3.4")
        db_session.add(entry)
        db_session.commit()

        assert entry.user_id is None

    def test_audit_survives_user_deletion(self, db_session: Session) -> None:
        """When a user is deleted, audit entries remain (with user_id=NULL).

        This is governance-critical: deleting a user must not erase their
        action history. ondelete='SET NULL' gives us that property.
        """
        user = User(email="ephemeral@test.dk")
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        db_session.add(AuditLog(user_id=user_id, action="login"))
        db_session.add(AuditLog(user_id=user_id, action="logout"))
        db_session.commit()

        db_session.delete(user)
        db_session.commit()

        entries = db_session.scalars(select(AuditLog)).all()
        assert len(entries) == 2
        assert all(e.user_id is None for e in entries)
        assert {e.action for e in entries} == {"login", "logout"}

    def test_audit_ordered_chronologically(self, db_session: Session) -> None:
        """The created_at index supports chronological queries."""
        base = datetime(2026, 1, 1)
        for i, action in enumerate(["login", "run.create", "logout"]):
            db_session.add(AuditLog(
                action=action,
                created_at=base + timedelta(minutes=i),
            ))
        db_session.commit()

        entries = db_session.scalars(
            select(AuditLog).order_by(AuditLog.created_at)
        ).all()
        assert [e.action for e in entries] == ["login", "run.create", "logout"]

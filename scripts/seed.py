"""Seed the database with a guest user and a handful of demo runs.

Run this once after the first ``alembic upgrade head``::

    python scripts/seed.py

It is idempotent — running it multiple times will not create duplicate
guest users or runs.

Purpose:
- Give first-time visitors something visible in the Runs sidebar so the
  empty state is less jarring than a truly empty database.
- Establish the built-in guest user so ``log_run()`` can attribute runs
  when no authenticated user exists (Fase 2 adds real auth).
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

# Make the project importable when run as a script.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import Run, User  # noqa: E402
from app.models._helpers import utcnow  # noqa: E402


GUEST_DISPLAY_NAME = "Guest"
GUEST_ROLE = "guest"


def main() -> None:
    db: Session = SessionLocal()
    try:
        guest = _ensure_guest_user(db)
        _ensure_demo_runs(db, guest)
        db.commit()
        print(f"✓ Seed complete — guest user id={guest.id}")
    finally:
        db.close()


def _ensure_guest_user(db: Session) -> User:
    """Create the guest user if it does not exist; return it either way."""
    existing = db.scalar(select(User).where(User.role == GUEST_ROLE).limit(1))
    if existing is not None:
        print(f"  guest user already present (id={existing.id})")
        return existing

    guest = User(
        email=None,
        display_name=GUEST_DISPLAY_NAME,
        role=GUEST_ROLE,
    )
    db.add(guest)
    db.flush()  # ensures guest.id is populated before we return it
    print(f"  created guest user (id={guest.id})")
    return guest


def _ensure_demo_runs(db: Session, guest: User) -> None:
    """Populate the runs table with a small, diverse set of demo rows.

    Skips insertion if any runs already exist (to keep the script idempotent
    and to preserve real user history on subsequent runs).
    """
    existing_count = db.scalar(select(Run.id).limit(1))
    if existing_count is not None:
        print("  runs table is not empty — skipping demo rows")
        return

    now = utcnow()
    demos = [
        {
            "tool_name": "analyze",
            "input_json": {"text": "# Sprint review notes\n\nTeam aligned on roadmap."},
            "output_json": {"document_type": "markdown_document", "entities": {}},
            "duration_ms": 42,
            "status": "success",
            "offset_minutes": 5,
        },
        {
            "tool_name": "process",
            "input_json": {"text": "(invoice demo)", "document_type": "auto"},
            "output_json": {
                "document_type": "invoice",
                "confidence": 0.87,
                "validation_errors": 0,
            },
            "duration_ms": 315,
            "status": "success",
            "offset_minutes": 12,
        },
        {
            "tool_name": "extract",
            "input_json": {"text": "(demo)", "fields": ["Company"], "strategy": "auto"},
            "output_json": {"extracted": {"Company": "Northwind Traders"}, "fields_found": 1},
            "duration_ms": 18,
            "status": "success",
            "offset_minutes": 30,
        },
        {
            "tool_name": "summarize",
            "input_json": {"text": "(long demo text)", "format": "bullets", "max_points": 5},
            "output_json": {"summary": "- Point 1\n- Point 2\n- Point 3", "method": "extractive"},
            "duration_ms": 67,
            "status": "success",
            "offset_minutes": 55,
        },
        {
            "tool_name": "pipeline",
            "input_json": {"task": "analyze github", "pipeline": "github"},
            "output_json": None,
            "duration_ms": 142,
            "status": "error",
            "error_message": "Pipeline dependencies not installed",
            "offset_minutes": 70,
        },
        {
            "tool_name": "chat",
            "input_json": {"message": "What can you do?"},
            "output_json": {"answer": "I can analyze documents, extract data, summarize text…"},
            "duration_ms": 1842,
            "status": "success",
            "input_tokens": 120,
            "output_tokens": 215,
            "offset_minutes": 125,
        },
    ]

    for demo in demos:
        offset = demo.pop("offset_minutes")
        created = now - timedelta(minutes=offset)
        run = Run(
            user_id=guest.id,
            input_hash="demo" + str(offset).zfill(6),  # unique enough for demo rows
            created_at=created,
            **demo,
        )
        db.add(run)

    print(f"  created {len(demos)} demo run(s)")


if __name__ == "__main__":
    main()

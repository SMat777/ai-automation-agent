"""Seed the database with a guest user and a handful of demo runs.

Run once after the first ``alembic upgrade head``::

    make seed

The script is idempotent — running it again leaves existing data alone.

Purpose:
- Establish the built-in guest user so ``log_run()`` can attribute runs
  when no authenticated user exists (Fase 2 adds real auth).
- Pre-populate the Runs sidebar with a *realistic* cross-section of the
  tools so the UI is populated on first visit and a recruiter can see the
  product in use without having to click anything.

Seed payloads are written to look like real work — actual-shaped invoices,
meeting notes, a GitHub repo analysis, a chat question — rather than the
obviously-synthetic '(demo)' placeholders the earlier version used.
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
    """Populate the runs table with a small, diverse, realistic set.

    Skips insertion if any runs already exist (to keep the script
    idempotent and to preserve real user history on re-runs).
    """
    existing = db.scalar(select(Run.id).limit(1))
    if existing is not None:
        print("  runs table is not empty — skipping demo rows")
        return

    now = utcnow()
    demos = _build_demo_runs()

    for demo in demos:
        offset = demo.pop("offset_minutes")
        created = now - timedelta(minutes=offset)
        run = Run(
            user_id=guest.id,
            input_hash=f"seed-{offset:06d}",  # unique + sortable
            created_at=created,
            **demo,
        )
        db.add(run)

    print(f"  created {len(demos)} demo run(s)")


# ── Demo payloads ───────────────────────────────────────────────────────────


def _build_demo_runs() -> list[dict]:
    """Return a curated list of realistic Run rows, spanning all tools."""
    return [
        _analyze_example(),
        _process_invoice_example(),
        _extract_contact_example(),
        _summarize_report_example(),
        _chat_question_example(),
        _pipeline_github_error_example(),
    ]


def _analyze_example() -> dict:
    text = (
        "# Q1 2026 Sprint Review\n\n"
        "Date: 2026-03-28\n"
        "Attendees: Erik Hansen, Mette Nielsen, Thomas Holm\n\n"
        "## Summary\n\n"
        "Delivered the document-processing pipeline ahead of schedule. "
        "Integration with Business Central is in staging; go-live planned for week 14."
    )
    return {
        "tool_name": "analyze",
        "input_json": {"text": text, "focus": "general"},
        "output_json": {
            "document_type": "markdown_document",
            "sections": [
                {"level": 1, "title": "Q1 2026 Sprint Review"},
                {"level": 2, "title": "Summary"},
            ],
            "entities": {
                "emails": [],
                "dates": ["2026-03-28"],
                "urls": [],
                "organizations": [],
            },
            "key_points": [
                "Delivered the document-processing pipeline ahead of schedule.",
                "Integration with Business Central is in staging; go-live planned for week 14.",
            ],
            "statistics": {
                "word_count": 44,
                "sentence_count": 3,
                "paragraph_count": 3,
                "line_count": 9,
            },
            "focus": "general",
        },
        "duration_ms": 38,
        "status": "success",
        "offset_minutes": 7,
    }


def _process_invoice_example() -> dict:
    text = (
        "INVOICE #INV-2026-0214\n\n"
        "From: Nordic Data Solutions ApS\n"
        "To: Meridian Logistics A/S\n\n"
        "Invoice Date: 2026-04-01\n"
        "Due Date: 2026-04-30\n\n"
        "Subtotal: 180,000 DKK\n"
        "VAT (25%): 45,000 DKK\n"
        "Total: 225,000 DKK\n\n"
        "Reference: INV-2026-0214"
    )
    return {
        "tool_name": "process",
        "input_json": {"text": text, "document_type": "auto"},
        "output_json": {
            "document_type": "invoice",
            "total_duration_ms": 287,
            "confidence": 0.91,
            "fields_extracted": "7/8",
            "entities_found": 3,
            "validation_errors": 0,
            "erp_output": {
                "document_type": "invoice",
                "extracted_fields": {
                    "Invoice Date": "2026-04-01",
                    "Due Date": "2026-04-30",
                    "Subtotal": "180,000 DKK",
                    "VAT": "45,000 DKK",
                    "Total": "225,000 DKK",
                    "From": "Nordic Data Solutions ApS",
                    "To": "Meridian Logistics A/S",
                },
                "entities": {
                    "dates": ["2026-04-01", "2026-04-30"],
                    "organizations": ["Nordic Data Solutions ApS", "Meridian Logistics A/S"],
                },
                "confidence_score": 0.91,
                "validation_passed": True,
                "processed_at": "2026-04-18T14:22:10Z",
            },
        },
        "duration_ms": 287,
        "status": "success",
        "offset_minutes": 23,
    }


def _extract_contact_example() -> dict:
    text = (
        "Name: Sarah Williamson\n"
        "Title: Head of Procurement\n"
        "Company: GreenField Manufacturing A/S\n"
        "Email: sarah.williamson@greenfield.dk\n"
        "Phone: +45 33 12 45 67"
    )
    return {
        "tool_name": "extract",
        "input_json": {
            "text": text,
            "fields": ["Name", "Title", "Company", "Email", "Phone"],
            "strategy": "auto",
        },
        "output_json": {
            "extracted": {
                "Name": "Sarah Williamson",
                "Title": "Head of Procurement",
                "Company": "GreenField Manufacturing A/S",
                "Email": "sarah.williamson@greenfield.dk",
                "Phone": "+45 33 12 45 67",
            },
            "fields_found": 5,
            "fields_missing": 0,
            "strategy": "auto",
            "strategies_used": ["key_value"],
        },
        "duration_ms": 14,
        "status": "success",
        "offset_minutes": 48,
    }


def _summarize_report_example() -> dict:
    text = (
        "The Q1 2026 operational review identified three priority areas: "
        "supply chain resilience, customer-facing automation, and cost optimisation. "
        "Supply chain initiatives are on track, with 82% of tier-1 suppliers now "
        "participating in the new forecasting portal. Automation work delivered a "
        "40% reduction in invoice-processing time. Cost optimisation achieved 6.3M DKK "
        "in annualised savings through contract renegotiation. Risks: a single-vendor "
        "dependency on the logistics side remains unaddressed."
    )
    return {
        "tool_name": "summarize",
        "input_json": {"text": text, "format": "bullets", "max_points": 4},
        "output_json": {
            "summary": (
                "- Q1 2026 review identified three priority areas: supply chain, "
                "automation, and cost optimisation.\n"
                "- 82% of tier-1 suppliers now participate in the new forecasting portal.\n"
                "- Invoice-processing time cut by 40% via automation work.\n"
                "- 6.3M DKK in annualised savings through contract renegotiation."
            ),
            "format": "bullets",
            "method": "extractive",
            "original_word_count": 72,
            "sentence_count": 6,
        },
        "duration_ms": 62,
        "status": "success",
        "offset_minutes": 95,
    }


def _chat_question_example() -> dict:
    return {
        "tool_name": "chat",
        "input_json": {"message": "Can you process invoices with VAT validation?"},
        "output_json": {
            "answer": (
                "Yes — the Process tab runs a four-step pipeline on any invoice: "
                "analyse, extract, summarise, validate. The validate step "
                "checks that the total matches subtotal + VAT and that the due "
                "date falls after the invoice date. Invalid invoices are flagged "
                "with a specific reason; valid ones produce an ERP-ready JSON "
                "payload."
            )
        },
        "duration_ms": 1_420,
        "status": "success",
        "input_tokens": 14,
        "output_tokens": 78,
        "offset_minutes": 170,
    }


def _pipeline_github_error_example() -> dict:
    return {
        "tool_name": "pipeline",
        "input_json": {"task": "Fetch recent repos for analysis", "pipeline": "github"},
        "output_json": None,
        "duration_ms": 45,
        "status": "error",
        "error_message": (
            "Pipeline dependencies not installed. Run: cd automation && npm install"
        ),
        "offset_minutes": 1_420,  # ~yesterday
    }


if __name__ == "__main__":
    main()

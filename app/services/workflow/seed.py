"""Seed preset workflows into the database on startup.

Called once when the application starts. Checks if preset workflows already
exist (by name) to avoid duplicates on restarts. These workflows demonstrate
the engine's capabilities and serve as templates for user-created workflows.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.workflow import Workflow, WorkflowStep

logger = logging.getLogger(__name__)

# ── Preset workflow definitions ──────────────────────────────────────────────

PRESET_WORKFLOWS = [
    {
        "name": "Document Processing",
        "description": (
            "Analyze, extract structured data from, and summarize any document. "
            "A general-purpose pipeline for invoices, contracts, reports, and more."
        ),
        "on_error": "stop",
        "steps": [
            {
                "step_id": "analyze",
                "tool_name": "analyze_document",
                "input_template": {"text": "$input.text", "focus": "general"},
            },
            {
                "step_id": "extract",
                "tool_name": "extract_data",
                "input_template": {"text": "$input.text", "strategy": "auto"},
            },
            {
                "step_id": "summarize",
                "tool_name": "summarize",
                "input_template": {"text": "$input.text", "max_length": 200},
            },
        ],
    },
    {
        "name": "Email Triage",
        "description": (
            "Classify an incoming email by category and priority, "
            "then draft a professional reply. Useful for customer support automation."
        ),
        "on_error": "stop",
        "steps": [
            {
                "step_id": "classify",
                "tool_name": "classify_email",
                "input_template": {"email_text": "$input.text"},
            },
            {
                "step_id": "draft",
                "tool_name": "draft_email_reply",
                "input_template": {
                    "context": "$input.text",
                    "tone": "professional",
                },
            },
        ],
    },
    {
        "name": "Research & Summarize",
        "description": (
            "Scrape a web page and produce a concise summary. "
            "Chains the web scraper with the summarizer for quick research."
        ),
        "on_error": "stop",
        "steps": [
            {
                "step_id": "scrape",
                "tool_name": "scrape_url",
                "input_template": {"url": "$input.url"},
            },
            {
                "step_id": "summarize",
                "tool_name": "summarize",
                "input_template": {"text": "$prev.content", "max_length": 300},
            },
        ],
    },
]


# ── Seed function ────────────────────────────────────────────────────────────


def seed_preset_workflows(db: Session) -> int:
    """Insert preset workflows if they don't already exist. Returns count of newly created."""
    created = 0

    for preset in PRESET_WORKFLOWS:
        # Skip if already seeded (match by name)
        exists = db.query(Workflow).filter(
            Workflow.name == preset["name"],
            Workflow.is_preset.is_(True),
        ).first()

        if exists:
            continue

        workflow = Workflow(
            name=preset["name"],
            description=preset["description"],
            on_error=preset["on_error"],
            is_preset=True,
        )
        for i, step_def in enumerate(preset["steps"]):
            workflow.steps.append(
                WorkflowStep(
                    step_order=i,
                    step_id=step_def["step_id"],
                    tool_name=step_def["tool_name"],
                    input_template=step_def["input_template"],
                )
            )

        db.add(workflow)
        created += 1

    if created:
        db.commit()
        logger.info("Seeded %d preset workflow(s)", created)

    return created

"""Workflow models — declarative multi-step tool automation.

A Workflow chains multiple tools into a sequence. Each WorkflowStep
references a tool from TOOL_HANDLERS and defines an input template
with variable references ($input, $prev, $steps.X) that the engine
resolves at execution time.

Preset workflows (is_preset=True) are seeded on startup and cannot
be deleted via the API. User-created workflows can be managed freely.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._helpers import utcnow


class Workflow(Base):
    """A reusable automation workflow definition."""

    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    on_error: Mapped[str] = mapped_column(
        String(20), nullable=False, default="stop",
    )  # "stop" or "skip"
    is_preset: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False,
    )

    steps: Mapped[list[WorkflowStep]] = relationship(
        "WorkflowStep",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.step_order",
    )

    def __repr__(self) -> str:
        return f"<Workflow {self.name!r} ({len(self.steps)} steps)>"

    def to_dict(self) -> dict[str, Any]:
        """Serialize for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "on_error": self.on_error,
            "is_preset": self.is_preset,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "steps": [s.to_dict() for s in self.steps],
        }


class WorkflowStep(Base):
    """A single step in a workflow — maps to one tool invocation."""

    __tablename__ = "workflow_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_id: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )  # Human-readable ID, e.g. "analyze", "extract"
    tool_name: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )  # Must exist in TOOL_HANDLERS
    input_template: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict,
    )  # Variable references resolved at execution time

    workflow: Mapped[Workflow] = relationship("Workflow", back_populates="steps")

    def __repr__(self) -> str:
        return f"<WorkflowStep {self.step_id!r} tool={self.tool_name!r}>"

    def to_dict(self) -> dict[str, Any]:
        """Serialize for API responses."""
        return {
            "id": self.id,
            "step_order": self.step_order,
            "step_id": self.step_id,
            "tool_name": self.tool_name,
            "input_template": self.input_template,
        }

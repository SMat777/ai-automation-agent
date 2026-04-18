"""Run model — one row per tool invocation.

Every call to analyze/extract/summarize/process/pipeline/chat creates a row
here. This is the backbone of run history, cost tracking, and the future
observability dashboard.

Kept deliberately wide — we'd rather have extra columns unused than realise
mid-Fase 5 that we cannot reconstruct what happened.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Run(Base):
    """A single invocation of a tool or agent endpoint.

    Status values: ``success``, ``error``, ``timeout``.
    Tools names correspond to the endpoint used: analyze, extract, summarize,
    process, pipeline, chat.
    """

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )

    tool_name: Mapped[str] = mapped_column(String(50), index=True)

    # SHA-256 of the input payload — lets us dedupe and find repeat runs
    # without storing the full input in this table.
    input_hash: Mapped[str] = mapped_column(String(64), index=True)

    # Flexible JSON blobs — the exact shape depends on the tool. We store
    # them so the UI can reconstruct history and the audit log can reference
    # what was computed.
    input_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

    # Token usage — only populated for AI-backed calls.
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(20), default="success", index=True)
    error_message: Mapped[str | None] = mapped_column(String(2000))

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,  # the Runs list is always sorted by created_at DESC
    )

    user: Mapped[User | None] = relationship("User", back_populates="runs")

    def __repr__(self) -> str:
        return (
            f"<Run id={self.id} tool={self.tool_name!r} "
            f"status={self.status!r} duration={self.duration_ms}ms>"
        )

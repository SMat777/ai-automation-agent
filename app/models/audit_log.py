"""Audit log — append-only record of security- and governance-relevant events.

This is the foundation that SECURITY.md's governance section rests on. Rows
are only ever inserted, never updated or deleted. If we need to retract
something, we append a compensating entry rather than mutating history.

Kept intentionally lightweight — just enough to reconstruct who did what
when, without duplicating the data that lives in other tables.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    """An immutable, append-only audit entry.

    Example actions: ``login``, ``logout``, ``run.create``, ``prompt.update``,
    ``user.delete``. The convention is ``<resource>.<verb>`` so the table is
    filterable by resource type.
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )

    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str | None] = mapped_column(String(50), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(100))

    # Request metadata. Stored so governance reviews can reconstruct the
    # context of an action — not used for app logic.
    ip_address: Mapped[str | None] = mapped_column(String(45))  # IPv6-sized
    user_agent: Mapped[str | None] = mapped_column(String(500))

    # Free-form detail, kept short on purpose. For detailed payloads, the
    # action should reference a Run or another entity via resource_id.
    detail: Mapped[str | None] = mapped_column(String(1000))

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    user: Mapped[User | None] = relationship("User", back_populates="audit_entries")

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action!r} "
            f"user_id={self.user_id} at={self.created_at.isoformat()}>"
        )

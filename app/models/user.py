"""User model.

Authentication (password hashing, sessions) arrives in Fase 2. For now
we store only the fields we know we will need, with auth fields nullable
so the guest user can exist without a password.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._helpers import utcnow

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.run import Run


class User(Base):
    """A user of the system.

    ``role`` is intentionally a plain string for now (not an Enum) — we will
    formalise it when authorisation arrives in Fase 2. Keeping the schema
    loose lets us iterate without premature migrations.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    # email is nullable for the built-in guest user; unique for real accounts
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(100))

    # Password hash — populated in Fase 2 when signup lands.
    password_hash: Mapped[str | None] = mapped_column(String(255))

    # Encrypted per-user Anthropic API key — Fase 2 too.
    api_key_encrypted: Mapped[str | None] = mapped_column(String(500))

    role: Mapped[str] = mapped_column(String(20), default="user", index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    # Reverse relationships
    runs: Mapped[list[Run]] = relationship(
        "Run",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_entries: Mapped[list[AuditLog]] = relationship(
        "AuditLog",
        back_populates="user",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"

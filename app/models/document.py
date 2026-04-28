"""Document model — tracks uploaded files in the knowledge base.

Each uploaded file creates one row here. The actual text chunks live
in ChromaDB (vector store), but this table provides the metadata
for listing, managing, and deleting documents.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._helpers import utcnow


class Document(Base):
    """An uploaded document in the knowledge base."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, docx, eml, txt, md
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    doc_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # UUID for vector store
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Document {self.filename!r} ({self.file_type}, {self.chunk_count} chunks)>"

    def to_dict(self) -> dict:
        """Serialize for API responses."""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "chunk_count": self.chunk_count,
            "doc_id": self.doc_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

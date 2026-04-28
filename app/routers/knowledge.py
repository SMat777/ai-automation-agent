"""Knowledge base management endpoints."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["knowledge"])


@lru_cache(maxsize=1)
def _get_retriever():  # type: ignore[no-untyped-def]
    from app.services.rag.retriever import Retriever  # noqa: PLC0415
    return Retriever()


@router.get("/knowledge")
def list_knowledge() -> dict[str, Any]:
    """List all documents in the knowledge base."""
    retriever = _get_retriever()
    doc_ids = retriever.list_documents()

    # Try to enrich with metadata from DB
    documents = _get_documents_metadata(doc_ids)

    return {"documents": documents, "count": len(documents)}


@router.delete("/knowledge/{doc_id}")
def delete_document(doc_id: str) -> dict[str, str]:
    """Remove a document from the knowledge base."""
    retriever = _get_retriever()
    retriever.delete_document(doc_id)
    _delete_document_metadata(doc_id)
    return {"status": "deleted", "doc_id": doc_id}


def _get_documents_metadata(doc_ids: list[str]) -> list[dict[str, Any]]:
    """Fetch document metadata from DB, fall back to bare IDs."""
    try:
        from app.db.database import SessionLocal  # noqa: PLC0415
        from app.models.document import Document  # noqa: PLC0415

        with SessionLocal() as session:
            docs = session.query(Document).filter(Document.doc_id.in_(doc_ids)).all()
            return [d.to_dict() for d in docs]
    except Exception:
        return [{"doc_id": did} for did in doc_ids]


def _delete_document_metadata(doc_id: str) -> None:
    """Remove document metadata from DB."""
    try:
        from app.db.database import SessionLocal  # noqa: PLC0415
        from app.models.document import Document  # noqa: PLC0415

        with SessionLocal() as session:
            session.query(Document).filter(Document.doc_id == doc_id).delete()
            session.commit()
    except Exception:
        pass

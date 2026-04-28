"""Document upload endpoint — ingest files into the RAG knowledge base."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/api", tags=["upload"])

_SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".eml"}
_EXTENSION_MAP = {
    ".txt": "txt",
    ".md": "md",
    ".pdf": "pdf",
    ".docx": "docx",
    ".eml": "eml",
}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload a document to the knowledge base.

    Supports: PDF, DOCX, EML, TXT, MD.
    The file is extracted, chunked, embedded, and stored in ChromaDB.
    """
    filename = file.filename or "unnamed"
    ext = _get_extension(filename)

    if ext not in _SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="File is empty")

    file_type = _EXTENSION_MAP.get(ext, "txt")
    result = _ingest_document(data, filename, file_type)

    return {
        "filename": filename,
        "file_type": file_type,
        "file_size": len(data),
        "status": "ingested",
        **result,
    }


def _get_extension(filename: str) -> str:
    """Extract lowercase file extension."""
    dot_idx = filename.rfind(".")
    if dot_idx == -1:
        return ""
    return filename[dot_idx:].lower()


def _ingest_document(
    data: bytes,
    filename: str,
    file_type: str,
) -> dict[str, Any]:
    """Extract text, chunk, embed, and store in vector DB.

    Returns dict with doc_id and chunk_count.
    """
    text = _extract_text(data, file_type)
    if not text.strip():
        return {"doc_id": "", "chunk_count": 0, "status": "empty"}

    from app.services.rag.retriever import Retriever  # noqa: PLC0415

    doc_id = str(uuid.uuid4())[:12]
    retriever = Retriever()
    chunk_count = retriever.ingest(
        doc_id=doc_id,
        text=text,
        source=filename,
    )

    # Store metadata in SQLite
    _save_document_metadata(doc_id, filename, file_type, len(data), chunk_count)

    return {"doc_id": doc_id, "chunk_count": chunk_count}


def _extract_text(data: bytes, file_type: str) -> str:
    """Route to the correct extractor based on file type."""
    if file_type == "pdf":
        from app.services.extractors.pdf import extract_pdf  # noqa: PLC0415
        return extract_pdf(data)
    elif file_type == "docx":
        from app.services.extractors.docx import extract_docx  # noqa: PLC0415
        return extract_docx(data)
    elif file_type == "eml":
        from app.services.extractors.email_parser import extract_email  # noqa: PLC0415
        return extract_email(data)
    else:
        from app.services.extractors.text import extract_text  # noqa: PLC0415
        return extract_text(data)


def _save_document_metadata(
    doc_id: str,
    filename: str,
    file_type: str,
    file_size: int,
    chunk_count: int,
) -> None:
    """Persist document metadata to the database."""
    try:
        from app.db.database import SessionLocal  # noqa: PLC0415
        from app.models.document import Document  # noqa: PLC0415

        with SessionLocal() as session:
            doc = Document(
                doc_id=doc_id,
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                chunk_count=chunk_count,
            )
            session.add(doc)
            session.commit()
    except Exception:
        pass  # Non-critical — vector store is the source of truth

"""DOCX text extractor using python-docx."""

from __future__ import annotations


def extract_docx(data: bytes) -> str:
    """Extract text from a DOCX file.

    Args:
        data: Raw DOCX file bytes.

    Returns:
        Extracted text with paragraphs separated by newlines.
    """
    import io

    from docx import Document  # noqa: PLC0415 (lazy import)

    doc = Document(io.BytesIO(data))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)

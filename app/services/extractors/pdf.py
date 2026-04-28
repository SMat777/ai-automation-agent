"""PDF text extractor using PyMuPDF (fitz)."""

from __future__ import annotations


def extract_pdf(data: bytes) -> str:
    """Extract text from a PDF file.

    Args:
        data: Raw PDF file bytes.

    Returns:
        Extracted text with page breaks marked.
    """
    import fitz  # noqa: PLC0415  (PyMuPDF — lazy import)

    doc = fitz.open(stream=data, filetype="pdf")
    pages: list[str] = []
    for page in doc:
        text = page.get_text().strip()
        if text:
            pages.append(text)
    doc.close()

    return "\n\n---\n\n".join(pages)

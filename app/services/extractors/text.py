"""Plain text extractor — passthrough for .txt and .md files."""

from __future__ import annotations


def extract_text(data: bytes) -> str:
    """Decode raw bytes to UTF-8 text.

    Args:
        data: Raw file bytes.

    Returns:
        Decoded text string.
    """
    return data.decode("utf-8", errors="replace")

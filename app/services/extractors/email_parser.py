"""Email (.eml) text extractor — parses email headers and body."""

from __future__ import annotations

import email
from email.policy import default as default_policy


def extract_email(data: bytes) -> str:
    """Parse an email message and extract headers + body text.

    Args:
        data: Raw .eml file bytes.

    Returns:
        Formatted string with key headers and body text.
    """
    msg = email.message_from_bytes(data, policy=default_policy)

    parts: list[str] = []

    # Extract key headers
    for header in ("From", "To", "Cc", "Subject", "Date"):
        value = msg.get(header)
        if value:
            parts.append(f"{header}: {value}")

    parts.append("")  # Blank line between headers and body

    # Extract body text
    body = msg.get_body(preferencelist=("plain", "html"))
    if body:
        content = body.get_content()
        if isinstance(content, str):
            parts.append(content.strip())

    return "\n".join(parts)

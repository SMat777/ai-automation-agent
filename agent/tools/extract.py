"""Data extraction tool — pulls specific data points from structured text."""

import re


EXTRACT_TOOL = {
    "name": "extract_data",
    "description": (
        "Extract specific data points from text based on a list of fields to look for. "
        "Use this when you need to pull structured information like names, dates, "
        "numbers, or categories from a document."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to extract data from",
            },
            "fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of field names to extract (e.g., ['company_name', 'date', 'amount'])",
            },
        },
        "required": ["text", "fields"],
    },
}


def handle_extract(text: str, fields: list[str]) -> dict:
    """Extract specified data points from text.

    Args:
        text: The text to extract data from.
        fields: List of field names to look for.

    Returns:
        Dictionary mapping field names to extracted values (or None if not found).
    """
    extracted: dict[str, str | None] = {}

    for field in fields:
        # Look for patterns like "Field: Value" or "Field = Value"
        pattern = rf"(?i){re.escape(field)}[\s:=]+(.+?)(?:\n|$)"
        match = re.search(pattern, text)
        extracted[field] = match.group(1).strip() if match else None

    return {
        "extracted": extracted,
        "fields_found": sum(1 for v in extracted.values() if v is not None),
        "fields_missing": sum(1 for v in extracted.values() if v is None),
    }

"""Data extraction tool — pulls structured data from text using multiple strategies."""

from __future__ import annotations

import re


EXTRACT_TOOL = {
    "name": "extract_data",
    "description": (
        "Extract specific data points from text using multiple strategies: "
        "key-value pairs (Field: Value), markdown tables, bulleted/numbered lists, "
        "and pattern matching. Use this when you need to pull structured information "
        "like names, dates, numbers, or categories from a document."
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
                "description": (
                    "List of field names to extract "
                    "(e.g., ['company_name', 'date', 'amount'])"
                ),
            },
            "strategy": {
                "type": "string",
                "enum": ["auto", "key_value", "table", "list"],
                "description": (
                    "Extraction strategy: 'auto' tries all methods, "
                    "'key_value' for Field: Value pairs, "
                    "'table' for markdown tables, "
                    "'list' for bulleted/numbered lists"
                ),
                "default": "auto",
            },
        },
        "required": ["text", "fields"],
    },
}


def handle_extract(
    text: str, fields: list[str], strategy: str = "auto"
) -> dict:
    """Extract specified data points from text using the chosen strategy.

    Args:
        text: The text to extract data from.
        fields: List of field names to look for.
        strategy: Extraction method — 'auto', 'key_value', 'table', or 'list'.

    Returns:
        Dictionary with extracted values, counts, and strategy used.
    """
    strategies = {
        "key_value": _extract_key_value,
        "table": _extract_table,
        "list": _extract_list,
    }

    if strategy == "auto":
        # Try all strategies, merge results (first non-None wins per field)
        extracted: dict[str, str | None] = {f: None for f in fields}
        strategies_used = []

        for name, extractor in strategies.items():
            partial = extractor(text, fields)
            for f in fields:
                if extracted[f] is None and partial.get(f) is not None:
                    extracted[f] = partial[f]
                    if name not in strategies_used:
                        strategies_used.append(name)

        return _build_result(extracted, "auto", strategies_used)

    extractor = strategies.get(strategy)  # type: ignore[assignment]
    if extractor is None:
        return {"error": f"Unknown strategy: {strategy}"}

    extracted = extractor(text, fields)
    return _build_result(extracted, strategy)


def _extract_key_value(text: str, fields: list[str]) -> dict[str, str | None]:
    """Extract from 'Field: Value' or 'Field = Value' patterns."""
    result: dict[str, str | None] = {}

    for f in fields:
        # Try exact match first, then fuzzy
        pattern = rf"(?i)(?:^|\n)\s*{re.escape(f)}\s*[:=]\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text)

        if not match:
            # Try with underscores/hyphens replaced by spaces
            alt_field = f.replace("_", " ").replace("-", " ")
            pattern = rf"(?i)(?:^|\n)\s*{re.escape(alt_field)}\s*[:=]\s*(.+?)(?:\n|$)"
            match = re.search(pattern, text)

        result[f] = match.group(1).strip() if match else None

    return result


def _extract_table(text: str, fields: list[str]) -> dict[str, str | None]:
    """Extract from markdown table format (| Header | Header | ...)."""
    result: dict[str, str | None] = {f: None for f in fields}

    # Find table rows
    rows = re.findall(r"^\|(.+)\|$", text, re.MULTILINE)
    if len(rows) < 2:
        return result

    # Parse header row
    headers = [h.strip().lower() for h in rows[0].split("|")]

    # Skip separator row (|---|---|)
    data_start = 1
    if rows[1].replace("-", "").replace("|", "").replace(" ", "") == "":
        data_start = 2

    # Match fields to columns
    for f in fields:
        f_lower = f.lower().replace("_", " ").replace("-", " ")
        col_idx = None
        for i, h in enumerate(headers):
            if f_lower in h or h in f_lower:
                col_idx = i
                break

        if col_idx is not None:
            for row in rows[data_start:]:
                cells = [c.strip() for c in row.split("|")]
                if col_idx < len(cells) and cells[col_idx]:
                    # Return first non-empty value
                    result[f] = cells[col_idx]
                    break

    return result


def _extract_list(text: str, fields: list[str]) -> dict[str, str | None]:
    """Extract from bulleted or numbered list items."""
    result: dict[str, str | None] = {f: None for f in fields}

    # Find list items (- item, * item, 1. item, 1) item)
    list_items = re.findall(
        r"^[\s]*(?:[-*+]|\d+[.)]\s)\s*(.+)$", text, re.MULTILINE
    )

    for f in fields:
        f_lower = f.lower().replace("_", " ").replace("-", " ")
        for item in list_items:
            item_lower = item.lower()
            # Check if the field name appears in the list item
            if f_lower in item_lower:
                # Try to extract value after colon or dash
                value_match = re.search(r"[:–—-]\s*(.+)$", item)
                if value_match:
                    result[f] = value_match.group(1).strip()
                else:
                    result[f] = item.strip()
                break

    return result


def _build_result(
    extracted: dict[str, str | None],
    strategy: str,
    strategies_used: list[str] | None = None,
) -> dict:
    """Build a standardized extraction result."""
    found = sum(1 for v in extracted.values() if v is not None)
    missing = sum(1 for v in extracted.values() if v is None)

    result: dict = {
        "extracted": extracted,
        "fields_found": found,
        "fields_missing": missing,
        "strategy": strategy,
    }

    if strategies_used:
        result["strategies_used"] = strategies_used

    return result

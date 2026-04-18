"""Document analysis tool — extracts structure, key points, and entities from text."""

from __future__ import annotations

import re

ANALYZE_TOOL = {
    "name": "analyze_document",
    "description": (
        "Analyze a document to extract its structure, key points, entities, "
        "and document type. Use this when you need to understand what a document "
        "contains before extracting specific data from it."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The document text to analyze",
            },
            "focus": {
                "type": "string",
                "description": (
                    "Optional focus area: 'general', 'financial', "
                    "'technical', 'organizational'"
                ),
                "default": "general",
            },
        },
        "required": ["text"],
    },
}


def handle_analyze(text: str, focus: str = "general") -> dict:
    """Analyze document structure, detect type, extract entities and key points.

    Args:
        text: The document text to analyze.
        focus: Optional focus area for the analysis.

    Returns:
        Dictionary with document_type, sections, entities, key_points,
        and statistics.
    """
    return {
        "document_type": _detect_type(text),
        "sections": _extract_sections(text),
        "entities": _extract_entities(text),
        "key_points": _extract_key_points(text),
        "statistics": _compute_stats(text),
        "focus": focus,
    }


def _detect_type(text: str) -> str:
    """Detect the document type based on structural cues."""
    lower = text.lower()

    # Contract / agreement — check first (most specific signals)
    contract_signals = ["agreement", "contract", "parties", "termination", "governing law", "effective date"]
    if sum(1 for kw in contract_signals if kw in lower) >= 2:
        return "contract"
    # Meeting notes
    meeting_signals = ["meeting", "attendees", "agenda", "action items", "minutes", "decisions"]
    if sum(1 for kw in meeting_signals if kw in lower) >= 2:
        return "meeting_notes"
    # Invoice — check before email since invoices often have From:/To: fields
    invoice_signals = ["invoice", "subtotal", "vat", "due date", "payment terms"]
    if sum(1 for kw in invoice_signals if kw in lower) >= 2:
        return "invoice"
    if re.search(r"^(from|to|subject|date):", text, re.MULTILINE | re.IGNORECASE):
        return "email"
    if re.search(r"\|.*\|.*\|", text):
        return "data_table"
    if text.strip().startswith("#") or re.search(r"^#{1,6}\s", text, re.MULTILINE):
        return "markdown_document"
    if re.search(r"^\d+\.\s", text, re.MULTILINE) and len(text.split("\n")) > 5:
        return "report"
    if any(kw in lower for kw in ["abstract", "conclusion", "methodology", "references"]):
        return "academic_paper"
    if any(kw in lower for kw in ["revenue", "profit", "q1", "q2", "fiscal"]):
        return "financial_report"
    return "general_text"


def _extract_sections(text: str) -> list[dict[str, str | int]]:
    """Extract heading hierarchy with nesting level."""
    sections = []
    for match in re.finditer(r"^(#{1,6})\s+(.+)$", text, re.MULTILINE):
        sections.append({
            "level": len(match.group(1)),
            "title": match.group(2).strip(),
        })
    return sections


def _extract_entities(text: str) -> dict[str, list[str]]:
    """Extract named entities: emails, dates, URLs, and potential names."""
    entities: dict[str, list[str]] = {
        "emails": [],
        "dates": [],
        "urls": [],
        "organizations": [],
    }

    # Emails
    entities["emails"] = list(set(re.findall(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text
    )))

    # Dates (various formats)
    date_patterns = [
        r"\d{4}-\d{2}-\d{2}",                    # 2026-04-16
        r"\d{1,2}[./]\d{1,2}[./]\d{2,4}",        # 16/04/2026 or 16.04.26
        r"\d{1,2}\.\s*\w+\s+\d{4}",              # 16. april 2026
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+\d{4}",
    ]
    for pattern in date_patterns:
        entities["dates"].extend(re.findall(pattern, text, re.IGNORECASE))
    entities["dates"] = list(set(entities["dates"]))

    # URLs
    entities["urls"] = list(set(re.findall(
        r"https?://[^\s<>\"')\]]+", text
    )))

    # Organizations (words followed by A/S, Inc, Ltd, etc.)
    org_matches = re.findall(
        r"([A-Z][a-zA-ZæøåÆØÅ]+(?:\s+[A-Z][a-zA-ZæøåÆØÅ]+)*)\s+"
        r"(A/S|ApS|Inc\.?|Ltd\.?|GmbH|Corp\.?|AS|AB)",
        text,
    )
    entities["organizations"] = list(set(
        f"{name} {suffix}" for name, suffix in org_matches
    ))

    return entities


def _extract_key_points(text: str) -> list[str]:
    """Extract the most important sentences/paragraphs as key points."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # Filter out headings-only paragraphs
    content_paragraphs = [
        p for p in paragraphs
        if not p.startswith("#") and len(p.split()) > 3
    ]

    # Return first 5, truncated
    return [
        p[:150] + "..." if len(p) > 150 else p
        for p in content_paragraphs[:5]
    ]


def _compute_stats(text: str) -> dict[str, int]:
    """Compute basic document statistics."""
    words = text.split()
    sentences = re.split(r"[.!?]+", text)
    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    return {
        "word_count": len(words),
        "sentence_count": len([s for s in sentences if s.strip()]),
        "paragraph_count": len(paragraphs),
        "line_count": len(text.splitlines()),
    }

"""Document analysis tool — AI-powered with rule-based fallback.

Uses Claude for intelligent document analysis when api_key is provided.
Falls back to regex/keyword-based analysis for offline or demo use.
"""

from __future__ import annotations

import json
import logging
import re

from anthropic import Anthropic

logger = logging.getLogger(__name__)

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


def handle_analyze(
    text: str,
    focus: str = "general",
    api_key: str | None = None,
    **_kwargs: object,
) -> dict:
    """Analyze document structure, detect type, extract entities and key points.

    Uses Claude when api_key is provided for intelligent analysis.
    Falls back to regex/keyword-based analysis without api_key.

    Args:
        text: The document text to analyze.
        focus: Optional focus area for the analysis.
        api_key: Anthropic API key. If None, uses rule-based fallback.

    Returns:
        Dictionary with document_type, sections, entities, key_points,
        statistics, and method used.
    """
    # Regex-based features always run (cheap and reliable)
    entities = _extract_entities(text)
    sections = _extract_sections(text)
    statistics = _compute_stats(text)

    if api_key:
        try:
            ai_result = _ai_analyze(text, focus, api_key)
            return {
                "document_type": ai_result.get("document_type", _detect_type(text)),
                "sections": sections,
                "entities": entities,
                "key_points": ai_result.get("key_points", _extract_key_points(text)),
                "summary": ai_result.get("summary", ""),
                "statistics": statistics,
                "focus": focus,
                "method": "ai",
            }
        except Exception as e:
            logger.warning("AI analysis failed, falling back to rule-based: %s", e)

    return {
        "document_type": _detect_type(text),
        "sections": sections,
        "entities": entities,
        "key_points": _extract_key_points(text),
        "statistics": statistics,
        "focus": focus,
        "method": "rule_based",
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


# ── AI-powered analysis ─────────────────────────────────────────────────────


def _ai_analyze(text: str, focus: str, api_key: str) -> dict:
    """Use Claude to analyze a document intelligently.

    Returns a dict with document_type, key_points, and summary.
    """
    client = Anthropic(api_key=api_key)

    # Truncate very long documents to avoid excessive token usage
    truncated = text[:10_000] if len(text) > 10_000 else text

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Analyze this document with focus on '{focus}'. "
                    "Return a JSON object with these fields:\n"
                    '- "document_type": one of "contract", "meeting_notes", "invoice", '
                    '"email", "report", "academic_paper", "financial_report", '
                    '"markdown_document", "data_table", "general_text"\n'
                    '- "key_points": array of 3-5 key insights from the document\n'
                    '- "summary": one paragraph summary\n\n'
                    "Return ONLY valid JSON, no markdown formatting.\n\n"
                    f"Document:\n{truncated}"
                ),
            }
        ],
    )

    block = response.content[0]
    raw = block.text if hasattr(block, "text") else str(block)

    # Strip markdown code fences if Claude wraps the JSON
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    return json.loads(cleaned)  # type: ignore[no-any-return]

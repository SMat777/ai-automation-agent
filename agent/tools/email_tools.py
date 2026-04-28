"""Email processing tools — classify intent and draft replies.

These tools enable the agent to function as an email triage system:
1. classify_email — detect category, priority, and intent
2. draft_email_reply — generate a professional response
"""

from __future__ import annotations

import re
from typing import Any

EMAIL_CLASSIFY_TOOL = {
    "name": "classify_email",
    "description": (
        "Classify an incoming email by category, priority, and intent. "
        "Use this to triage emails before deciding how to respond. "
        "Categories: order_inquiry, complaint, general, technical, billing."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "email_text": {
                "type": "string",
                "description": "The full email text including headers if available",
            },
        },
        "required": ["email_text"],
    },
}

EMAIL_DRAFT_TOOL = {
    "name": "draft_email_reply",
    "description": (
        "Draft a professional email reply based on context and classification. "
        "The draft should be ready for human review before sending."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "context": {
                "type": "string",
                "description": "Summary of the situation and what to address in the reply",
            },
            "tone": {
                "type": "string",
                "description": "Tone: 'professional', 'empathetic', 'formal'",
                "default": "professional",
            },
            "include_order_info": {
                "type": "boolean",
                "description": "Whether to include order status information",
                "default": False,
            },
        },
        "required": ["context"],
    },
}

# Keyword-based classification (no API needed — runs offline)
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "order_inquiry": ["order", "status", "shipped", "delivery", "tracking", "shipment"],
    "complaint": ["disappointed", "unacceptable", "damaged", "broken", "terrible", "refund", "worst"],
    "billing": ["invoice", "payment", "charge", "billing", "receipt", "price"],
    "technical": ["error", "bug", "not working", "crash", "issue", "problem", "login"],
}

_HIGH_PRIORITY_SIGNALS = [
    "urgent", "asap", "immediately", "unacceptable", "disappointed",
    "complaint", "damaged", "legal", "lawyer", "refund",
]


def handle_classify_email(params: dict[str, Any]) -> dict[str, Any]:
    """Classify an email by category, priority, and intent."""
    text = params.get("email_text")
    if not text:
        return {"error": "Missing required parameter: email_text"}

    lower = text.lower()

    # Detect category
    category = "general"
    category_scores: dict[str, int] = {}
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            category_scores[cat] = score

    if category_scores:
        category = max(category_scores, key=category_scores.get)  # type: ignore[arg-type]

    # Detect priority
    high_signals = sum(1 for s in _HIGH_PRIORITY_SIGNALS if s in lower)
    priority = "high" if high_signals >= 1 else "medium" if len(text) > 200 else "low"

    # Detect intent
    intent = _detect_intent(lower)

    # Extract entities
    entities = _extract_email_entities(text)

    return {
        "category": category,
        "priority": priority,
        "intent": intent,
        "entities": entities,
        "confidence": min(0.95, 0.5 + (len(category_scores) * 0.15)),
    }


def handle_draft_email(params: dict[str, Any]) -> dict[str, Any]:
    """Draft a professional email reply."""
    context = params.get("context")
    if not context:
        return {"error": "Missing required parameter: context"}

    tone = params.get("tone", "professional")

    greeting = "Dear valued customer,"
    if tone == "empathetic":
        greeting = "Dear customer,"
    elif tone == "formal":
        greeting = "Dear Sir/Madam,"

    # Build draft based on context
    draft_parts = [
        greeting,
        "",
        "Thank you for reaching out to us.",
        "",
        f"Regarding your inquiry: {context}",
        "",
        "Please don't hesitate to contact us if you need any further assistance.",
        "",
        "Best regards,",
        "Customer Support Team",
    ]

    return {
        "draft": "\n".join(draft_parts),
        "tone": tone,
        "needs_review": True,
        "note": "This draft should be reviewed by a human before sending.",
    }


def _detect_intent(text: str) -> str:
    """Detect the primary intent of the email."""
    if any(w in text for w in ["status", "where is", "tracking", "when will"]):
        return "status_check"
    if any(w in text for w in ["cancel", "refund", "return"]):
        return "cancellation"
    if any(w in text for w in ["complaint", "disappointed", "unacceptable"]):
        return "complaint"
    if any(w in text for w in ["question", "how to", "can i", "is it possible"]):
        return "question"
    if any(w in text for w in ["order", "purchase", "buy"]):
        return "new_order"
    return "general"


def _extract_email_entities(text: str) -> dict[str, list[str]]:
    """Extract key entities from email text."""
    entities: dict[str, list[str]] = {}

    # Order numbers
    orders = re.findall(r"#?\d{4,6}", text)
    if orders:
        entities["order_numbers"] = orders

    # Email addresses
    emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    if emails:
        entities["emails"] = emails

    # Names (simple: "Dr. X" or "Dear X")
    names = re.findall(r"(?:Dr\.|Mr\.|Mrs\.|Ms\.)\s+\w+", text)
    if names:
        entities["names"] = names

    return entities

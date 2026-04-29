"""Email processing tools — AI-powered with rule-based fallback.

These tools enable the agent to function as an email triage system:
1. classify_email — AI-powered classification with keyword fallback
2. draft_email_reply — AI-generated replies with template fallback
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from anthropic import Anthropic

logger = logging.getLogger(__name__)

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


def handle_classify_email(
    email_text: str | None = None,
    api_key: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Classify an email by category, priority, and intent.

    Uses Claude when api_key is provided for intelligent classification.
    Falls back to keyword-based scoring without api_key.

    Supports both direct keyword arguments (agent dispatch path) and the
    legacy dict-based call style used in older tests/helpers.
    """
    # Backward compatibility: allow handle_classify_email({"email_text": ...})
    if isinstance(email_text, dict):
        params = email_text
        email_text = params.get("email_text")
        api_key = params.get("api_key", api_key)

    # Extra fallback for callers that pass a "params" kwarg explicitly
    if not email_text and isinstance(kwargs.get("params"), dict):
        email_text = kwargs["params"].get("email_text")

    text = email_text
    if not text:
        return {"error": "Missing required parameter: email_text"}

    # AI path
    if api_key:
        try:
            ai_result = _ai_classify(text, api_key)
            # Always include entities from regex (cheap and reliable)
            ai_result["entities"] = _extract_email_entities(text)
            ai_result["method"] = "ai"
            return ai_result
        except Exception as e:
            logger.warning("AI classification failed, falling back: %s", e)

    # Rule-based fallback
    lower = text.lower()

    category = "general"
    category_scores: dict[str, int] = {}
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            category_scores[cat] = score

    if category_scores:
        category = max(category_scores, key=category_scores.get)  # type: ignore[arg-type]

    high_signals = sum(1 for s in _HIGH_PRIORITY_SIGNALS if s in lower)
    priority = "high" if high_signals >= 1 else "medium" if len(text) > 200 else "low"

    intent = _detect_intent(lower)
    entities = _extract_email_entities(text)

    return {
        "category": category,
        "priority": priority,
        "intent": intent,
        "entities": entities,
        "confidence": min(0.95, 0.5 + (len(category_scores) * 0.15)),
        "method": "rule_based",
    }


def handle_draft_email(
    context: str | None = None,
    tone: str = "professional",
    include_order_info: bool = False,
    api_key: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Draft a professional email reply.

    Uses Claude when api_key is provided for context-aware drafting.
    Falls back to template-based drafting without api_key.

    Supports both direct keyword arguments (agent dispatch path) and the
    legacy dict-based call style used in older tests/helpers.
    """
    # Backward compatibility: allow handle_draft_email({"context": ...})
    if isinstance(context, dict):
        params = context
        context = params.get("context")
        tone = params.get("tone", tone)
        include_order_info = params.get("include_order_info", include_order_info)
        api_key = params.get("api_key", api_key)

    # Extra fallback for callers that pass a "params" kwarg explicitly
    if not context and isinstance(kwargs.get("params"), dict):
        params = kwargs["params"]
        context = params.get("context")
        tone = params.get("tone", tone)
        include_order_info = params.get("include_order_info", include_order_info)

    if not context:
        return {"error": "Missing required parameter: context"}

    # AI path
    if api_key:
        try:
            draft = _ai_draft(context, tone, include_order_info, api_key)
            return {
                "draft": draft,
                "tone": tone,
                "needs_review": True,
                "method": "ai",
                "note": "AI-generated draft — review before sending.",
            }
        except Exception as e:
            logger.warning("AI drafting failed, falling back to template: %s", e)

    # Template fallback
    greeting = "Dear valued customer,"
    if tone == "empathetic":
        greeting = "Dear customer,"
    elif tone == "formal":
        greeting = "Dear Sir/Madam,"

    draft_parts = [
        greeting,
        "",
        "Thank you for reaching out to us.",
        "",
        f"Regarding your inquiry: {context}",
    ]

    if include_order_info:
        draft_parts.extend([
            "",
            "We have included the latest available order information above for your review.",
        ])

    draft_parts.extend([
        "",
        "Please don't hesitate to contact us if you need any further assistance.",
        "",
        "Best regards,",
        "Customer Support Team",
    ])

    return {
        "draft": "\n".join(draft_parts),
        "tone": tone,
        "needs_review": True,
        "method": "template",
        "note": "This draft should be reviewed by a human before sending.",
    }


# ── AI-powered functions ──────────────────────────────────────────────────────


def _ai_classify(email_text: str, api_key: str) -> dict[str, Any]:
    """Use Claude to classify an email with genuine understanding."""
    client = Anthropic(api_key=api_key)

    truncated = email_text[:5_000] if len(email_text) > 5_000 else email_text

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    "Classify this email. Return a JSON object with:\n"
                    '- "category": one of "order_inquiry", "complaint", '
                    '"billing", "technical", "general"\n'
                    '- "priority": "high", "medium", or "low"\n'
                    '- "intent": the primary intent in snake_case\n'
                    '- "confidence": 0.0-1.0\n'
                    '- "reasoning": one sentence explaining the classification\n\n'
                    "Return ONLY valid JSON.\n\n"
                    f"Email:\n{truncated}"
                ),
            }
        ],
    )

    block = response.content[0]
    raw = block.text if hasattr(block, "text") else str(block)

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    return json.loads(cleaned)  # type: ignore[no-any-return]


def _ai_draft(
    context: str, tone: str, include_order_info: bool, api_key: str
) -> str:
    """Use Claude to draft a context-aware email reply."""
    client = Anthropic(api_key=api_key)

    order_instruction = (
        " Include relevant order information in the reply."
        if include_order_info
        else ""
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Draft a {tone} email reply for the following situation:\n\n"
                    f"{context}\n\n"
                    f"Tone: {tone}.{order_instruction}\n"
                    "Write ONLY the email text — no JSON, no explanation. "
                    "Keep it concise and professional."
                ),
            }
        ],
    )

    block = response.content[0]
    return block.text if hasattr(block, "text") else str(block)


# ── Rule-based helpers ────────────────────────────────────────────────────────


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

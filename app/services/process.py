"""Document processing pipeline.

Orchestrates the four-step flow: analyze → extract → summarize → validate.
Kept out of the router so that HTTP concerns and business logic remain separate,
and so that this code can later be called from a background job, the agent's
tool layer, or a CLI.
"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime
from typing import Any

from agent.tools.analyze import handle_analyze
from agent.tools.extract import handle_extract
from agent.tools.summarize import handle_summarize


# ── Public orchestrator ──────────────────────────────────────────────────────


def run_process_pipeline(text: str, document_type: str = "auto") -> dict[str, Any]:
    """Run the full document processing pipeline and return a structured result.

    The response shape matches what the frontend expects:
    steps, document_type, total_duration_ms, confidence, fields_extracted,
    entities_found, validation_errors, erp_output.
    """
    steps: list[dict] = []
    total_start = time.perf_counter()

    # Step 1: Analyze
    step_start = time.perf_counter()
    analysis = handle_analyze(text, focus="general")
    steps.append({
        "name": "analyze",
        "status": "done",
        "duration_ms": round((time.perf_counter() - step_start) * 1000),
        "data": analysis,
    })

    # Determine fields to extract based on detected document type
    doc_type = document_type if document_type != "auto" else analysis["document_type"]
    fields = _fields_for_type(doc_type)

    # Step 2: Extract
    step_start = time.perf_counter()
    extraction = handle_extract(text, fields=fields, strategy="auto")
    steps.append({
        "name": "extract",
        "status": "done",
        "duration_ms": round((time.perf_counter() - step_start) * 1000),
        "data": extraction,
    })

    # Step 3: Summarize (AI if available, extractive fallback)
    step_start = time.perf_counter()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    summary = handle_summarize(text, format="bullets", max_points=5, api_key=api_key)
    smart_summary = _build_smart_summary(doc_type, extraction["extracted"], analysis)
    if smart_summary:
        summary["smart_summary"] = smart_summary
    steps.append({
        "name": "summarize",
        "status": "done",
        "duration_ms": round((time.perf_counter() - step_start) * 1000),
        "data": summary,
    })

    # Step 4: Validate
    step_start = time.perf_counter()
    validation = _validate_document(doc_type, extraction["extracted"], analysis)
    steps.append({
        "name": "validate",
        "status": "done",
        "duration_ms": round((time.perf_counter() - step_start) * 1000),
        "data": {"issues": validation},
    })

    total_ms = round((time.perf_counter() - total_start) * 1000)

    # Confidence score (weighted heuristic)
    entity_count = sum(len(v) for v in analysis["entities"].values())
    total_fields = extraction["fields_found"] + extraction["fields_missing"]
    extraction_rate = extraction["fields_found"] / max(total_fields, 1)
    has_structure = len(analysis["sections"]) > 0
    type_confident = doc_type != "general_text"
    error_count = sum(1 for v in validation if v["severity"] == "error")

    confidence = round(
        (0.25 * min(entity_count / 3, 1.0))
        + (0.35 * extraction_rate)
        + (0.10 * (1.0 if has_structure else 0.3))
        + (0.15 * (1.0 if type_confident else 0.4))
        + (0.15 * (1.0 if error_count == 0 else 0.0)),
        2,
    )

    # ERP-ready structured output
    erp_output = {
        "document_type": doc_type,
        "extracted_fields": {k: v for k, v in extraction["extracted"].items() if v is not None},
        "entities": {k: v for k, v in analysis["entities"].items() if v},
        "confidence_score": confidence,
        "validation_passed": error_count == 0,
        "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    return {
        "steps": steps,
        "document_type": doc_type,
        "total_duration_ms": total_ms,
        "confidence": confidence,
        "fields_extracted": f"{extraction['fields_found']}/{total_fields}",
        "entities_found": entity_count,
        "validation_errors": error_count,
        "erp_output": erp_output,
    }


# ── Helpers: field selection, summary shaping, validation ────────────────────


def _fields_for_type(doc_type: str) -> list[str]:
    """Return relevant extraction fields based on document type."""
    field_map: dict[str, list[str]] = {
        "invoice": ["Invoice Date", "Due Date", "Subtotal", "VAT", "Total", "From", "To", "Reference"],
        "contract": ["Parties", "Effective Date", "Duration", "Value", "Governing Law"],
        "report": ["Author", "Date", "Department", "Status", "Deadline"],
        "meeting_notes": ["Date", "Attendees", "Decisions", "Action Items", "Next Meeting"],
        "email": ["From", "To", "Subject", "Date"],
        "financial_report": ["Revenue", "Profit", "Period", "Growth"],
        "data_table": ["Name", "Date", "Value", "Status"],
        "markdown_document": ["Author", "Date", "Title", "Status"],
        "academic_paper": ["Author", "Title", "Abstract", "Date"],
    }
    return field_map.get(doc_type, ["Date", "Author", "Title", "Status", "Summary"])


def _build_smart_summary(
    doc_type: str, extracted: dict[str, str | None], analysis: dict
) -> str | None:
    """Build a human-readable business summary from extracted data."""

    def _get(*keys: str) -> str | None:
        for k in keys:
            val = extracted.get(k)
            if val:
                return val
        return None

    if doc_type == "invoice":
        sender = _get("From") or "unknown sender"
        recipient = _get("To") or "unknown recipient"
        total = _get("Total") or "unknown amount"
        due = _get("Due Date")
        ref = _get("Reference")
        parts = [f"Invoice from {sender} to {recipient} for {total}"]
        if due:
            parts[0] += f", due {due}"
        parts[0] += "."
        if ref:
            parts.append(f"Reference: {ref}.")
        orgs = analysis.get("entities", {}).get("organizations", [])
        if orgs:
            parts.append(f"Parties: {', '.join(orgs)}.")
        return " ".join(parts)

    if doc_type == "contract":
        parties = _get("Parties")
        effective = _get("Effective Date")
        duration = _get("Duration")
        value = _get("Value")
        law = _get("Governing Law")
        parts = ["Service agreement"]
        if effective:
            parts[0] += f" effective {effective}"
        if duration:
            parts[0] += f" for {duration}"
        parts[0] += "."
        if parties:
            parts.append(f"Parties: {parties}.")
        if value:
            parts.append(f"Value: {value}.")
        if law:
            parts.append(f"Governed by {law}.")
        return " ".join(parts)

    if doc_type == "meeting_notes":
        date = _get("Date")
        attendees = _get("Attendees")
        actions = _get("Action Items")
        next_meeting = _get("Next Meeting")
        parts = ["Meeting"]
        if date:
            parts[0] += f" on {date}"
        if attendees:
            parts[0] += f" with {attendees}"
        parts[0] += "."
        if actions:
            parts.append(f"Action items: {actions}.")
        if next_meeting:
            parts.append(f"Next meeting: {next_meeting}.")
        return " ".join(parts)

    if doc_type == "email":
        sender = _get("From")
        subject = _get("Subject")
        date = _get("Date")
        parts: list[str] = []
        if sender and subject:
            parts.append(f'Email from {sender} regarding "{subject}"')
        elif sender:
            parts.append(f"Email from {sender}")
        if date and parts:
            parts[-1] += f" on {date}"
        if parts:
            parts[-1] += "."
        return " ".join(parts) if parts else None

    return None


def _validate_document(
    doc_type: str, extracted: dict[str, str | None], analysis: dict
) -> list[dict[str, str]]:
    """Validate extracted data and flag potential issues."""
    issues: list[dict[str, str]] = []

    if doc_type == "invoice":
        issues.extend(_validate_invoice(extracted))

    elif doc_type == "contract":
        effective = _parse_date(extracted.get("Effective Date"))
        if effective and effective < datetime.now():
            issues.append({
                "severity": "warning",
                "field": "Effective Date",
                "message": "Contract effective date is in the past",
            })
        if not extracted.get("Governing Law"):
            issues.append({
                "severity": "warning",
                "field": "Governing Law",
                "message": "No governing law specified — may cause legal ambiguity",
            })

    elif doc_type == "meeting_notes":
        if not extracted.get("Action Items"):
            issues.append({
                "severity": "warning",
                "field": "Action Items",
                "message": "No action items identified — meeting may lack follow-up",
            })
        if not extracted.get("Next Meeting"):
            issues.append({
                "severity": "info",
                "field": "Next Meeting",
                "message": "No next meeting date specified",
            })

    # Universal: missing critical fields
    missing = [k for k, v in extracted.items() if v is None]
    if missing:
        issues.append({
            "severity": "warning",
            "field": "Coverage",
            "message": f"{len(missing)} field(s) could not be extracted: {', '.join(missing)}",
        })

    return issues


def _validate_invoice(extracted: dict[str, str | None]) -> list[dict[str, str]]:
    """Invoice-specific validation: date consistency + VAT arithmetic."""
    issues: list[dict[str, str]] = []

    inv_date = _parse_date(extracted.get("Invoice Date"))
    due_date = _parse_date(extracted.get("Due Date"))
    if inv_date and due_date:
        if due_date < inv_date:
            issues.append({
                "severity": "error",
                "field": "Due Date",
                "message": f"Due date ({extracted['Due Date']}) is before invoice date ({extracted['Invoice Date']})",
            })
        elif due_date == inv_date:
            issues.append({
                "severity": "warning",
                "field": "Due Date",
                "message": "Due date is the same as invoice date — payment due immediately",
            })
        else:
            days = (due_date - inv_date).days
            issues.append({
                "severity": "info",
                "field": "Payment Terms",
                "message": f"Net {days} days payment window",
            })

    subtotal = _parse_amount(extracted.get("Subtotal"))
    vat = _parse_amount(extracted.get("VAT"))
    total = _parse_amount(extracted.get("Total"))
    if subtotal and vat:
        expected_rate = round(vat / subtotal * 100)
        issues.append({
            "severity": "info",
            "field": "VAT",
            "message": f"Effective VAT rate: {expected_rate}%",
        })
    if subtotal and vat and total:
        expected_total = subtotal + vat
        if abs(expected_total - total) < 1:
            issues.append({
                "severity": "pass",
                "field": "Total",
                "message": "Total matches subtotal + VAT ✓",
            })
        else:
            issues.append({
                "severity": "error",
                "field": "Total",
                "message": f"Total ({total:,.0f}) doesn't match subtotal + VAT ({expected_total:,.0f})",
            })

    return issues


def _parse_date(val: str | None) -> datetime | None:
    """Parse a date string in one of several common formats."""
    if not val:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(val.strip(), fmt)
        except ValueError:
            continue
    return None


def _parse_amount(val: str | None) -> float | None:
    """Parse a monetary amount, handling Danish-style thousand separators."""
    if not val:
        return None
    cleaned = re.sub(r"[^\d.,]", "", val).replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None

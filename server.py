"""FastAPI server — exposes AI agent tools as a REST API with web frontend."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent.tools.analyze import handle_analyze
from agent.tools.extract import handle_extract
from agent.tools.summarize import handle_summarize
from agent.tools.pipeline import handle_run_pipeline, AVAILABLE_PIPELINES

load_dotenv()

app = FastAPI(
    title="AI Automation Agent",
    description="AI-powered document analysis, data extraction, and automation pipelines",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response models ──────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Document text to analyze")
    focus: str = Field("general", description="Focus area: general, financial, technical, organizational")


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to extract data from")
    fields: list[str] = Field(..., min_length=1, description="Field names to extract")
    strategy: str = Field("auto", description="Strategy: auto, key_value, table, list")


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to summarize")
    format: str = Field("bullets", description="Output format: bullets or paragraph")
    max_points: int = Field(5, ge=1, le=20, description="Max bullet points")


class ProcessRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Document text to process")
    document_type: str = Field("auto", description="Document type hint: auto, invoice, contract, report, meeting_notes")


class PipelineRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Description of the pipeline task")
    pipeline: str = Field("posts", description="Pipeline to run: posts or github")


class ToolResponse(BaseModel):
    success: bool
    data: dict[str, Any]


# ── API endpoints ────────────────────────────────────────────────────────────


@app.get("/api/health")
def health() -> dict:
    """Health check endpoint."""
    api_key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
    return {
        "status": "ok",
        "api_key_configured": api_key_set,
        "available_tools": ["analyze", "extract", "summarize", "process", "pipeline"],
        "available_pipelines": list(AVAILABLE_PIPELINES.keys()),
    }


@app.post("/api/analyze", response_model=ToolResponse)
def analyze(req: AnalyzeRequest) -> ToolResponse:
    """Analyze a document — detect type, extract entities, key points, stats."""
    result = handle_analyze(req.text, focus=req.focus)
    return ToolResponse(success=True, data=result)


@app.post("/api/extract", response_model=ToolResponse)
def extract(req: ExtractRequest) -> ToolResponse:
    """Extract structured data from text using key-value, table, or list strategies."""
    result = handle_extract(req.text, fields=req.fields, strategy=req.strategy)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ToolResponse(success=True, data=result)


@app.post("/api/summarize", response_model=ToolResponse)
def summarize(req: SummarizeRequest) -> ToolResponse:
    """Summarize text. Uses AI when API key is configured, otherwise extractive."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    result = handle_summarize(
        req.text,
        format=req.format,
        max_points=req.max_points,
        api_key=api_key,
    )
    return ToolResponse(success=True, data=result)


@app.post("/api/process", response_model=ToolResponse)
def process(req: ProcessRequest) -> ToolResponse:
    """Run full document processing pipeline: analyze → extract → summarize."""
    import time

    steps: list[dict] = []
    total_start = time.perf_counter()

    # Step 1: Analyze
    step_start = time.perf_counter()
    analysis = handle_analyze(req.text, focus="general")
    step_ms = round((time.perf_counter() - step_start) * 1000)
    steps.append({"name": "analyze", "status": "done", "duration_ms": step_ms, "data": analysis})

    # Determine fields to extract based on detected document type
    doc_type = req.document_type if req.document_type != "auto" else analysis["document_type"]
    fields = _fields_for_type(doc_type)

    # Step 2: Extract
    step_start = time.perf_counter()
    extraction = handle_extract(req.text, fields=fields, strategy="auto")
    step_ms = round((time.perf_counter() - step_start) * 1000)
    steps.append({"name": "extract", "status": "done", "duration_ms": step_ms, "data": extraction})

    # Step 3: Summarize (smart template + extractive fallback)
    step_start = time.perf_counter()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    summary = handle_summarize(req.text, format="bullets", max_points=5, api_key=api_key)

    # Generate structured business summary from extracted data
    smart_summary = _build_smart_summary(doc_type, extraction["extracted"], analysis)
    if smart_summary:
        summary["smart_summary"] = smart_summary

    step_ms = round((time.perf_counter() - step_start) * 1000)
    steps.append({"name": "summarize", "status": "done", "duration_ms": step_ms, "data": summary})

    # Step 4: Validate
    step_start = time.perf_counter()
    validation = _validate_document(doc_type, extraction["extracted"], analysis)
    step_ms = round((time.perf_counter() - step_start) * 1000)
    steps.append({"name": "validate", "status": "done", "duration_ms": step_ms, "data": {"issues": validation}})

    total_ms = round((time.perf_counter() - total_start) * 1000)

    # Compute overall confidence score
    entity_count = sum(len(v) for v in analysis["entities"].values())
    extraction_rate = extraction["fields_found"] / max(extraction["fields_found"] + extraction["fields_missing"], 1)
    has_structure = len(analysis["sections"]) > 0
    type_confident = doc_type not in ("general_text",)
    error_count = sum(1 for v in validation if v["severity"] == "error")

    confidence = round(
        (0.25 * min(entity_count / 3, 1.0))
        + (0.35 * extraction_rate)
        + (0.1 * (1.0 if has_structure else 0.3))
        + (0.15 * (1.0 if type_confident else 0.4))
        + (0.15 * (1.0 if error_count == 0 else 0.0))
    , 2)

    # Build ERP-ready structured output
    erp_output = {
        "document_type": doc_type,
        "extracted_fields": {k: v for k, v in extraction["extracted"].items() if v is not None},
        "entities": {
            k: v for k, v in analysis["entities"].items() if v
        },
        "confidence_score": confidence,
        "validation_passed": error_count == 0,
        "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    return ToolResponse(success=True, data={
        "steps": steps,
        "document_type": doc_type,
        "total_duration_ms": total_ms,
        "confidence": confidence,
        "fields_extracted": f"{extraction['fields_found']}/{extraction['fields_found'] + extraction['fields_missing']}",
        "entities_found": entity_count,
        "validation_errors": error_count,
        "erp_output": erp_output,
    })


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
        # Add line item count if table detected
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
        parts = []
        if sender and subject:
            parts.append(f"Email from {sender} regarding \"{subject}\"")
        elif sender:
            parts.append(f"Email from {sender}")
        if date:
            parts[-1] += f" on {date}" if parts else ""
        if parts:
            parts[-1] += "."
        return " ".join(parts) if parts else None

    return None


def _validate_document(
    doc_type: str, extracted: dict[str, str | None], analysis: dict
) -> list[dict[str, str]]:
    """Validate extracted data and flag potential issues."""
    import re
    from datetime import datetime

    issues: list[dict[str, str]] = []

    def _parse_date(val: str | None) -> datetime | None:
        if not val:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(val.strip(), fmt)
            except ValueError:
                continue
        return None

    def _parse_amount(val: str | None) -> float | None:
        if not val:
            return None
        cleaned = re.sub(r"[^\d.,]", "", val).replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    if doc_type == "invoice":
        # Check: due date after invoice date
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

        # Check: VAT vs Total consistency
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

    elif doc_type == "contract":
        effective = _parse_date(extracted.get("Effective Date"))
        if effective:
            from datetime import datetime as dt
            if effective < dt.now():
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

    # Universal: check for missing critical fields
    missing = [k for k, v in extracted.items() if v is None]
    if missing:
        issues.append({
            "severity": "warning",
            "field": "Coverage",
            "message": f"{len(missing)} field(s) could not be extracted: {', '.join(missing)}",
        })

    return issues


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


@app.post("/api/pipeline", response_model=ToolResponse)
def pipeline(req: PipelineRequest) -> ToolResponse:
    """Run a data pipeline (posts or github) and return results."""
    result = handle_run_pipeline(task=req.task, pipeline=req.pipeline)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ToolResponse(success=True, data=result)


# ── Frontend ─────────────────────────────────────────────────────────────────


app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def serve_frontend() -> FileResponse:
    """Serve the web frontend."""
    return FileResponse("frontend/index.html")

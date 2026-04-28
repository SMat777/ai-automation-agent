"""Document processing endpoint — chains analyze, extract, summarize, validate."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ToolResponse
from app.services.process import run_process_pipeline
from app.services.run_tracker import track_run

router = APIRouter(tags=["tools"])


class ProcessRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Document text to process")
    document_type: str = Field(
        "auto",
        description="Document type hint: auto, invoice, contract, report, meeting_notes",
    )


@router.post("/process", response_model=ToolResponse)
def process(
    req: ProcessRequest,
    db: Session = Depends(get_db),
) -> ToolResponse:
    """Run full document processing pipeline: analyze → extract → summarize → validate."""
    with track_run(db, tool_name="process", input_payload=req.model_dump()) as tr:
        result = run_process_pipeline(req.text, document_type=req.document_type)
        tr.output = result
    return ToolResponse(success=True, data=result)

"""Data extraction endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agent.tools.extract import handle_extract
from app.db import get_db
from app.schemas import ToolResponse
from app.services.run_tracker import track_run

router = APIRouter(tags=["tools"])


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to extract data from")
    fields: list[str] = Field(..., min_length=1, description="Field names to extract")
    strategy: str = Field("auto", description="Strategy: auto, key_value, table, list")


@router.post("/extract", response_model=ToolResponse)
def extract(
    req: ExtractRequest,
    db: Session = Depends(get_db),
) -> ToolResponse:
    """Extract structured data from text using key-value, table, or list strategies."""
    with track_run(db, tool_name="extract", input_payload=req.model_dump()) as tr:
        result = handle_extract(req.text, fields=req.fields, strategy=req.strategy)
        if "error" in result:
            # Record the error in the run log, then surface a 400.
            tr.output = {"error": result["error"]}
            raise HTTPException(status_code=400, detail=result["error"])
        tr.output = result
    return ToolResponse(success=True, data=result)

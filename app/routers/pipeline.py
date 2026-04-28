"""Pipeline endpoint — runs TypeScript automation pipelines."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agent.tools.pipeline import handle_run_pipeline
from app.db import get_db
from app.schemas import ToolResponse
from app.services.run_tracker import track_run

router = APIRouter(tags=["tools"])


class PipelineRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Description of the pipeline task")
    pipeline: str = Field("posts", description="Pipeline to run: posts or github")


@router.post("/pipeline", response_model=ToolResponse)
def pipeline(
    req: PipelineRequest,
    db: Session = Depends(get_db),
) -> ToolResponse:
    """Run a data pipeline (posts or github) and return results."""
    with track_run(db, tool_name="pipeline", input_payload=req.model_dump()) as tr:
        result = handle_run_pipeline(task=req.task, pipeline=req.pipeline)
        if "error" in result:
            tr.output = {"error": result["error"]}
            raise HTTPException(status_code=400, detail=result["error"])
        tr.output = result
    return ToolResponse(success=True, data=result)

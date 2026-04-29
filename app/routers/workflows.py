"""Workflow CRUD and execution endpoints.

Provides API access to the workflow engine — listing, creating, running
and deleting workflow definitions. Preset workflows (seeded on startup)
cannot be deleted.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agent.tools import TOOL_HANDLERS
from app.db import get_db
from app.models.workflow import Workflow, WorkflowStep
from app.schemas import ToolResponse
from app.services.run_tracker import track_run
from app.services.workflow.engine import WorkflowEngine

router = APIRouter(prefix="/api", tags=["workflows"])

# Single engine instance — stateless, so safe to share.
_engine = WorkflowEngine(tool_handlers=TOOL_HANDLERS)  # type: ignore[arg-type]


# ── Request schemas ──────────────────────────────────────────────────────────


class StepCreate(BaseModel):
    step_id: str = Field(..., min_length=1, description="Unique step identifier")
    tool_name: str = Field(..., min_length=1, description="Tool to invoke")
    input_template: dict[str, Any] = Field(
        default_factory=dict,
        description="Input template with optional $-variable references",
    )


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Workflow name")
    description: str = Field(default="", max_length=500, description="Workflow description")
    on_error: str = Field(default="stop", description="Error strategy: stop or skip")
    steps: list[StepCreate] = Field(..., min_length=1, description="Ordered list of steps")


class WorkflowRunRequest(BaseModel):
    input: dict[str, Any] = Field(
        default_factory=dict,
        description="Input data passed to the workflow as $input",
    )


# ── Helpers ──────────────────────────────────────────────────────────────────


def _workflow_to_definition(workflow: Workflow) -> dict[str, Any]:
    """Convert a DB Workflow into the dict format the engine expects."""
    return {
        "steps": [
            {
                "step_id": step.step_id,
                "tool_name": step.tool_name,
                "input_template": step.input_template,
            }
            for step in workflow.steps
        ],
        "on_error": workflow.on_error,
    }


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/workflows")
def list_workflows(db: Session = Depends(get_db)) -> dict[str, Any]:
    """List all workflow definitions."""
    workflows = db.query(Workflow).order_by(Workflow.id).all()
    return {"workflows": [w.to_dict() for w in workflows]}


@router.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get a specific workflow definition with its steps."""
    workflow = db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    return workflow.to_dict()


@router.post("/workflows", status_code=201)
def create_workflow(
    req: WorkflowCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create a new workflow definition."""
    # Validate the definition before persisting
    definition = {
        "steps": [s.model_dump() for s in req.steps],
        "on_error": req.on_error,
    }
    errors = _engine.validate(definition)
    if errors:
        raise HTTPException(status_code=422, detail={"validation_errors": errors})

    workflow = Workflow(
        name=req.name,
        description=req.description,
        on_error=req.on_error,
        is_preset=False,
    )
    for i, step in enumerate(req.steps):
        workflow.steps.append(
            WorkflowStep(
                step_order=i,
                step_id=step.step_id,
                tool_name=step.tool_name,
                input_template=step.input_template,
            )
        )

    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow.to_dict()


@router.delete("/workflows/{workflow_id}", status_code=204)
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a user-created workflow. Preset workflows cannot be deleted."""
    workflow = db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    if workflow.is_preset:
        raise HTTPException(status_code=403, detail="Preset workflows cannot be deleted")

    db.delete(workflow)
    db.commit()


@router.post("/workflows/{workflow_id}/run", response_model=ToolResponse)
def run_workflow(
    workflow_id: int,
    req: WorkflowRunRequest,
    db: Session = Depends(get_db),
) -> ToolResponse:
    """Execute a workflow and return the result."""
    workflow = db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

    definition = _workflow_to_definition(workflow)

    with track_run(
        db,
        tool_name="workflow_run",
        input_payload={"workflow_id": workflow_id, "workflow_name": workflow.name, "input": req.input},
    ) as tr:
        result = _engine.execute(definition, workflow_input=req.input)
        tr.output = result

    return ToolResponse(success=result["status"] == "completed", data=result)

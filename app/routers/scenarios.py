"""Scenario listing endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ToolResponse
from app.services.run_tracker import track_run
from app.services.scenarios.registry import get_scenario, list_scenarios
from app.services.scenarios.runner import run_scenario

router = APIRouter(prefix="/api", tags=["scenarios"])


class ScenarioRunRequest(BaseModel):
    input_text: str = Field(..., min_length=1, description="Scenario input text to process")


@router.get("/scenarios")
def get_scenarios() -> dict[str, Any]:
    """List all available agent scenarios."""
    return {"scenarios": list_scenarios()}


@router.get("/scenarios/{scenario_id}")
def get_scenario_detail(scenario_id: str) -> dict[str, Any]:
    """Get details for a specific scenario."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")
    return scenario.to_dict()


@router.post("/scenarios/{scenario_id}/run", response_model=ToolResponse)
def run_scenario_endpoint(
    scenario_id: str,
    req: ScenarioRunRequest,
    db: Session = Depends(get_db),
) -> ToolResponse:
    """Run a scenario-specific business flow and return structured output."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")

    with track_run(
        db,
        tool_name="scenario_run",
        input_payload={"scenario_id": scenario_id, "input_text": req.input_text},
    ) as tr:
        result = run_scenario(scenario_id, req.input_text)
        if result is None:
            # Defensive guard: registry says it exists, but service returned None.
            raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")
        tr.output = result

    return ToolResponse(success=True, data=result)

"""Scenario listing endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.scenarios.registry import get_scenario, list_scenarios

router = APIRouter(prefix="/api", tags=["scenarios"])


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

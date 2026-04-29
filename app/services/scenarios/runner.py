"""Scenario runner service.

Executes scenario-specific business flows and returns structured output
contracts tailored for frontend rendering.
"""

from __future__ import annotations

from typing import Any

from agent.tools.email_tools import handle_classify_email, handle_draft_email
from agent.tools.lookup import handle_lookup_order
from app.services.process import run_process_pipeline
from app.services.scenarios.registry import get_scenario


def run_scenario(scenario_id: str, input_text: str) -> dict[str, Any] | None:
    """Run a scenario-specific business flow.

    Returns None when scenario_id does not exist.
    """
    scenario = get_scenario(scenario_id)
    if not scenario:
        return None

    if scenario_id == "invoice-processing":
        return _run_invoice_scenario(scenario_id, scenario.name, input_text)
    if scenario_id == "clinic-email":
        return _run_clinic_email_scenario(scenario_id, scenario.name, input_text)
    if scenario_id == "support-triage":
        return _run_support_triage_scenario(scenario_id, scenario.name, input_text)
    if scenario_id == "contract-review":
        return _run_contract_review_scenario(scenario_id, scenario.name, input_text)

    # Fallback for future scenarios
    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario.name,
        "output_type": "generic_result",
        "result": {
            "message": "Scenario is registered but has no dedicated runner yet.",
            "input_preview": input_text[:400],
        },
    }


def _run_invoice_scenario(scenario_id: str, scenario_name: str, input_text: str) -> dict[str, Any]:
    pipeline_result = run_process_pipeline(input_text, document_type="invoice")
    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "output_type": "invoice_result",
        "result": pipeline_result,
    }


def _run_clinic_email_scenario(scenario_id: str, scenario_name: str, input_text: str) -> dict[str, Any]:
    classification = handle_classify_email(email_text=input_text)
    order_lookup = _lookup_order_from_entities(classification)

    draft_context = (
        f"Email category: {classification.get('category', 'unknown')}. "
        f"Intent: {classification.get('intent', 'unknown')}. "
        f"Order lookup status: {order_lookup.get('status', 'not_run')}."
    )
    reply_draft = handle_draft_email(
        context=draft_context,
        tone="professional",
        include_order_info=(order_lookup.get("status") == "found"),
    )

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "output_type": "email_triage_result",
        "result": {
            "classification": classification,
            "order_lookup": order_lookup,
            "reply_draft": reply_draft,
        },
    }


def _run_support_triage_scenario(scenario_id: str, scenario_name: str, input_text: str) -> dict[str, Any]:
    classification = handle_classify_email(email_text=input_text)
    reply_draft = handle_draft_email(
        context=(
            f"Support request triage: category={classification.get('category')}, "
            f"priority={classification.get('priority')}, intent={classification.get('intent')}"
        ),
        tone="empathetic",
    )

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "output_type": "email_triage_result",
        "result": {
            "classification": classification,
            "order_lookup": {"status": "not_run"},
            "reply_draft": reply_draft,
        },
    }


def _run_contract_review_scenario(scenario_id: str, scenario_name: str, input_text: str) -> dict[str, Any]:
    # Reuse process pipeline with contract hint for structured extraction/validation
    pipeline_result = run_process_pipeline(input_text, document_type="contract")
    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "output_type": "contract_review_result",
        "result": pipeline_result,
    }


def _lookup_order_from_entities(classification: dict[str, Any]) -> dict[str, Any]:
    entities = classification.get("entities", {}) or {}
    order_numbers = entities.get("order_numbers", [])
    if not order_numbers:
        return {"status": "not_found", "message": "No order number found in email"}

    order_id = str(order_numbers[0]).lstrip("#")
    return handle_lookup_order(order_id=order_id)

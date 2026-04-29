"""Tests for scenario-run API endpoint."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


class TestScenarioRunEndpoint:
    """POST /api/scenarios/{scenario_id}/run"""

    @patch("app.routers.scenarios.run_scenario")
    def test_returns_structured_result_for_known_scenario(self, mock_run_scenario, client: TestClient) -> None:
        mock_run_scenario.return_value = {
            "scenario_id": "invoice-processing",
            "scenario_name": "Invoice Processing",
            "output_type": "invoice_result",
            "result": {
                "document_type": "invoice",
                "validation_errors": 0,
            },
        }

        response = client.post(
            "/api/scenarios/invoice-processing/run",
            json={"input_text": "INVOICE #123\nTotal: 1000 DKK"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["scenario_id"] == "invoice-processing"
        assert data["data"]["output_type"] == "invoice_result"

    def test_returns_404_for_unknown_scenario(self, client: TestClient) -> None:
        response = client.post(
            "/api/scenarios/unknown-scenario/run",
            json={"input_text": "hello"},
        )

        assert response.status_code == 404
        assert "Scenario not found" in response.json()["detail"]

    def test_validates_non_empty_input_text(self, client: TestClient) -> None:
        response = client.post(
            "/api/scenarios/invoice-processing/run",
            json={"input_text": ""},
        )
        assert response.status_code == 422


class TestScenarioRunnerService:
    """Service-level behavior through endpoint-level integration."""

    @patch("app.services.scenarios.runner.run_process_pipeline")
    def test_invoice_flow_uses_process_pipeline(self, mock_pipeline, client: TestClient) -> None:
        mock_pipeline.return_value = {
            "document_type": "invoice",
            "validation_errors": 0,
            "erp_output": {"total": "2125.00 DKK"},
        }

        response = client.post(
            "/api/scenarios/invoice-processing/run",
            json={"input_text": "INVOICE #INV-2026-0847"},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["output_type"] == "invoice_result"
        mock_pipeline.assert_called_once_with("INVOICE #INV-2026-0847", document_type="invoice")

    @patch("app.services.scenarios.runner.handle_draft_email")
    @patch("app.services.scenarios.runner.handle_lookup_order")
    @patch("app.services.scenarios.runner.handle_classify_email")
    def test_clinic_email_flow_composes_email_tools(
        self,
        mock_classify,
        mock_lookup,
        mock_draft,
        client: TestClient,
    ) -> None:
        mock_classify.return_value = {
            "category": "order_inquiry",
            "priority": "medium",
            "intent": "status_check",
            "entities": {"order_numbers": ["#12345"]},
        }
        mock_lookup.return_value = {"status": "found", "order": {"order_id": "12345"}}
        mock_draft.return_value = {"draft": "Dear clinic, your order is shipped.", "needs_review": True}

        response = client.post(
            "/api/scenarios/clinic-email/run",
            json={"input_text": "Please update on order #12345"},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["output_type"] == "email_triage_result"
        assert payload["result"]["classification"]["category"] == "order_inquiry"
        assert payload["result"]["order_lookup"]["status"] == "found"
        assert "draft" in payload["result"]["reply_draft"]

"""Tests for the stats endpoint."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    return TestClient(app)


class TestStatsEndpoint:
    """Test GET /api/stats."""

    @patch("app.routers.stats._query_stats")
    def test_returns_stats_structure(self, mock_query, client):
        mock_query.return_value = {
            "total_runs": 42,
            "total_cost_usd": 1.23,
            "runs_today": 5,
            "error_count": 2,
            "avg_duration_ms": 450,
            "runs_by_tool": {"chat": 20, "process": 15, "analyze": 7},
            "runs_by_day": [{"date": "2026-07-14", "count": 5}],
        }

        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_runs" in data
        assert "total_cost_usd" in data
        assert "runs_today" in data

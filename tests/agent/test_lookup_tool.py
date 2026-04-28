"""Tests for the order lookup tool (mock data)."""

import pytest

from agent.tools.lookup import LOOKUP_TOOL, handle_lookup_order


class TestLookupTool:
    """Test order lookup."""

    def test_tool_definition(self):
        assert LOOKUP_TOOL["name"] == "lookup_order"

    def test_known_order_returns_data(self):
        result = handle_lookup_order({"order_id": "12345"})
        assert result["status"] != "not_found"
        assert "order" in result

    def test_unknown_order_returns_not_found(self):
        result = handle_lookup_order({"order_id": "99999"})
        assert result["status"] == "not_found"

    def test_missing_order_id_returns_error(self):
        result = handle_lookup_order({})
        assert "error" in result

"""Integration tests for the agent tool-dispatch call contract.

These tests verify that handlers registered in TOOL_HANDLERS accept
keyword arguments exactly as the agent sends them via handler(**params).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent.tools import TOOL_HANDLERS


class TestToolDispatchContract:
    """Ensure handlers can be called with keyword arguments."""

    def test_classify_email_accepts_keyword_arguments(self) -> None:
        result = TOOL_HANDLERS["classify_email"](
            email_text="Please confirm delivery for order #12345",
        )
        assert "category" in result
        assert "priority" in result

    def test_draft_email_accepts_keyword_arguments(self) -> None:
        result = TOOL_HANDLERS["draft_email_reply"](
            context="Customer asked for shipping status of order #12345",
            tone="professional",
            include_order_info=True,
        )
        assert "draft" in result
        assert result["needs_review"] is True

    def test_lookup_order_accepts_keyword_arguments(self) -> None:
        result = TOOL_HANDLERS["lookup_order"](order_id="12345")
        assert result["status"] in {"found", "not_found"}

    def test_search_knowledge_accepts_keyword_arguments(self) -> None:
        mock_retriever = MagicMock()
        mock_retriever.search.return_value = []

        with patch("agent.tools.knowledge._get_retriever", return_value=mock_retriever):
            result = TOOL_HANDLERS["search_knowledge"](
                query="What are the payment terms?",
                n_results=3,
            )

        assert result["status"] == "not_found"
        mock_retriever.search.assert_called_once_with("What are the payment terms?", n_results=3)

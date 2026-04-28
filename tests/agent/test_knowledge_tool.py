"""Tests for the search_knowledge agent tool."""

from unittest.mock import patch, MagicMock

import pytest

from agent.tools.knowledge import KNOWLEDGE_TOOL, handle_search_knowledge


class TestKnowledgeToolDefinition:
    """Test tool schema."""

    def test_has_required_fields(self):
        assert KNOWLEDGE_TOOL["name"] == "search_knowledge"
        assert "input_schema" in KNOWLEDGE_TOOL
        assert "query" in KNOWLEDGE_TOOL["input_schema"]["properties"]

    def test_query_is_required(self):
        assert "query" in KNOWLEDGE_TOOL["input_schema"]["required"]


class TestHandleSearchKnowledge:
    """Test the tool handler function."""

    @patch("agent.tools.knowledge._get_retriever")
    def test_returns_context_and_sources(self, mock_get_retriever):
        mock_retriever = MagicMock()

        # Create proper SearchResult objects
        from app.services.rag.retriever import SearchResult
        mock_results = [
            SearchResult(text="Relevant info", source="doc.pdf", doc_id="d1", score=0.92, chunk_id="d1-0"),
        ]
        mock_retriever.search.return_value = mock_results
        mock_retriever.format_context.return_value = "Knowledge base context:\n\n[1] (source: doc.pdf) (relevance: 92%)\nRelevant info"
        mock_get_retriever.return_value = mock_retriever

        result = handle_search_knowledge({"query": "What is X?"})

        assert result["status"] == "found"
        assert len(result["sources"]) == 1
        assert result["sources"][0]["source"] == "doc.pdf"
        assert "context" in result

    @patch("agent.tools.knowledge._get_retriever")
    def test_returns_not_found_when_empty(self, mock_get_retriever):
        mock_retriever = MagicMock()
        mock_retriever.search.return_value = []
        mock_retriever.format_context.return_value = "No relevant documents found in knowledge base."
        mock_get_retriever.return_value = mock_retriever

        result = handle_search_knowledge({"query": "Unknown topic"})
        assert result["status"] == "not_found"

    def test_missing_query_returns_error(self):
        result = handle_search_knowledge({})
        assert "error" in result

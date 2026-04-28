"""Tests for the RAG retriever that ties chunking, embedding, and search."""

from unittest.mock import patch, MagicMock

import pytest

from app.services.rag.retriever import Retriever, SearchResult


@pytest.fixture()
def mock_deps():
    """Mock vectorstore and embedder."""
    with (
        patch("app.services.rag.retriever.VectorStore") as MockVS,
        patch("app.services.rag.retriever.embed_single") as mock_embed,
        patch("app.services.rag.retriever.embed_texts") as mock_batch,
    ):
        mock_store = MagicMock()
        MockVS.return_value = mock_store
        yield {
            "store": mock_store,
            "embed_single": mock_embed,
            "embed_batch": mock_batch,
        }


class TestRetrieverIngest:
    """Test document ingestion."""

    def test_ingest_chunks_and_stores(self, mock_deps):
        # Make embed_batch return one vector per input text
        mock_deps["embed_batch"].side_effect = lambda texts: [[0.1]] * len(texts)
        long_text = "First paragraph. " * 40 + "\n\n" + "Second paragraph. " * 40

        retriever = Retriever()
        count = retriever.ingest(doc_id="doc-1", text=long_text, source="test.pdf")

        assert count > 1  # Text should be split into multiple chunks
        mock_deps["embed_batch"].assert_called_once()
        mock_deps["store"].add.assert_called_once()
        call_kwargs = mock_deps["store"].add.call_args[1]
        assert call_kwargs["doc_id"] == "doc-1"
        assert len(call_kwargs["texts"]) == len(call_kwargs["embeddings"])

    def test_ingest_passes_source_metadata(self, mock_deps):
        mock_deps["embed_batch"].return_value = [[0.1]]

        retriever = Retriever()
        retriever.ingest(doc_id="doc-1", text="Hello world", source="report.pdf")

        call_kwargs = mock_deps["store"].add.call_args[1]
        assert call_kwargs["metadatas"][0]["source"] == "report.pdf"


class TestRetrieverSearch:
    """Test similarity search."""

    def test_search_returns_results(self, mock_deps):
        mock_deps["embed_single"].return_value = [0.1, 0.2]
        mock_deps["store"].query.return_value = [
            {"text": "relevant chunk", "metadata": {"source": "test.pdf", "doc_id": "doc-1"}, "distance": 0.12, "id": "doc-1-0"},
        ]

        retriever = Retriever()
        results = retriever.search("What is the main topic?")

        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].text == "relevant chunk"
        assert results[0].source == "test.pdf"
        assert results[0].score == pytest.approx(0.88, abs=0.01)  # 1 - distance

    def test_search_formats_context_string(self, mock_deps):
        mock_deps["embed_single"].return_value = [0.1]
        mock_deps["store"].query.return_value = [
            {"text": "Chunk A", "metadata": {"source": "a.pdf", "doc_id": "d1"}, "distance": 0.1, "id": "d1-0"},
            {"text": "Chunk B", "metadata": {"source": "b.pdf", "doc_id": "d2"}, "distance": 0.2, "id": "d2-0"},
        ]

        retriever = Retriever()
        results = retriever.search("query")
        context = retriever.format_context(results)

        assert "Chunk A" in context
        assert "Chunk B" in context
        assert "a.pdf" in context

    def test_search_empty_returns_empty(self, mock_deps):
        mock_deps["embed_single"].return_value = [0.1]
        mock_deps["store"].query.return_value = []

        retriever = Retriever()
        results = retriever.search("nothing")
        assert results == []

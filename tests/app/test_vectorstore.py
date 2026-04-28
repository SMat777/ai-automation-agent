"""Tests for the ChromaDB vector store wrapper."""

from unittest.mock import patch, MagicMock

import pytest

from app.services.rag.vectorstore import VectorStore


@pytest.fixture()
def mock_chroma():
    """Provide a mocked ChromaDB client and collection."""
    with patch("app.services.rag.vectorstore.chromadb") as mock_mod:
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_mod.PersistentClient.return_value = mock_client
        yield mock_collection


class TestVectorStoreAdd:
    """Test adding documents to the store."""

    def test_add_stores_texts_with_embeddings(self, mock_chroma):
        store = VectorStore(persist_dir="/tmp/test_chroma")
        store.add(
            doc_id="doc-1",
            texts=["chunk one", "chunk two"],
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            metadatas=[{"source": "test.pdf"}, {"source": "test.pdf"}],
        )
        mock_chroma.add.assert_called_once()
        call_kwargs = mock_chroma.add.call_args[1]
        assert len(call_kwargs["documents"]) == 2
        assert len(call_kwargs["embeddings"]) == 2
        assert call_kwargs["documents"][0] == "chunk one"

    def test_add_generates_ids_with_doc_prefix(self, mock_chroma):
        store = VectorStore(persist_dir="/tmp/test_chroma")
        store.add(
            doc_id="abc",
            texts=["one"],
            embeddings=[[0.1]],
        )
        call_kwargs = mock_chroma.add.call_args[1]
        assert call_kwargs["ids"][0].startswith("abc-")


class TestVectorStoreQuery:
    """Test querying the store."""

    def test_query_returns_results(self, mock_chroma):
        mock_chroma.query.return_value = {
            "documents": [["relevant text"]],
            "metadatas": [[{"source": "test.pdf", "doc_id": "doc-1"}]],
            "distances": [[0.15]],
            "ids": [["doc-1-0"]],
        }
        store = VectorStore(persist_dir="/tmp/test_chroma")
        results = store.query(embedding=[0.1, 0.2], n_results=3)
        assert len(results) == 1
        assert results[0]["text"] == "relevant text"
        assert results[0]["distance"] == 0.15

    def test_query_respects_n_results(self, mock_chroma):
        mock_chroma.query.return_value = {
            "documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]],
        }
        store = VectorStore(persist_dir="/tmp/test_chroma")
        store.query(embedding=[0.1], n_results=5)
        call_kwargs = mock_chroma.query.call_args[1]
        assert call_kwargs["n_results"] == 5


class TestVectorStoreDelete:
    """Test deleting documents."""

    def test_delete_by_doc_id(self, mock_chroma):
        mock_chroma.get.return_value = {"ids": ["doc-1-0", "doc-1-1"]}
        store = VectorStore(persist_dir="/tmp/test_chroma")
        store.delete(doc_id="doc-1")
        mock_chroma.delete.assert_called_once_with(ids=["doc-1-0", "doc-1-1"])


class TestVectorStoreList:
    """Test listing stored documents."""

    def test_list_returns_unique_doc_ids(self, mock_chroma):
        mock_chroma.get.return_value = {
            "metadatas": [
                {"doc_id": "doc-1"}, {"doc_id": "doc-1"},
                {"doc_id": "doc-2"},
            ],
        }
        store = VectorStore(persist_dir="/tmp/test_chroma")
        docs = store.list_documents()
        assert set(docs) == {"doc-1", "doc-2"}

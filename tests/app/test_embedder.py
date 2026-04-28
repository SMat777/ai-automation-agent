"""Tests for the embedding service."""

from unittest.mock import patch, MagicMock

import pytest

from app.services.rag.embedder import embed_texts, embed_single


class TestEmbedTexts:
    """Test batch embedding."""

    @patch("app.services.rag.embedder._get_client")
    def test_returns_list_of_float_lists(self, mock_client):
        mock_resp = MagicMock()
        mock_resp.data = [
            MagicMock(embedding=[0.1, 0.2, 0.3]),
            MagicMock(embedding=[0.4, 0.5, 0.6]),
        ]
        mock_client.return_value.embeddings.create.return_value = mock_resp

        result = embed_texts(["hello", "world"])
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]

    @patch("app.services.rag.embedder._get_client")
    def test_calls_openai_with_correct_model(self, mock_client):
        mock_resp = MagicMock()
        mock_resp.data = [MagicMock(embedding=[0.1])]
        mock_client.return_value.embeddings.create.return_value = mock_resp

        embed_texts(["test"])
        mock_client.return_value.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input=["test"],
        )

    @patch("app.services.rag.embedder._get_client")
    def test_empty_list_returns_empty(self, mock_client):
        result = embed_texts([])
        assert result == []
        mock_client.return_value.embeddings.create.assert_not_called()


class TestEmbedSingle:
    """Test single text embedding."""

    @patch("app.services.rag.embedder.embed_texts")
    def test_delegates_to_batch(self, mock_batch):
        mock_batch.return_value = [[0.1, 0.2]]
        result = embed_single("hello")
        assert result == [0.1, 0.2]
        mock_batch.assert_called_once_with(["hello"])

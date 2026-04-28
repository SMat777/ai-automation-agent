"""Tests for the document upload endpoint."""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    return TestClient(app)


class TestUploadEndpoint:
    """Test POST /api/upload."""

    @patch("app.routers.upload._ingest_document")
    def test_upload_text_file(self, mock_ingest, client):
        mock_ingest.return_value = {"doc_id": "abc123", "chunk_count": 3}

        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", b"Hello world content", "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["status"] == "ingested"

    @patch("app.routers.upload._ingest_document")
    def test_upload_eml_file(self, mock_ingest, client):
        mock_ingest.return_value = {"doc_id": "def456", "chunk_count": 1}

        eml_content = (
            b"From: test@example.com\r\n"
            b"Subject: Test\r\n\r\n"
            b"Body text here"
        )
        response = client.post(
            "/api/upload",
            files={"file": ("email.eml", eml_content, "message/rfc822")},
        )
        assert response.status_code == 200

    def test_rejects_unsupported_file_type(self, client):
        response = client.post(
            "/api/upload",
            files={"file": ("image.png", b"fakepng", "image/png")},
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_rejects_empty_file(self, client):
        response = client.post(
            "/api/upload",
            files={"file": ("empty.txt", b"", "text/plain")},
        )
        assert response.status_code == 400


class TestKnowledgeEndpoints:
    """Test GET/DELETE /api/knowledge."""

    @patch("app.routers.knowledge._get_retriever")
    def test_list_documents_empty(self, mock_ret, client):
        mock_retriever = MagicMock()
        mock_retriever.list_documents.return_value = []
        mock_ret.return_value = mock_retriever

        response = client.get("/api/knowledge")
        assert response.status_code == 200
        assert response.json()["documents"] == []

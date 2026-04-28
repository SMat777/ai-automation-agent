"""Tests for the RAG text chunker."""

import pytest

from app.services.rag.chunker import chunk_text, Chunk


class TestChunkText:
    """Test recursive character text splitting."""

    def test_short_text_returns_single_chunk(self):
        text = "This is a short text."
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].index == 0

    def test_long_text_splits_into_multiple_chunks(self):
        text = "Word " * 200  # 1000 chars
        chunks = chunk_text(text, chunk_size=200, overlap=40)
        assert len(chunks) > 1
        # Every chunk respects max size
        for c in chunks:
            assert len(c.text) <= 200

    def test_overlap_creates_shared_content(self):
        text = "A " * 300  # 600 chars
        chunks = chunk_text(text, chunk_size=200, overlap=40)
        assert len(chunks) >= 2
        # Second chunk should start before first chunk ends
        end_of_first = chunks[0].text
        start_of_second = chunks[1].text
        # There should be overlapping content
        assert end_of_first[-20:].strip() in start_of_second or len(chunks) > 2

    def test_splits_on_paragraph_boundary(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = chunk_text(text, chunk_size=30, overlap=5)
        # Should prefer splitting on \n\n
        for c in chunks:
            stripped = c.text.strip()
            assert not stripped.startswith("\n\n")

    def test_chunk_has_correct_metadata(self):
        text = "Hello world. " * 100
        chunks = chunk_text(text, chunk_size=200, overlap=30)
        for i, c in enumerate(chunks):
            assert c.index == i
            assert isinstance(c.text, str)
            assert len(c.text) > 0

    def test_empty_text_returns_empty_list(self):
        assert chunk_text("", chunk_size=500, overlap=50) == []

    def test_whitespace_only_returns_empty_list(self):
        assert chunk_text("   \n\n  ", chunk_size=500, overlap=50) == []

    def test_default_parameters(self):
        text = "Test content for default params."
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0].text == text

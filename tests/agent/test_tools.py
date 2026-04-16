"""Tests for agent tools — verifies tool handlers work correctly without API calls."""

from agent.tools.analyze import handle_analyze
from agent.tools.extract import handle_extract
from agent.tools.summarize import handle_summarize


class TestAnalyzeTool:
    def test_counts_words(self) -> None:
        result = handle_analyze("Hello world this is a test")
        assert result["word_count"] == 6

    def test_finds_sections(self) -> None:
        text = "# Header 1\nSome text\n# Header 2\nMore text"
        result = handle_analyze(text)
        assert len(result["sections"]) == 2
        assert result["sections"][0] == "# Header 1"

    def test_extracts_key_points(self) -> None:
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = handle_analyze(text)
        assert result["paragraph_count"] == 3
        assert len(result["key_points"]) == 3

    def test_respects_focus(self) -> None:
        result = handle_analyze("Some text", focus="financial")
        assert result["focus"] == "financial"

    def test_default_focus_is_general(self) -> None:
        result = handle_analyze("Some text")
        assert result["focus"] == "general"


class TestExtractTool:
    def test_extracts_field(self) -> None:
        text = "Company: Columbus Global\nLocation: Aarhus"
        result = handle_extract(text, fields=["Company", "Location"])
        assert result["extracted"]["Company"] == "Columbus Global"
        assert result["extracted"]["Location"] == "Aarhus"

    def test_reports_missing_fields(self) -> None:
        text = "Company: Columbus Global"
        result = handle_extract(text, fields=["Company", "Revenue"])
        assert result["fields_found"] == 1
        assert result["fields_missing"] == 1
        assert result["extracted"]["Revenue"] is None

    def test_handles_no_matches(self) -> None:
        result = handle_extract("Random text", fields=["Name", "Date"])
        assert result["fields_found"] == 0
        assert result["fields_missing"] == 2

    def test_case_insensitive(self) -> None:
        text = "company: Test Corp"
        result = handle_extract(text, fields=["Company"])
        assert result["extracted"]["Company"] == "Test Corp"


class TestSummarizeTool:
    def test_bullet_format(self) -> None:
        text = "First point. Second point. Third point."
        result = handle_summarize(text, format="bullets", max_points=2)
        assert result["format"] == "bullets"
        assert result["summary"].count("- ") == 2

    def test_paragraph_format(self) -> None:
        text = "First sentence. Second sentence. Third sentence."
        result = handle_summarize(text, format="paragraph")
        assert result["format"] == "paragraph"
        assert "- " not in result["summary"]

    def test_counts_original_words(self) -> None:
        text = "One two three four five"
        result = handle_summarize(text)
        assert result["original_word_count"] == 5

    def test_default_format_is_bullets(self) -> None:
        result = handle_summarize("Some text here.")
        assert result["format"] == "bullets"

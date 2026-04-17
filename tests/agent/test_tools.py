"""Tests for agent tools — verifies tool handlers work correctly without API calls."""

from agent.tools.analyze import handle_analyze
from agent.tools.extract import handle_extract
from agent.tools.summarize import handle_summarize


# ── Analyze Tool ─────────────────────────────────────────────────────────────


class TestAnalyzeDocumentType:
    def test_detects_email(self) -> None:
        text = "From: alice@example.com\nTo: bob@example.com\nSubject: Hello\n\nHi Bob"
        result = handle_analyze(text)
        assert result["document_type"] == "email"

    def test_detects_markdown(self) -> None:
        text = "# Title\n\nSome text\n\n## Section 2\n\nMore text"
        result = handle_analyze(text)
        assert result["document_type"] == "markdown_document"

    def test_detects_data_table(self) -> None:
        text = "| Name | Age |\n|------|-----|\n| Alice | 30 |"
        result = handle_analyze(text)
        assert result["document_type"] == "data_table"

    def test_detects_general_text(self) -> None:
        result = handle_analyze("Just some regular text without structure.")
        assert result["document_type"] == "general_text"


class TestAnalyzeSections:
    def test_extracts_heading_hierarchy(self) -> None:
        text = "# H1\n\nText\n\n## H2\n\nMore\n\n### H3"
        result = handle_analyze(text)
        sections = result["sections"]
        assert len(sections) == 3
        assert sections[0] == {"level": 1, "title": "H1"}
        assert sections[1] == {"level": 2, "title": "H2"}
        assert sections[2] == {"level": 3, "title": "H3"}

    def test_empty_sections_for_plain_text(self) -> None:
        result = handle_analyze("No headings here.")
        assert result["sections"] == []


class TestAnalyzeEntities:
    def test_extracts_emails(self) -> None:
        text = "Contact alice@example.com or bob@test.org"
        entities = handle_analyze(text)["entities"]
        assert set(entities["emails"]) == {"alice@example.com", "bob@test.org"}

    def test_extracts_dates(self) -> None:
        text = "Meeting on 2026-04-16 and deadline 15. april 2026"
        entities = handle_analyze(text)["entities"]
        assert "2026-04-16" in entities["dates"]

    def test_extracts_urls(self) -> None:
        text = "Visit https://example.com and http://test.org/page"
        entities = handle_analyze(text)["entities"]
        assert len(entities["urls"]) == 2

    def test_no_entities_in_plain_text(self) -> None:
        entities = handle_analyze("Hello world")["entities"]
        assert entities["emails"] == []
        assert entities["dates"] == []
        assert entities["urls"] == []


class TestAnalyzeStats:
    def test_word_count(self) -> None:
        result = handle_analyze("Hello world this is a test")
        assert result["statistics"]["word_count"] == 6

    def test_paragraph_count(self) -> None:
        text = "First paragraph.\n\nSecond paragraph.\n\nThird."
        result = handle_analyze(text)
        assert result["statistics"]["paragraph_count"] == 3


class TestAnalyzeKeyPoints:
    def test_extracts_content_paragraphs(self) -> None:
        text = "# Title\n\nImportant first point here.\n\nSecond point is also here."
        points = handle_analyze(text)["key_points"]
        assert len(points) == 2
        assert "Important first point" in points[0]

    def test_truncates_long_paragraphs(self) -> None:
        long_text = "Word " * 100
        points = handle_analyze(long_text)["key_points"]
        assert points[0].endswith("...")

    def test_respects_focus(self) -> None:
        result = handle_analyze("Text", focus="financial")
        assert result["focus"] == "financial"


# ── Extract Tool ─────────────────────────────────────────────────────────────


class TestExtractKeyValue:
    def test_extracts_basic_fields(self) -> None:
        text = "Company: Northwind Traders\nLocation: Copenhagen"
        result = handle_extract(text, ["Company", "Location"], strategy="key_value")
        assert result["extracted"]["Company"] == "Northwind Traders"
        assert result["extracted"]["Location"] == "Copenhagen"

    def test_case_insensitive(self) -> None:
        text = "company: Test Corp"
        result = handle_extract(text, ["Company"], strategy="key_value")
        assert result["extracted"]["Company"] == "Test Corp"

    def test_handles_underscored_fields(self) -> None:
        text = "Company Name: Acme Corp"
        result = handle_extract(text, ["company_name"], strategy="key_value")
        assert result["extracted"]["company_name"] == "Acme Corp"

    def test_reports_missing(self) -> None:
        result = handle_extract("Random text", ["Name"], strategy="key_value")
        assert result["fields_found"] == 0
        assert result["fields_missing"] == 1


class TestExtractTable:
    def test_extracts_from_markdown_table(self) -> None:
        text = "| Name | Age | City |\n|------|-----|------|\n| Alice | 30 | Aarhus |"
        result = handle_extract(text, ["Name", "Age", "City"], strategy="table")
        assert result["extracted"]["Name"] == "Alice"
        assert result["extracted"]["Age"] == "30"
        assert result["extracted"]["City"] == "Aarhus"

    def test_handles_no_table(self) -> None:
        result = handle_extract("Plain text", ["Name"], strategy="table")
        assert result["fields_found"] == 0


class TestExtractList:
    def test_extracts_from_bullet_list(self) -> None:
        text = "- Name: Alice\n- Role: Developer\n- Location: Aarhus"
        result = handle_extract(text, ["Name", "Role"], strategy="list")
        assert result["extracted"]["Name"] == "Alice"
        assert result["extracted"]["Role"] == "Developer"

    def test_extracts_from_numbered_list(self) -> None:
        text = "1. Name: Bob\n2. Title: Manager"
        result = handle_extract(text, ["Name", "Title"], strategy="list")
        assert result["extracted"]["Name"] == "Bob"


class TestExtractAuto:
    def test_auto_combines_strategies(self) -> None:
        text = (
            "Company: Northwind Traders\n\n"
            "| Role | Status |\n|------|--------|\n| Engineer | Active |\n\n"
            "- Location: Copenhagen"
        )
        result = handle_extract(
            text, ["Company", "Role", "Location"], strategy="auto"
        )
        assert result["extracted"]["Company"] == "Northwind Traders"
        assert result["extracted"]["Role"] == "Engineer"
        assert result["extracted"]["Location"] == "Copenhagen"
        assert result["strategy"] == "auto"
        assert len(result["strategies_used"]) > 0

    def test_auto_is_default(self) -> None:
        result = handle_extract("Company: Test", ["Company"])
        assert result["strategy"] == "auto"


# ── Summarize Tool ───────────────────────────────────────────────────────────


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
        result = handle_summarize("One two three four five")
        assert result["original_word_count"] == 5

    def test_default_format_is_bullets(self) -> None:
        result = handle_summarize("Some text here.")
        assert result["format"] == "bullets"

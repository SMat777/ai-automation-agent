"""Tests for agent tools — verifies tool handlers work correctly without API calls."""

from unittest.mock import MagicMock, patch

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

    def test_extracts_organizations_with_suffix(self) -> None:
        text = "We partnered with Columbus A/S and Acme Corp. last year."
        entities = handle_analyze(text)["entities"]
        assert "Columbus A/S" in entities["organizations"]
        assert "Acme Corp." in entities["organizations"]

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


class TestAnalyzeAiPath:
    """Verify that analyze_document uses Claude when api_key is provided."""

    def test_ai_path_returns_ai_method(self) -> None:
        """When api_key is given, method should be 'ai'."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(
            text='{"document_type": "contract", "key_points": ["Effective date is 2026-01-01", "Governs IP ownership"], "summary": "Employment contract between two parties."}'
        )]

        with patch("agent.tools.analyze.Anthropic") as mock_cls:
            mock_cls.return_value.messages.create.return_value = mock_response
            result = handle_analyze(
                "This agreement is entered into by Party A and Party B. "
                "The effective date is January 1, 2026. This contract governs IP ownership.",
                api_key="test-key",
            )

        assert result["method"] == "ai"
        mock_cls.assert_called_once_with(api_key="test-key")

    def test_fallback_when_no_api_key(self) -> None:
        """Without api_key, method should be 'rule_based'."""
        result = handle_analyze("Some text for analysis")
        assert result["method"] == "rule_based"

    def test_ai_path_still_includes_entities_and_stats(self) -> None:
        """AI path should still include regex-based entities and stats."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(
            text='{"document_type": "email", "key_points": ["Meeting at 3pm"], "summary": "A meeting invitation."}'
        )]

        with patch("agent.tools.analyze.Anthropic") as mock_cls:
            mock_cls.return_value.messages.create.return_value = mock_response
            result = handle_analyze(
                "From: alice@example.com\nMeeting on 2026-04-16 at 3pm.",
                api_key="test-key",
            )

        # AI provides document_type and key_points
        assert result["method"] == "ai"
        # Regex still provides entities and stats
        assert "alice@example.com" in result["entities"]["emails"]
        assert result["statistics"]["word_count"] > 0

    def test_falls_back_on_api_error(self) -> None:
        """If Claude API fails, should fall back to rule-based gracefully."""
        with patch("agent.tools.analyze.Anthropic") as mock_cls:
            mock_cls.return_value.messages.create.side_effect = Exception("API error")
            result = handle_analyze(
                "# Contract\n\nThis agreement between parties.",
                api_key="test-key",
            )

        assert result["method"] == "rule_based"
        assert result["document_type"] is not None


# ── Extract Tool ─────────────────────────────────────────────────────────────


class TestExtractKeyValue:
    def test_extracts_basic_fields(self) -> None:
        text = "Company: Columbus Global\nLocation: Aarhus"
        result = handle_extract(text, ["Company", "Location"], strategy="key_value")
        assert result["extracted"]["Company"] == "Columbus Global"
        assert result["extracted"]["Location"] == "Aarhus"

    def test_case_insensitive(self) -> None:
        text = "company: Test Corp"
        result = handle_extract(text, ["Company"], strategy="key_value")
        assert result["extracted"]["Company"] == "Test Corp"

    def test_handles_underscored_fields(self) -> None:
        text = "Company Name: Columbus"
        result = handle_extract(text, ["company_name"], strategy="key_value")
        assert result["extracted"]["company_name"] == "Columbus"

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
            "Company: Columbus\n\n"
            "| Role | Status |\n|------|--------|\n| Intern | Active |\n\n"
            "- Location: Aarhus"
        )
        result = handle_extract(
            text, ["Company", "Role", "Location"], strategy="auto"
        )
        assert result["extracted"]["Company"] == "Columbus"
        assert result["extracted"]["Role"] == "Intern"
        assert result["extracted"]["Location"] == "Aarhus"
        assert result["strategy"] == "auto"
        assert len(result["strategies_used"]) > 0

    def test_auto_is_default(self) -> None:
        result = handle_extract("Company: Test", ["Company"])
        assert result["strategy"] == "auto"


class TestExtractAiPath:
    """Verify AI-assisted extraction when regex finds insufficient fields."""

    def test_ai_fills_missing_fields(self) -> None:
        """When regex misses fields, Claude should fill them in."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(
            text='{"deadline": "March 15, 2026", "budget": "$50,000"}'
        )]

        with patch("agent.tools.extract.Anthropic") as mock_cls:
            mock_cls.return_value.messages.create.return_value = mock_response
            result = handle_extract(
                "The project involves building a new website for the client.",
                fields=["company", "deadline", "budget"],
                api_key="test-key",
            )

        assert result["method"] == "ai"
        assert result["extracted"]["deadline"] == "March 15, 2026"
        assert result["extracted"]["budget"] == "$50,000"

    def test_fallback_when_no_api_key(self) -> None:
        """Without api_key, should use rule-based only."""
        result = handle_extract(
            "Company: Test Corp",
            fields=["company", "missing_field"],
        )
        assert result["method"] == "rule_based"

    def test_no_ai_when_regex_finds_enough(self) -> None:
        """If regex finds >50% of fields, AI is not called."""
        result = handle_extract(
            "Company: Acme\nLocation: Aarhus\nRole: Developer",
            fields=["Company", "Location", "Role"],
            api_key="test-key",
        )
        # All fields found by regex — AI should not be called
        assert result["method"] == "rule_based"
        assert result["fields_found"] == 3

    def test_falls_back_on_api_error(self) -> None:
        """If Claude API fails, should return regex-only results."""
        with patch("agent.tools.extract.Anthropic") as mock_cls:
            mock_cls.return_value.messages.create.side_effect = Exception("API down")
            result = handle_extract(
                "Some unstructured text about a project.",
                fields=["company", "deadline", "budget"],
                api_key="test-key",
            )

        assert result["method"] == "rule_based"
        assert "fields_found" in result


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

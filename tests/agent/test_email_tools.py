"""Tests for email classification and drafting tools."""

from unittest.mock import MagicMock, patch

from agent.tools.email_tools import (
    EMAIL_CLASSIFY_TOOL,
    EMAIL_DRAFT_TOOL,
    handle_classify_email,
    handle_draft_email,
)


class TestClassifyEmailTool:
    """Test email classification."""

    def test_tool_definition(self):
        assert EMAIL_CLASSIFY_TOOL["name"] == "classify_email"
        assert "email_text" in EMAIL_CLASSIFY_TOOL["input_schema"]["required"]

    def test_classifies_order_inquiry(self):
        email_text = (
            "Hi, I would like to check the status of order #12345. "
            "When will it be shipped? Best regards, Dr. Smith"
        )
        result = handle_classify_email({"email_text": email_text})
        assert result["category"] in ("order_inquiry", "shipping", "general")
        assert "priority" in result
        assert "intent" in result

    def test_classifies_complaint(self):
        email_text = (
            "I am very disappointed with the service. The package arrived "
            "damaged and nobody responds to my calls. This is unacceptable!"
        )
        result = handle_classify_email({"email_text": email_text})
        assert result["priority"] == "high"

    def test_missing_text_returns_error(self):
        result = handle_classify_email({})
        assert "error" in result


class TestDraftEmailTool:
    """Test email reply drafting."""

    def test_tool_definition(self):
        assert EMAIL_DRAFT_TOOL["name"] == "draft_email_reply"
        assert "context" in EMAIL_DRAFT_TOOL["input_schema"]["required"]

    def test_drafts_reply(self):
        result = handle_draft_email({
            "context": "Customer asked about order #12345 status. Order is shipped.",
            "tone": "professional",
        })
        assert "draft" in result
        assert len(result["draft"]) > 20

    def test_missing_context_returns_error(self):
        result = handle_draft_email({})
        assert "error" in result


class TestClassifyEmailAiPath:
    """Verify AI-powered email classification."""

    def test_ai_classification_returns_ai_method(self):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(
            text='{"category": "complaint", "priority": "high", "intent": "refund_request", "confidence": 0.92, "reasoning": "Customer expresses strong dissatisfaction and requests refund."}'
        )]

        with patch("agent.tools.email_tools.Anthropic") as mock_cls:
            mock_cls.return_value.messages.create.return_value = mock_response
            result = handle_classify_email(
                email_text="I want a full refund. Your product is terrible.",
                api_key="test-key",
            )

        assert result["method"] == "ai"
        assert result["category"] == "complaint"
        assert result["confidence"] == 0.92
        assert "reasoning" in result
        mock_cls.assert_called_once_with(api_key="test-key")

    def test_classify_fallback_without_api_key(self):
        result = handle_classify_email(
            email_text="I want to check my order status.",
        )
        assert result["method"] == "rule_based"

    def test_classify_falls_back_on_api_error(self):
        with patch("agent.tools.email_tools.Anthropic") as mock_cls:
            mock_cls.return_value.messages.create.side_effect = Exception("API error")
            result = handle_classify_email(
                email_text="Where is my order?",
                api_key="test-key",
            )
        assert result["method"] == "rule_based"
        assert "category" in result


class TestDraftEmailAiPath:
    """Verify AI-powered email drafting."""

    def test_ai_draft_returns_ai_method(self):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(
            text="Dear Customer,\n\nThank you for your patience. Your order #12345 has been shipped and will arrive by Friday.\n\nBest regards,\nSupport Team"
        )]

        with patch("agent.tools.email_tools.Anthropic") as mock_cls:
            mock_cls.return_value.messages.create.return_value = mock_response
            result = handle_draft_email(
                context="Customer asked about order #12345. It shipped yesterday.",
                tone="professional",
                api_key="test-key",
            )

        assert result["method"] == "ai"
        assert "12345" in result["draft"]
        assert result["needs_review"] is True

    def test_draft_fallback_without_api_key(self):
        result = handle_draft_email(
            context="Customer needs help with billing.",
        )
        assert result["method"] == "template"

    def test_draft_falls_back_on_api_error(self):
        with patch("agent.tools.email_tools.Anthropic") as mock_cls:
            mock_cls.return_value.messages.create.side_effect = Exception("API error")
            result = handle_draft_email(
                context="Customer asked about refund.",
                api_key="test-key",
            )
        assert result["method"] == "template"
        assert "draft" in result

"""Tests for email classification and drafting tools."""

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

"""Tests for document text extractors."""


from app.services.extractors.text import extract_text


class TestTextExtractor:
    """Test plain text passthrough extractor."""

    def test_returns_input_unchanged(self):
        assert extract_text(b"Hello world") == "Hello world"

    def test_handles_utf8(self):
        text = "Ærø Ødegaard Åse"
        assert extract_text(text.encode("utf-8")) == text

    def test_empty_returns_empty(self):
        assert extract_text(b"") == ""


class TestEmailExtractor:
    """Test email (.eml) text extraction."""

    def test_extracts_plain_text_body(self):
        from app.services.extractors.email_parser import extract_email

        eml = (
            "From: clinic@example.com\r\n"
            "To: support@donornetwork.com\r\n"
            "Subject: Order status inquiry\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            "\r\n"
            "Hi, I would like to check the status of order #12345.\r\n"
            "Best regards, Dr. Smith\r\n"
        )
        result = extract_email(eml.encode("utf-8"))
        assert "order #12345" in result.lower()
        assert "From: clinic@example.com" in result
        assert "Subject: Order status inquiry" in result

    def test_empty_email_returns_headers(self):
        from app.services.extractors.email_parser import extract_email

        eml = (
            "From: a@b.com\r\n"
            "Subject: Test\r\n"
            "\r\n"
        )
        result = extract_email(eml.encode("utf-8"))
        assert "From: a@b.com" in result

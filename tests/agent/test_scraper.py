"""Tests for the scrape_url tool — all HTTP calls are mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent.tools.scraper import SCRAPE_TOOL, handle_scrape_url


# ── Tool Schema ──────────────────────────────────────────────────────────────


class TestScrapeToolSchema:
    def test_tool_name(self) -> None:
        assert SCRAPE_TOOL["name"] == "scrape_url"

    def test_requires_url_parameter(self) -> None:
        assert "url" in SCRAPE_TOOL["input_schema"]["properties"]
        assert "url" in SCRAPE_TOOL["input_schema"]["required"]


# ── Successful Scraping ──────────────────────────────────────────────────────


SIMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Page</title><meta name="description" content="A test page"></head>
<body>
<h1>Main Heading</h1>
<p>First paragraph with useful content.</p>
<p>Second paragraph with more info.</p>
<a href="https://example.com/about">About</a>
<a href="/relative">Relative link</a>
<script>alert('ignored')</script>
<style>.hidden { display: none; }</style>
</body>
</html>
"""


class TestScrapeSuccess:
    @patch("agent.tools.scraper.httpx")
    def test_extracts_title(self, mock_httpx: MagicMock) -> None:
        mock_response = MagicMock(status_code=200, text=SIMPLE_HTML)
        mock_response.headers = {"content-type": "text/html"}
        mock_httpx.get.return_value = mock_response

        result = handle_scrape_url(url="https://example.com")
        assert result["title"] == "Test Page"

    @patch("agent.tools.scraper.httpx")
    def test_extracts_text_without_scripts_and_styles(
        self, mock_httpx: MagicMock
    ) -> None:
        mock_response = MagicMock(status_code=200, text=SIMPLE_HTML)
        mock_response.headers = {"content-type": "text/html"}
        mock_httpx.get.return_value = mock_response

        result = handle_scrape_url(url="https://example.com")
        assert "First paragraph" in result["content"]
        assert "Second paragraph" in result["content"]
        assert "alert" not in result["content"]
        assert ".hidden" not in result["content"]

    @patch("agent.tools.scraper.httpx")
    def test_extracts_links(self, mock_httpx: MagicMock) -> None:
        mock_response = MagicMock(status_code=200, text=SIMPLE_HTML)
        mock_response.headers = {"content-type": "text/html"}
        mock_httpx.get.return_value = mock_response

        result = handle_scrape_url(url="https://example.com")
        assert any(
            link["href"] == "https://example.com/about" for link in result["links"]
        )

    @patch("agent.tools.scraper.httpx")
    def test_extracts_meta_description(self, mock_httpx: MagicMock) -> None:
        mock_response = MagicMock(status_code=200, text=SIMPLE_HTML)
        mock_response.headers = {"content-type": "text/html"}
        mock_httpx.get.return_value = mock_response

        result = handle_scrape_url(url="https://example.com")
        assert result["metadata"]["description"] == "A test page"

    @patch("agent.tools.scraper.httpx")
    def test_returns_status_and_url(self, mock_httpx: MagicMock) -> None:
        mock_response = MagicMock(status_code=200, text=SIMPLE_HTML)
        mock_response.headers = {"content-type": "text/html"}
        mock_httpx.get.return_value = mock_response

        result = handle_scrape_url(url="https://example.com")
        assert result["status"] == "success"
        assert result["url"] == "https://example.com"


# ── Error Handling ───────────────────────────────────────────────────────────


def _set_httpx_exceptions(mock_httpx: MagicMock) -> None:
    """Attach real httpx exception classes to a module-level mock.

    When we @patch the entire httpx module, `except httpx.SomeError` needs
    real exception classes — not MagicMock objects.
    """
    import httpx as real_httpx

    mock_httpx.TimeoutException = real_httpx.TimeoutException
    mock_httpx.ConnectError = real_httpx.ConnectError
    mock_httpx.HTTPStatusError = real_httpx.HTTPStatusError
    mock_httpx.HTTPError = real_httpx.HTTPError


class TestScrapeErrors:
    def test_missing_url_returns_error(self) -> None:
        result = handle_scrape_url(url="")
        assert "error" in result

    @patch("agent.tools.scraper.httpx")
    def test_http_404_returns_error(self, mock_httpx: MagicMock) -> None:
        import httpx as real_httpx

        _set_httpx_exceptions(mock_httpx)
        mock_response = MagicMock(status_code=404)
        mock_response.raise_for_status.side_effect = real_httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock(status_code=404)
        )
        mock_httpx.get.return_value = mock_response

        result = handle_scrape_url(url="https://example.com/missing")
        assert "error" in result

    @patch("agent.tools.scraper.httpx")
    def test_timeout_returns_error(self, mock_httpx: MagicMock) -> None:
        import httpx as real_httpx

        _set_httpx_exceptions(mock_httpx)
        mock_httpx.get.side_effect = real_httpx.TimeoutException("timed out")

        result = handle_scrape_url(url="https://slow-site.com")
        assert "error" in result
        assert "timeout" in result["error"].lower() or "timed out" in result["error"].lower()

    @patch("agent.tools.scraper.httpx")
    def test_connection_error_returns_error(self, mock_httpx: MagicMock) -> None:
        import httpx as real_httpx

        _set_httpx_exceptions(mock_httpx)
        mock_httpx.get.side_effect = real_httpx.ConnectError("connection refused")

        result = handle_scrape_url(url="https://unreachable.test")
        assert "error" in result


# ── Content Truncation ───────────────────────────────────────────────────────


class TestScrapeTruncation:
    @patch("agent.tools.scraper.httpx")
    def test_large_content_is_truncated(self, mock_httpx: MagicMock) -> None:
        huge_body = "<html><body>" + ("x" * 60_000) + "</body></html>"
        mock_response = MagicMock(status_code=200, text=huge_body)
        mock_response.headers = {"content-type": "text/html"}
        mock_httpx.get.return_value = mock_response

        result = handle_scrape_url(url="https://example.com")
        assert len(result["content"]) <= 50_000
        assert result["truncated"] is True

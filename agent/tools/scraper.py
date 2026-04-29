"""Web scraping tool — fetches and parses content from URLs.

Returns structured output: title, cleaned text content, links, and metadata.
Uses httpx for HTTP requests and BeautifulSoup for HTML parsing.
"""

from __future__ import annotations

from typing import Any

import httpx
from bs4 import BeautifulSoup

# Maximum content length returned to the agent (characters).
MAX_CONTENT_LENGTH = 50_000

# HTTP request timeout in seconds.
REQUEST_TIMEOUT = 15

SCRAPE_TOOL = {
    "name": "scrape_url",
    "description": (
        "Fetch and extract content from a web page URL. Returns the page "
        "title, cleaned text content (scripts and styles removed), links, "
        "and metadata. Use this when you need to read or analyze a web page, "
        "documentation, article, or any publicly accessible URL."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch and parse",
            },
        },
        "required": ["url"],
    },
}


def _extract_metadata(soup: BeautifulSoup) -> dict[str, str]:
    """Pull description, author, and keywords from <meta> tags."""
    meta: dict[str, str] = {}
    for tag in soup.find_all("meta"):
        raw_name = tag.get("name") or tag.get("property") or ""
        name = str(raw_name).lower()
        content = str(tag.get("content", ""))
        if name in ("description", "author", "keywords", "og:title", "og:description"):
            meta[name] = content
    return meta


def _extract_links(soup: BeautifulSoup) -> list[dict[str, str]]:
    """Collect all <a> links with their text labels."""
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    for tag in soup.find_all("a", href=True):
        href = str(tag["href"])
        if href in seen or href.startswith(("#", "javascript:")):
            continue
        seen.add(href)
        text = tag.get_text(strip=True)
        links.append({"href": href, "text": text})
    return links


def _clean_text(soup: BeautifulSoup) -> str:
    """Strip script/style tags and collapse whitespace."""
    for element in soup(["script", "style", "noscript", "iframe"]):
        element.decompose()
    text = soup.get_text(separator="\n")
    # Collapse multiple blank lines into one.
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def handle_scrape_url(
    url: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Fetch a URL, parse HTML, and return structured content.

    Args:
        url: The web page URL to scrape.

    Returns:
        Dict with status, title, content, links, metadata, and truncation flag.
    """
    if not url:
        return {"error": "Missing required parameter: url"}

    try:
        response = httpx.get(
            url,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "AI-Automation-Agent/1.0 (document analysis)"},
        )
        response.raise_for_status()
    except httpx.TimeoutException:
        return {"error": f"Request timed out after {REQUEST_TIMEOUT}s: {url}"}
    except httpx.ConnectError:
        return {"error": f"Could not connect to: {url}"}
    except httpx.HTTPStatusError as exc:
        return {"error": f"HTTP {exc.response.status_code} for: {url}"}
    except httpx.HTTPError as exc:
        return {"error": f"Request failed: {exc}"}

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type and "text" not in content_type:
        return {
            "status": "success",
            "url": url,
            "title": None,
            "content": response.text[:MAX_CONTENT_LENGTH],
            "links": [],
            "metadata": {},
            "truncated": len(response.text) > MAX_CONTENT_LENGTH,
            "content_type": content_type,
        }

    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    content = _clean_text(soup)
    truncated = len(content) > MAX_CONTENT_LENGTH
    if truncated:
        content = content[:MAX_CONTENT_LENGTH]

    return {
        "status": "success",
        "url": url,
        "title": title,
        "content": content,
        "links": _extract_links(soup),
        "metadata": _extract_metadata(soup),
        "truncated": truncated,
        "content_type": content_type,
    }

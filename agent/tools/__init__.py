"""Agent tools — functions the AI agent can call to accomplish tasks."""

from agent.tools.analyze import ANALYZE_TOOL, handle_analyze
from agent.tools.email_tools import (
    EMAIL_CLASSIFY_TOOL,
    EMAIL_DRAFT_TOOL,
    handle_classify_email,
    handle_draft_email,
)
from agent.tools.extract import EXTRACT_TOOL, handle_extract
from agent.tools.knowledge import KNOWLEDGE_TOOL, handle_search_knowledge
from agent.tools.lookup import LOOKUP_TOOL, handle_lookup_order
from agent.tools.pipeline import PIPELINE_TOOL, handle_run_pipeline
from agent.tools.scraper import SCRAPE_TOOL, handle_scrape_url
from agent.tools.summarize import SUMMARIZE_TOOL, handle_summarize

# Registry of all available tools
TOOLS = [
    ANALYZE_TOOL,
    EXTRACT_TOOL,
    SUMMARIZE_TOOL,
    PIPELINE_TOOL,
    KNOWLEDGE_TOOL,
    EMAIL_CLASSIFY_TOOL,
    EMAIL_DRAFT_TOOL,
    LOOKUP_TOOL,
    SCRAPE_TOOL,
]

TOOL_HANDLERS = {
    "analyze_document": handle_analyze,
    "extract_data": handle_extract,
    "summarize": handle_summarize,
    "run_pipeline": handle_run_pipeline,
    "search_knowledge": handle_search_knowledge,
    "classify_email": handle_classify_email,
    "draft_email_reply": handle_draft_email,
    "lookup_order": handle_lookup_order,
    "scrape_url": handle_scrape_url,
}

__all__ = ["TOOLS", "TOOL_HANDLERS"]

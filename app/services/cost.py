"""Token cost calculation service.

Calculates the USD cost of API calls based on Claude Sonnet pricing.
Shows users what their agent runs actually cost — a key production metric.
"""

from __future__ import annotations

# Claude Sonnet 4 pricing (USD per 1M tokens)
_INPUT_PRICE_PER_M = 3.0
_OUTPUT_PRICE_PER_M = 15.0


def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate the USD cost of an API call.

    Args:
        input_tokens: Number of input tokens used.
        output_tokens: Number of output tokens generated.

    Returns:
        Cost in USD as a float.
    """
    input_cost = (input_tokens / 1_000_000) * _INPUT_PRICE_PER_M
    output_cost = (output_tokens / 1_000_000) * _OUTPUT_PRICE_PER_M
    return round(input_cost + output_cost, 6)


def format_cost(cost_usd: float) -> str:
    """Format a cost value for display.

    Args:
        cost_usd: Cost in USD.

    Returns:
        Formatted string like "$0.0034" or "$1.25".
    """
    if cost_usd < 0.01:
        return f"${cost_usd:.4f}"
    return f"${cost_usd:.2f}"

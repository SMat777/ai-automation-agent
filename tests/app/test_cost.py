"""Tests for the cost calculation service."""

import pytest

from app.services.cost import calculate_cost, format_cost


class TestCalculateCost:
    """Test token-to-DKK cost calculation."""

    def test_zero_tokens_returns_zero(self):
        assert calculate_cost(0, 0) == 0.0

    def test_input_tokens_cost(self):
        # Claude Sonnet: $3 per 1M input tokens
        cost = calculate_cost(input_tokens=1_000_000, output_tokens=0)
        assert cost == pytest.approx(3.0, abs=0.01)

    def test_output_tokens_cost(self):
        # Claude Sonnet: $15 per 1M output tokens
        cost = calculate_cost(input_tokens=0, output_tokens=1_000_000)
        assert cost == pytest.approx(15.0, abs=0.01)

    def test_combined_cost(self):
        cost = calculate_cost(input_tokens=1000, output_tokens=500)
        assert cost > 0

    def test_returns_float(self):
        result = calculate_cost(100, 50)
        assert isinstance(result, float)


class TestFormatCost:
    """Test cost formatting."""

    def test_formats_small_cost(self):
        result = format_cost(0.003)
        assert "$" in result or "kr" in result.lower() or "0.003" in result

    def test_formats_zero(self):
        result = format_cost(0.0)
        assert "0" in result

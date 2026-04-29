"""Order lookup tool — simulates querying an order management system.

In production this would connect to a real database or API (e.g., Codon).
For the demo, we use realistic mock data to show the full agent workflow.
"""

from __future__ import annotations

from typing import Any

LOOKUP_TOOL = {
    "name": "lookup_order",
    "description": (
        "Look up order status by order ID. Returns shipping status, "
        "delivery estimate, and order details. Use this when a customer "
        "asks about their order."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "The order ID to look up (e.g., '12345')",
            },
        },
        "required": ["order_id"],
    },
}

# Realistic mock data — simulates an order management system
_MOCK_ORDERS: dict[str, dict[str, Any]] = {
    "12345": {
        "order_id": "12345",
        "customer": "Fertility Clinic Copenhagen",
        "status": "shipped",
        "shipping_date": "2026-07-10",
        "estimated_delivery": "2026-07-14",
        "tracking_number": "DK-2026-78901",
        "items": [
            {"product": "Donor Profile #A-2847", "quantity": 2, "unit": "straws"},
        ],
        "total": "€1,200.00",
    },
    "12346": {
        "order_id": "12346",
        "customer": "IVF Center Aarhus",
        "status": "processing",
        "estimated_shipping": "2026-07-16",
        "items": [
            {"product": "Donor Profile #B-1923", "quantity": 4, "unit": "straws"},
            {"product": "Donor Profile #C-5571", "quantity": 2, "unit": "straws"},
        ],
        "total": "€3,600.00",
    },
    "12347": {
        "order_id": "12347",
        "customer": "London Fertility Group",
        "status": "delivered",
        "delivery_date": "2026-07-08",
        "items": [
            {"product": "Donor Profile #A-1102", "quantity": 1, "unit": "straws"},
        ],
        "total": "€600.00",
    },
}


def handle_lookup_order(
    order_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Look up an order by ID.

    Supports both direct keyword arguments (agent dispatch path) and the
    legacy dict-based call style used in older tests/helpers.
    """
    # Backward compatibility: allow handle_lookup_order({"order_id": ...})
    if isinstance(order_id, dict):
        params = order_id
        order_id = params.get("order_id")

    # Extra fallback for callers that pass a "params" kwarg explicitly
    if not order_id and isinstance(kwargs.get("params"), dict):
        order_id = kwargs["params"].get("order_id")

    if not order_id:
        return {"error": "Missing required parameter: order_id"}

    # Strip common prefixes
    clean_id = order_id.lstrip("#").strip()

    order = _MOCK_ORDERS.get(clean_id)
    if not order:
        return {
            "status": "not_found",
            "message": f"No order found with ID {clean_id}",
        }

    return {
        "status": "found",
        "order": order,
    }

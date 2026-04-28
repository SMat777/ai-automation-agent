"""Shared Pydantic response schemas used across multiple routers."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ToolResponse(BaseModel):
    """Standard envelope for successful tool responses."""

    success: bool
    data: dict[str, Any]

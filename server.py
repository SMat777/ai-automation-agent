"""Backwards-compatibility shim.

The real application lives in app/main.py now. This module re-exports the
FastAPI instance so existing commands like `uvicorn server:app` still work.
"""

from app.main import app

__all__ = ["app"]

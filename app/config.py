"""Application configuration — single source of truth for runtime settings.

All settings come from environment variables (or a .env file in development).
This is our 12-factor config boundary — no hardcoded secrets, no scattered
os.getenv() calls across the codebase.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables.

    Access via ``get_settings()`` — the result is cached so reads are cheap.
    """

    # ── Database ──────────────────────────────────────────────────────────
    # SQLite file in the repo root for development (zero-friction).
    # In production, set DATABASE_URL to a postgresql:// URL.
    database_url: str = Field(
        default="sqlite:///./app.db",
        description="SQLAlchemy database URL. SQLite file in dev, Postgres in prod.",
    )

    # ── Anthropic ─────────────────────────────────────────────────────────
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key. When absent, the app runs in demo mode.",
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Default Claude model for agent runs.",
    )

    # ── App meta ──────────────────────────────────────────────────────────
    app_name: str = "AI Automation Agent"
    app_version: str = "0.5.0"
    log_level: str = Field(default="INFO", description="Logging level.")

    # ── Pydantic settings config ──────────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_sqlite(self) -> bool:
        """True if the configured database is SQLite (affects engine options)."""
        return self.database_url.startswith("sqlite")

    @property
    def is_postgres(self) -> bool:
        """True if the configured database is Postgres."""
        return self.database_url.startswith("postgresql")


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance.

    FastAPI endpoints inject this via ``Depends(get_settings)`` — the cache
    ensures settings are parsed once per process and shared thereafter.
    """
    return Settings()

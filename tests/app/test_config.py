"""Tests for app.config — environment-driven settings."""

from __future__ import annotations

import pytest

from app.config import Settings, get_settings


class TestSettings:
    def test_defaults(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        """Without env vars, defaults kick in: SQLite file + demo mode."""
        # Point Settings at an empty env file so it doesn't pick up a real .env
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./app.db")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        settings = Settings(_env_file=None)

        assert settings.is_sqlite is True
        assert settings.is_postgres is False
        assert settings.anthropic_api_key is None
        assert settings.log_level == "INFO"

    def test_postgres_url_detection(self) -> None:
        settings = Settings(
            _env_file=None,
            database_url="postgresql://user:pw@localhost/db",
        )
        assert settings.is_postgres is True
        assert settings.is_sqlite is False

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Env vars take precedence over defaults."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./custom.db")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        settings = Settings(_env_file=None)

        assert settings.database_url == "sqlite:///./custom.db"
        assert settings.anthropic_api_key == "sk-test-key"
        assert settings.log_level == "DEBUG"


class TestGetSettings:
    def test_returns_cached_instance(self) -> None:
        """get_settings() should return the same object each call (lru_cache)."""
        a = get_settings()
        b = get_settings()
        assert a is b

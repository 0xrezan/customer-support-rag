"""Settings loading tests."""

from __future__ import annotations

import pytest

from app.config import Environment, Settings
from app.lifespan import _validate_settings


class TestSettings:
    def test_ignores_unprefixed_debug_environment_variable(self, monkeypatch) -> None:
        monkeypatch.setenv("DEBUG", "release")
        monkeypatch.delenv("APP_DEBUG", raising=False)

        settings = Settings(_env_file=None)

        assert settings.debug is False

    def test_reads_prefixed_debug_environment_variable(self, monkeypatch) -> None:
        monkeypatch.setenv("DEBUG", "release")
        monkeypatch.setenv("APP_DEBUG", "true")

        settings = Settings(_env_file=None)

        assert settings.debug is True

    def test_production_rejects_short_admin_token(self) -> None:
        settings = Settings(
            _env_file=None,
            app_env=Environment.PRODUCTION,
            admin_api_token="short",
            cors_origins=["https://support.example.com"],
        )

        with pytest.raises(RuntimeError, match="ADMIN_API_TOKEN"):
            _validate_settings(settings)

    def test_production_rejects_wildcard_cors_with_credentials(self) -> None:
        settings = Settings(
            _env_file=None,
            app_env=Environment.PRODUCTION,
            admin_api_token="x" * 32,
            cors_origins=["*"],
        )

        with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
            _validate_settings(settings)

    def test_production_rejects_debug_mode(self, monkeypatch) -> None:
        monkeypatch.setenv("APP_DEBUG", "true")
        settings = Settings(
            _env_file=None,
            app_env=Environment.PRODUCTION,
            admin_api_token="x" * 32,
            cors_origins=["https://support.example.com"],
        )

        with pytest.raises(RuntimeError, match="APP_DEBUG"):
            _validate_settings(settings)

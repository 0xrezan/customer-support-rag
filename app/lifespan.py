"""FastAPI lifespan — startup / shutdown resource wiring."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from app.config import Settings, get_settings
from app.containers import Container
from app.logging import get_logger, setup_logging

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from fastapi import FastAPI

logger = get_logger(__name__)

_INSECURE_TOKENS = {"changeme-admin-token-here", "changeme", ""}
_MIN_ADMIN_TOKEN_LENGTH = 32


def _validate_settings(settings: Settings) -> None:
    """Raise on dangerous defaults that must be changed before production."""
    token = settings.admin_api_token.get_secret_value()
    if settings.is_production:
        if token in _INSECURE_TOKENS or len(token) < _MIN_ADMIN_TOKEN_LENGTH:
            raise RuntimeError(
                "ADMIN_API_TOKEN must be a non-default secret with at least "
                f"{_MIN_ADMIN_TOKEN_LENGTH} characters before running in production."
            )
        if "*" in settings.cors_origins:
            raise RuntimeError(
                "CORS_ORIGINS cannot contain '*' in production because admin "
                "endpoints use credentialed requests."
            )
        if settings.debug:
            raise RuntimeError("APP_DEBUG must be false in production.")

    if token in _INSECURE_TOKENS:
        # In development, just warn loudly
        import warnings

        warnings.warn(
            "ADMIN_API_TOKEN is set to a default placeholder. "
            "Change it before deploying to production.",
            stacklevel=1,
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise shared resources on startup; tear them down on shutdown."""

    settings = get_settings()

    # 0. Validate critical config
    _validate_settings(settings)

    # 1. Logging
    setup_logging(
        log_level=settings.log_level,
        json_logs=settings.is_production,
    )
    logger.info("startup.begin", app_env=settings.app_env)

    # 2. Build and wire the DI container
    container = Container(settings=settings)
    await container.init_resources()
    app.state.container = container
    app.state.settings = settings

    logger.info("startup.complete")

    yield  # ── application is running ──

    # 3. Teardown
    logger.info("shutdown.begin")
    await container.close_resources()
    logger.info("shutdown.complete")

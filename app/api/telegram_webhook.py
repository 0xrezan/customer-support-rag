"""Telegram webhook adapter for production deployments.

When ``TELEGRAM_WEBHOOK_ENABLED=true``, the bot receives updates via an
HTTPS POST endpoint instead of long-polling. This is more efficient in
production and works behind load balancers.
"""

from __future__ import annotations

import hmac
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.bot.middlewares.auth import AdminAuthMiddleware
from app.bot.middlewares.correlation import CorrelationMiddleware
from app.bot.middlewares.throttling import ThrottlingMiddleware
from app.bot.routers.admin_upload import router as admin_router
from app.bot.routers.feedback import router as feedback_router
from app.bot.routers.user_chat import router as chat_router
from app.logging import get_logger
from app.security.admin_auth import require_admin_token

logger = get_logger(__name__)

router = APIRouter(prefix="/telegram")

# Module-level bot / dispatcher — initialised lazily on first request.
_bot: Bot | None = None
_dp: Dispatcher | None = None


def _verify_secret(payload: bytes, secret_token: str, header_token: str) -> bool:
    """Verify the ``X-Telegram-Bot-Api-Secret-Token`` header."""
    return hmac.compare_digest(secret_token, header_token)


def _get_bot_and_dp(request: Request) -> tuple[Bot, Dispatcher]:
    """Lazily build the aiogram Bot + Dispatcher, reusing across requests."""
    global _bot, _dp

    if _bot is not None and _dp is not None:
        return _bot, _dp

    settings = request.app.state.settings
    container = request.app.state.container

    _bot = Bot(
        token=settings.telegram_bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    _dp = Dispatcher()
    _dp["container"] = container
    _dp["settings"] = settings

    # Middlewares
    _dp.message.middleware(CorrelationMiddleware())
    _dp.message.middleware(ThrottlingMiddleware())
    _dp.message.middleware(AdminAuthMiddleware(admin_ids=settings.admin_telegram_ids))
    _dp.callback_query.middleware(CorrelationMiddleware())

    # Routers
    _dp.include_router(admin_router)
    _dp.include_router(feedback_router)
    _dp.include_router(chat_router)

    logger.info("webhook.dispatcher_ready")
    return _bot, _dp


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None),
) -> dict[str, str]:
    """Receive Telegram updates via webhook POST."""
    settings = request.app.state.settings

    # Verify secret token if configured
    webhook_secret = settings.telegram_webhook_secret.get_secret_value()
    if webhook_secret:
        if not x_telegram_bot_api_secret_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing secret token header",
            )
        if not _verify_secret(b"", webhook_secret, x_telegram_bot_api_secret_token):
            logger.warning("webhook.invalid_secret")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid secret token",
            )

    body = await request.json()
    bot, dp = _get_bot_and_dp(request)

    update = Update.model_validate(body, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)

    return {"status": "ok"}


@router.post("/set-webhook", dependencies=[Depends(require_admin_token)])
async def set_webhook(request: Request) -> dict[str, Any]:
    """Admin helper to register the webhook URL with Telegram."""
    settings = request.app.state.settings
    bot, _ = _get_bot_and_dp(request)

    webhook_url = settings.telegram_webhook_url
    secret = settings.telegram_webhook_secret.get_secret_value()

    kwargs: dict[str, Any] = {"url": webhook_url}
    if secret:
        kwargs["secret_token"] = secret

    result = await bot.set_webhook(**kwargs)

    logger.info("webhook.set", url=webhook_url, result=result)
    return {"ok": result, "webhook_url": webhook_url}


@router.post("/delete-webhook", dependencies=[Depends(require_admin_token)])
async def delete_webhook(request: Request) -> dict[str, Any]:
    """Admin helper to remove the webhook."""
    bot, _ = _get_bot_and_dp(request)
    result = await bot.delete_webhook()
    logger.info("webhook.deleted", result=result)
    return {"ok": result}

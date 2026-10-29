"""Telegram bot bootstrap for polling / webhook mode."""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from app.bot.middlewares.auth import AdminAuthMiddleware
from app.bot.middlewares.correlation import CorrelationMiddleware
from app.bot.middlewares.throttling import ThrottlingMiddleware
from app.bot.routers.admin_upload import router as admin_router
from app.bot.routers.feedback import router as feedback_router
from app.bot.routers.user_chat import router as chat_router
from app.config import get_settings
from app.containers import Container
from app.logging import get_logger, setup_logging

logger = get_logger(__name__)


async def start_bot() -> None:
    """Build and run the Telegram bot in polling mode."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level, json_logs=settings.is_production)

    bot = Bot(
        token=settings.telegram_bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    dp = Dispatcher()

    # Wire DI container
    container = Container(settings=settings)
    await container.init_resources()
    dp["container"] = container
    dp["settings"] = settings

    # Register middlewares
    dp.message.middleware(CorrelationMiddleware())
    dp.message.middleware(ThrottlingMiddleware())
    dp.message.middleware(AdminAuthMiddleware(admin_ids=settings.admin_telegram_ids))

    dp.callback_query.middleware(CorrelationMiddleware())

    # Register routers
    dp.include_router(admin_router)
    dp.include_router(feedback_router)
    dp.include_router(chat_router)  # catch-all last

    logger.info("bot.starting")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await container.close_resources()
        await bot.session.close()
        logger.info("bot.stopped")


def run() -> None:
    """Entry point for ``scripts/run_bot.py``."""
    asyncio.run(start_bot())

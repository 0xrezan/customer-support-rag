"""Correlation ID propagation middleware."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware

from app.logging import set_correlation_id

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import TelegramObject


class CorrelationMiddleware(BaseMiddleware):
    """Inject a fresh correlation ID for every incoming update."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        cid = set_correlation_id()
        data["correlation_id"] = cid
        return await handler(event, data)

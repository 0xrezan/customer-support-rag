"""Anti-spam throttling middleware — Redis-backed with in-memory fallback."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware

from app.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import Message

logger = get_logger(__name__)

_DEFAULT_RATE_LIMIT = 1.0  # seconds between messages (in-memory fallback)


class ThrottlingMiddleware(BaseMiddleware):
    """Per-user throttle. Uses Redis rate limiter if available, otherwise
    falls back to simple in-memory timestamp check."""

    def __init__(self, rate_limit: float = _DEFAULT_RATE_LIMIT) -> None:
        self._rate_limit = rate_limit
        self._last_message: dict[int, float] = defaultdict(float)
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else 0

        # Try Redis rate limiter from container
        container = data.get("container")
        if container is not None:
            rate_limiter = getattr(container, "rate_limiter", None)
            if rate_limiter is not None:
                allowed = await rate_limiter.is_allowed(str(user_id))
                if not allowed:
                    logger.debug("bot.throttled.redis", user_id=user_id)
                    await event.answer("You're sending messages too fast. Please wait a moment.")
                    return None
                return await handler(event, data)

        # Fallback: in-memory throttle
        now = time.monotonic()
        last = self._last_message[user_id]

        if now - last < self._rate_limit:
            logger.debug("bot.throttled.memory", user_id=user_id)
            return None

        self._last_message[user_id] = now
        return await handler(event, data)

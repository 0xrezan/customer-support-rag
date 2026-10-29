"""Admin allowlist and auth checks middleware."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from aiogram import BaseMiddleware

from app.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import Message

logger = get_logger(__name__)


class AdminAuthMiddleware(BaseMiddleware):
    """Block /upload and other admin commands for non-allowlisted users."""

    _ADMIN_COMMANDS: ClassVar[set[str]] = {"/upload", "/reindex", "/delete"}

    def __init__(self, admin_ids: list[int]) -> None:
        self._admin_ids = set(admin_ids)
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if event.text and any(event.text.startswith(cmd) for cmd in self._ADMIN_COMMANDS):
            user_id = event.from_user.id if event.from_user else 0
            if user_id not in self._admin_ids:
                logger.warning("bot.auth.denied", user_id=user_id, text=event.text)
                await event.answer("You are not authorised to use this command.")
                return None

        # Pass the container into handler data
        if "container" not in data and hasattr(event, "bot"):
            data.get("dispatcher")
            # aiogram stores dp-level data via __getitem__
        return await handler(event, data)

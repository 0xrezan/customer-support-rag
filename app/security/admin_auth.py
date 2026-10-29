"""Admin token and Telegram allowlist validation."""

from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.logging import get_logger

logger = get_logger(__name__)

_bearer = HTTPBearer(auto_error=False)


async def require_admin_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """FastAPI dependency that validates the admin bearer token."""
    settings = request.app.state.settings

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    if not hmac.compare_digest(
        credentials.credentials,
        settings.admin_api_token.get_secret_value(),
    ):
        logger.warning("auth.invalid_admin_token")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token",
        )

    return credentials.credentials


def is_telegram_admin(user_id: int, admin_ids: list[int]) -> bool:
    """Check whether a Telegram user ID is in the admin allowlist."""
    return user_id in admin_ids

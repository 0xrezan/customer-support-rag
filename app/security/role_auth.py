"""Role-based admin auth — RBAC for multiple admin/operator users."""

from __future__ import annotations

import hashlib
import hmac

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.infrastructure.db.models_phase2 import AdminRole
from app.logging import get_logger

logger = get_logger(__name__)

_bearer = HTTPBearer(auto_error=False)


def hash_token(token: str) -> str:
    """Hash an API token for storage comparison."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class RoleChecker:
    """Dependency factory that checks if the authenticated user has the required role."""

    def __init__(self, required_roles: set[AdminRole]) -> None:
        self._required_roles = required_roles

    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    ) -> dict:
        """Validate token and check role. Returns user info dict."""
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header",
            )

        container = request.app.state.container
        admin_repo = getattr(container, "admin_user_repo", None)

        if admin_repo is None:
            # Fallback to simple token check
            settings = request.app.state.settings
            if hmac.compare_digest(
                credentials.credentials,
                settings.admin_api_token.get_secret_value(),
            ):
                return {"role": AdminRole.SUPER_ADMIN, "user_id": "legacy"}
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token",
            )

        token_hash = hash_token(credentials.credentials)
        user = await admin_repo.get_by_token_hash(token_hash)

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or inactive token",
            )

        if AdminRole(user.role) not in self._required_roles:
            logger.warning(
                "auth.role_denied",
                user_id=str(user.id),
                role=user.role,
                required=str(self._required_roles),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' insufficient. Required: {self._required_roles}",
            )

        return {"role": user.role, "user_id": str(user.id), "username": user.username}


# Pre-built role checkers
require_super_admin = RoleChecker({AdminRole.SUPER_ADMIN})
require_admin = RoleChecker({AdminRole.SUPER_ADMIN, AdminRole.ADMIN})
require_operator = RoleChecker({AdminRole.SUPER_ADMIN, AdminRole.ADMIN, AdminRole.OPERATOR})
require_any_role = RoleChecker(set(AdminRole))

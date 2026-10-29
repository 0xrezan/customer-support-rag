"""Role auth security tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.infrastructure.db.models_phase2 import AdminRole
from app.security.role_auth import RoleChecker


@pytest.mark.asyncio
async def test_legacy_fallback_uses_constant_time_token_compare() -> None:
    request = MagicMock()
    request.app.state.container.admin_user_repo = None
    request.app.state.settings.admin_api_token.get_secret_value.return_value = "expected-token"
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="expected-token",
    )
    checker = RoleChecker({AdminRole.SUPER_ADMIN})

    with patch("app.security.role_auth.hmac.compare_digest", return_value=True) as compare:
        result = await checker(request, credentials)

    compare.assert_called_once_with("expected-token", "expected-token")
    assert result["role"] == AdminRole.SUPER_ADMIN

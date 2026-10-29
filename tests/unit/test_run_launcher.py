from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

from app.config import get_settings


def _load_run_module() -> dict[str, Any]:
    return runpy.run_path(Path("run.py"))


def test_launcher_skips_telegram_bot_without_token(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    get_settings.cache_clear()

    commands = _load_run_module()["_build_commands"]()

    names = [name for name, _cmd, _cwd in commands]
    assert "API" in names
    assert "WORKER" in names
    assert "BOT" not in names


def test_launcher_starts_telegram_bot_when_token_is_configured(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:token")
    get_settings.cache_clear()

    commands = _load_run_module()["_build_commands"]()

    names = [name for name, _cmd, _cwd in commands]
    assert "BOT" in names

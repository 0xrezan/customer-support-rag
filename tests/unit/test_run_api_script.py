from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

from app.config import get_settings


def test_development_api_runner_limits_reload_watch_dirs(
    monkeypatch,
) -> None:
    """Dev reload should watch source dirs, not the whole repo including .venv."""
    calls: dict[str, Any] = {}

    def fake_uvicorn_run(*args: Any, **kwargs: Any) -> None:
        calls["args"] = args
        calls["kwargs"] = kwargs

    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("API_PORT", "18080")
    get_settings.cache_clear()
    monkeypatch.setattr("uvicorn.run", fake_uvicorn_run)

    runpy.run_path(Path("scripts/run_api.py"), run_name="__main__")

    assert calls["kwargs"]["reload"] is True
    assert calls["kwargs"]["reload_dirs"] == ["app", "scripts"]

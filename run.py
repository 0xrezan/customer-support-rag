"""Start local services: API, worker, optional Telegram bot, and frontend.

Usage: python run.py

Press Ctrl+C to stop everything.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
CommandSpec = tuple[str, list[str], str | None]


def _flush_stale_dramatiq_messages() -> None:
    """Requeue Dramatiq tasks that got stuck after an unclean shutdown."""
    try:
        from app.config import get_settings
        from app.infrastructure.queue.broker import flush_stale_messages

        settings = get_settings()
        flush_stale_messages(settings.dramatiq_broker_url)
    except Exception as exc:
        print(f"[run.py] Warning: could not flush stale messages: {exc}")
        print("[run.py] Continuing startup anyway...")


def _telegram_token_configured() -> bool:
    from app.config import get_settings

    token = get_settings().telegram_bot_token.get_secret_value().strip()
    return ":" in token


def _build_commands() -> list[CommandSpec]:
    """Build process commands for locally available services."""
    npm_bin = shutil.which("npm")

    commands: list[CommandSpec] = [
        ("API", [sys.executable, "scripts/run_api.py"], None),
        ("WORKER", [sys.executable, "-m", "dramatiq", "app.infrastructure.queue.tasks"], None),
    ]

    if _telegram_token_configured():
        commands.insert(1, ("BOT", [sys.executable, "scripts/run_bot.py"], None))
    else:
        print("[run.py] TELEGRAM_BOT_TOKEN is not configured; skipping Telegram bot")

    if npm_bin and os.path.isdir(FRONTEND_DIR):
        commands.append(("FRONTEND", [npm_bin, "run", "dev"], FRONTEND_DIR))
    else:
        print("[run.py] Warning: npm not found or frontend/ missing - skipping frontend")

    return commands


def main() -> None:
    processes: list[subprocess.Popen] = []

    _flush_stale_dramatiq_messages()
    commands = _build_commands()

    try:
        for name, cmd, cwd in commands:
            print(f"[run.py] Starting {name}: {' '.join(cmd)}")
            proc = subprocess.Popen(cmd, cwd=cwd)
            processes.append(proc)
            time.sleep(1)

        print(f"\n[run.py] All {len(processes)} services running. Ctrl+C to stop.\n")

        while True:
            for i, proc in enumerate(processes):
                ret = proc.poll()
                if ret is not None:
                    name = commands[i][0]
                    print(f"\n[run.py] {name} exited with code {ret}, shutting down...")
                    raise KeyboardInterrupt
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[run.py] Stopping all services...")
        for proc in processes:
            proc.terminate()

        for proc in processes:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

        print("[run.py] All services stopped.")


if __name__ == "__main__":
    main()

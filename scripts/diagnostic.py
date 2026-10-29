"""Validate env, tokens, DB, Redis, Chroma, provider connectivity.

Outputs exactly ``SYSTEM READY`` on success or ``ERROR: [reason]`` on failure.
"""

from __future__ import annotations

import asyncio
import sys

from app.config import get_settings
from app.logging import setup_logging


async def main() -> None:
    setup_logging(log_level="WARNING")
    settings = get_settings()
    errors: list[str] = []

    # 1. Database
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(settings.database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        print("  [OK] Database")
    except Exception as e:
        errors.append(f"Database: {e}")
        print(f"  [FAIL] Database: {e}")

    # 2. Redis
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        await r.ping()
        await r.aclose()
        print("  [OK] Redis")
    except Exception as e:
        errors.append(f"Redis: {e}")
        print(f"  [FAIL] Redis: {e}")

    # 3. ChromaDB
    try:
        import chromadb

        client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        client.heartbeat()
        print("  [OK] ChromaDB")
    except Exception as e:
        errors.append(f"ChromaDB: {e}")
        print(f"  [FAIL] ChromaDB: {e}")

    # 4. OpenAI API key
    if settings.openai_api_key.get_secret_value():
        print("  [OK] OpenAI API key configured")
    else:
        errors.append("OpenAI API key missing")
        print("  [FAIL] OpenAI API key missing")

    # 5. Anthropic API key
    if settings.anthropic_api_key.get_secret_value():
        print("  [OK] Anthropic API key configured")
    else:
        print("  [WARN] Anthropic API key not configured (optional)")

    # 6. Telegram token format
    token = settings.telegram_bot_token.get_secret_value()
    if token and ":" in token:
        print("  [OK] Telegram bot token format")
    else:
        errors.append("Telegram bot token invalid or missing")
        print("  [FAIL] Telegram bot token invalid or missing")

    # Verdict
    print()
    if errors:
        print(f"ERROR: {'; '.join(errors)}")
        sys.exit(1)
    else:
        print("SYSTEM READY")


if __name__ == "__main__":
    asyncio.run(main())

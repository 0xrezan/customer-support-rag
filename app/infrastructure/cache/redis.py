"""Redis client and cache helpers."""

from __future__ import annotations

import redis.asyncio as aioredis

from app.logging import get_logger

logger = get_logger(__name__)


async def create_redis_pool(redis_url: str) -> aioredis.Redis:
    """Create and return an async Redis connection pool."""
    pool: aioredis.Redis = aioredis.from_url(
        redis_url,
        decode_responses=True,
    )
    # Verify connectivity
    await pool.ping()
    logger.info("redis.connected", url=redis_url)
    return pool


async def cache_get(redis: aioredis.Redis, key: str) -> str | None:
    """Get a cached value by key."""
    value = await redis.get(key)
    return value


async def cache_set(
    redis: aioredis.Redis,
    key: str,
    value: str,
    ttl_seconds: int = 300,
) -> None:
    """Set a cached value with TTL."""
    await redis.setex(key, ttl_seconds, value)


async def cache_delete(redis: aioredis.Redis, key: str) -> None:
    """Delete a cached key."""
    await redis.delete(key)

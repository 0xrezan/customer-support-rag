"""Rate-limit persistence per user in Redis using sliding window."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.logging import get_logger

if TYPE_CHECKING:
    import redis.asyncio as aioredis

logger = get_logger(__name__)

_DEFAULT_WINDOW_SECONDS = 60
_DEFAULT_MAX_REQUESTS = 20


class RedisRateLimiter:
    """Sliding-window rate limiter backed by Redis sorted sets.

    Each user has a sorted set keyed by ``rate:{user_id}``. Members are
    request timestamps; the set is trimmed on every check.
    """

    def __init__(
        self,
        redis: aioredis.Redis,
        *,
        window_seconds: int = _DEFAULT_WINDOW_SECONDS,
        max_requests: int = _DEFAULT_MAX_REQUESTS,
        key_prefix: str = "rate",
    ) -> None:
        self._redis = redis
        self._window = window_seconds
        self._max = max_requests
        self._prefix = key_prefix

    async def is_allowed(self, user_id: str) -> bool:
        """Return True if the user is within their rate limit.

        Also records the current request timestamp.
        """
        import time

        key = f"{self._prefix}:{user_id}"
        now = time.time()
        window_start = now - self._window

        pipe = self._redis.pipeline()
        # Remove expired entries
        pipe.zremrangebyscore(key, "-inf", window_start)
        # Count remaining entries
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Set TTL so keys don't leak
        pipe.expire(key, self._window + 10)

        results = await pipe.execute()
        current_count = results[1]

        if current_count >= self._max:
            logger.debug("rate_limiter.blocked", user_id=user_id, count=current_count)
            return False

        return True

    async def remaining(self, user_id: str) -> int:
        """Return how many requests the user has left in the current window."""
        import time

        key = f"{self._prefix}:{user_id}"
        now = time.time()
        window_start = now - self._window

        await self._redis.zremrangebyscore(key, "-inf", window_start)
        current = await self._redis.zcard(key)
        return max(0, self._max - current)

    async def reset(self, user_id: str) -> None:
        """Reset rate limit for a user."""
        key = f"{self._prefix}:{user_id}"
        await self._redis.delete(key)

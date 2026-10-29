"""Dramatiq broker configuration with Redis."""

from __future__ import annotations

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from app.logging import get_logger

logger = get_logger(__name__)

_broker: RedisBroker | None = None

# How often (1/N chance per message) the broker runs maintenance to requeue
# messages from dead workers.  Lower = more frequent.  Default is 100.
_MAINTENANCE_CHANCE: int = 25

# Seconds after which an unacknowledged message is considered dead and is
# requeued.  Default in Dramatiq is 86_400_000 ms (1 day).  We lower it to
# 10 minutes so tasks stuck after a crash are retried quickly.
_REQUEUE_DEADLINE_MS: int = 10 * 60 * 1000  # 10 minutes


def setup_broker(redis_url: str = "redis://redis:6379/1") -> RedisBroker:
    """Create and set the global Dramatiq broker.

    Configures shorter requeue deadlines so messages stuck in the acking
    queue after a worker crash are retried promptly (BUG-2 fix).
    """
    global _broker
    _broker = RedisBroker(
        url=redis_url,
        maintenance_chance=_MAINTENANCE_CHANCE,
        requeue_deadline=_REQUEUE_DEADLINE_MS,
    )
    dramatiq.set_broker(_broker)
    logger.info(
        "dramatiq.broker_ready",
        url=redis_url,
        requeue_deadline_ms=_REQUEUE_DEADLINE_MS,
        maintenance_chance=_MAINTENANCE_CHANCE,
    )
    return _broker


def flush_stale_messages(redis_url: str) -> None:
    """Force-run broker maintenance to requeue messages from dead workers.

    Call this at application startup to recover tasks stuck after an
    unclean shutdown.
    """
    import redis as sync_redis

    try:
        client = sync_redis.from_url(redis_url)
        heartbeat_key = "dramatiq:__heartbeats__"

        # Dramatiq stores heartbeats as a sorted set (zset).
        # Older versions used a hash — detect the type to avoid WRONGTYPE.
        key_type = client.type(heartbeat_key)
        if isinstance(key_type, bytes):
            key_type = key_type.decode()

        if key_type == "zset":
            stale = client.zcard(heartbeat_key) or 0
        elif key_type == "hash":
            stale = client.hlen(heartbeat_key) or 0
        else:
            stale = 0

        if stale:
            logger.info("dramatiq.stale_heartbeats_found", count=stale)
            client.delete(heartbeat_key)
            logger.info("dramatiq.stale_heartbeats_cleared")

        client.close()
    except Exception:
        logger.exception("dramatiq.flush_stale_failed")


def get_broker() -> RedisBroker:
    if _broker is None:
        msg = "Broker not initialised. Call setup_broker() first."
        raise RuntimeError(msg)
    return _broker

# src/database/redis.py
import logging
import redis.asyncio as redis
from src.config.config import settings

# Global placeholders for the connection pool and client wrapper
_redis_pool: redis.ConnectionPool | None = None
_redis_client: redis.Redis | None = None


async def get_redis(logger: logging.Logger) -> redis.Redis:
    """
    Returns the active global Redis client interface linked directly to a
    pre-configured shared worker pool.
    """
    global _redis_client, _redis_pool

    if _redis_client is None:
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        logger.info(f"Initializing Redis Connection Pool at {redis_url}")

        # max_connections prevents leakage under heavy concurrency workloads
        _redis_pool = redis.ConnectionPool.from_url(
            redis_url,
            decode_responses=True,
            max_connections=50,
            socket_timeout=5.0,
            socket_connect_timeout=5.0
        )
        _redis_client = redis.Redis(connection_pool=_redis_pool)

    return _redis_client


async def close_redis(logger: logging.Logger):
    """
    Closes the global client and completely disconnects the connection pool
    during application shutdown.
    """
    global _redis_client, _redis_pool

    if _redis_client:
        logger.info("Closing active Redis client connection...")
        await _redis_client.aclose()
        _redis_client = None

    if _redis_pool:
        logger.info("Disconnecting Redis Connection Pool cleanly...")
        await _redis_pool.disconnect()
        _redis_pool = None


# --- Atomic Core Utility Methods for Key & Metric Lifecycles ---

async def increment_key(key: str, amount: int, logger: logging.Logger) -> int:
    """Atomically increments a string value key by an explicit integer amount."""
    r = await get_redis(logger)
    return await r.incrby(key, amount)


async def get_key(key: str, logger: logging.Logger) -> str | None:
    """Fetches text string content values by key identifier."""
    r = await get_redis(logger)
    return await r.get(key)


async def set_key(key: str, value: str, logger: logging.Logger, expire: int | None = None):
    """Sets a string payload key with an optional time-to-live (TTL) expiration window."""
    r = await get_redis(logger)
    await r.set(key, value, ex=expire)
"""Redis helper utilities."""
from __future__ import annotations

import os
from typing import Optional

from redis.asyncio import Redis

_redis_client: Optional[Redis] = None


async def get_client() -> Redis:
    """Return a singleton Redis client instance."""

    global _redis_client  # noqa: PLW0603
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
        _redis_client = Redis.from_url(redis_url, decode_responses=True)
    return _redis_client


async def set_value(key: str, value: str, ttl: Optional[int] = None) -> None:
    """Set a key with optional expiry."""

    client = await get_client()
    await client.set(key, value, ex=ttl)


async def get_value(key: str) -> Optional[str]:
    """Fetch the string value for the given key."""

    client = await get_client()
    return await client.get(key)


async def close_client() -> None:
    """Close the Redis connection if open."""

    global _redis_client  # noqa: PLW0603
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None

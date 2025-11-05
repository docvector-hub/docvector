"""Redis caching implementation."""

import json
from typing import Any, Optional

import redis.asyncio as redis

from docvector.core import get_logger, settings

logger = get_logger(__name__)


class RedisCache:
    """Redis cache wrapper."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 3600,
        prefix: str = "cache:",
    ):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds
            prefix: Key prefix
        """
        self.redis_url = redis_url or settings.redis_url
        self.default_ttl = default_ttl
        self.prefix = prefix
        self.client: Optional[redis.Redis] = None

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self.client is not None:
            return

        self.client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.redis_max_connections,
        )

        logger.info("Redis cache initialized")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        await self.initialize()

        full_key = self._make_key(key)

        try:
            value = await self.client.get(full_key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning("Cache get error", key=key, error=str(e))

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache."""
        await self.initialize()

        full_key = self._make_key(key)
        ttl = ttl or self.default_ttl

        try:
            await self.client.setex(
                full_key,
                ttl,
                json.dumps(value),
            )
            return True
        except Exception as e:
            logger.warning("Cache set error", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        await self.initialize()

        full_key = self._make_key(key)

        try:
            await self.client.delete(full_key)
            return True
        except Exception as e:
            logger.warning("Cache delete error", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        await self.initialize()

        full_key = self._make_key(key)

        try:
            return await self.client.exists(full_key) > 0
        except Exception as e:
            logger.warning("Cache exists error", key=key, error=str(e))
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        await self.initialize()

        full_pattern = self._make_key(pattern)

        try:
            keys = []
            async for key in self.client.scan_iter(match=full_pattern):
                keys.append(key)

            if keys:
                return await self.client.delete(*keys)

            return 0
        except Exception as e:
            logger.warning("Cache clear error", pattern=pattern, error=str(e))
            return 0

    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Redis cache closed")

    def _make_key(self, key: str) -> str:
        """Create full cache key with prefix."""
        return f"{self.prefix}{key}"

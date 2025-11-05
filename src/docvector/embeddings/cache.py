"""Embedding cache using Redis."""

import hashlib
import json
from typing import Dict, List, Optional

import redis.asyncio as redis

from docvector.core import get_logger, settings

logger = get_logger(__name__)


class EmbeddingCache:
    """Cache embeddings in Redis to avoid regenerating."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        ttl: int = 86400 * 7,  # 7 days default
        prefix: str = "embed:",
    ):
        """
        Initialize embedding cache.

        Args:
            redis_url: Redis connection URL
            ttl: Time-to-live for cached embeddings in seconds
            prefix: Key prefix for cache entries
        """
        self.redis_url = redis_url or settings.redis_url
        self.ttl = ttl
        self.prefix = prefix
        self.client: Optional[redis.Redis] = None

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self.client is not None:
            return

        self.client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=False,  # We'll handle JSON serialization
            max_connections=settings.redis_max_connections,
        )

        logger.info("Embedding cache initialized")

    async def get(self, text: str, model: str) -> Optional[List[float]]:
        """
        Get cached embedding for text.

        Args:
            text: Text to look up
            model: Model name (part of cache key)

        Returns:
            Cached embedding or None if not found
        """
        await self.initialize()

        cache_key = self._make_key(text, model)

        try:
            cached = await self.client.get(cache_key)
            if cached:
                embedding = json.loads(cached)
                logger.debug("Cache hit", key=cache_key[:50])
                return embedding
        except Exception as e:
            logger.warning("Cache get error", error=str(e))

        return None

    async def set(
        self,
        text: str,
        model: str,
        embedding: List[float],
    ) -> None:
        """
        Cache an embedding.

        Args:
            text: Text that was embedded
            model: Model name
            embedding: The embedding vector
        """
        await self.initialize()

        cache_key = self._make_key(text, model)

        try:
            await self.client.setex(
                cache_key,
                self.ttl,
                json.dumps(embedding),
            )
            logger.debug("Cached embedding", key=cache_key[:50])
        except Exception as e:
            logger.warning("Cache set error", error=str(e))

    async def get_many(
        self,
        texts: List[str],
        model: str,
    ) -> Dict[str, List[float]]:
        """
        Get multiple cached embeddings.

        Args:
            texts: List of texts to look up
            model: Model name

        Returns:
            Dict mapping texts to their cached embeddings
        """
        await self.initialize()

        if not texts:
            return {}

        # Build cache keys
        keys = [self._make_key(text, model) for text in texts]

        try:
            # Use pipeline for efficiency
            pipe = self.client.pipeline()
            for key in keys:
                pipe.get(key)

            results = await pipe.execute()

            # Build result dict
            cached = {}
            for text, result in zip(texts, results):
                if result:
                    try:
                        embedding = json.loads(result)
                        cached[text] = embedding
                    except Exception as e:
                        logger.warning("Failed to deserialize cached embedding", error=str(e))

            if cached:
                logger.debug("Cache hits", count=len(cached), total=len(texts))

            return cached

        except Exception as e:
            logger.warning("Cache get_many error", error=str(e))
            return {}

    async def set_many(
        self,
        texts: List[str],
        model: str,
        embeddings: List[List[float]],
    ) -> None:
        """
        Cache multiple embeddings.

        Args:
            texts: List of texts
            model: Model name
            embeddings: List of embedding vectors
        """
        await self.initialize()

        if not texts or not embeddings:
            return

        if len(texts) != len(embeddings):
            logger.warning("Texts and embeddings length mismatch")
            return

        try:
            # Use pipeline for efficiency
            pipe = self.client.pipeline()
            for text, embedding in zip(texts, embeddings):
                cache_key = self._make_key(text, model)
                pipe.setex(
                    cache_key,
                    self.ttl,
                    json.dumps(embedding),
                )

            await pipe.execute()
            logger.debug("Cached embeddings", count=len(texts))

        except Exception as e:
            logger.warning("Cache set_many error", error=str(e))

    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Embedding cache closed")

    def _make_key(self, text: str, model: str) -> str:
        """
        Create cache key from text and model.

        Uses hash of text + model to create a stable key.

        Args:
            text: Text content
            model: Model name

        Returns:
            Cache key
        """
        # Create hash from text + model
        content = f"{model}:{text}"
        hash_value = hashlib.sha256(content.encode()).hexdigest()

        return f"{self.prefix}{hash_value}"

"""Redis-based job queue for managing background tasks."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import redis.asyncio as redis

from docvector.core import get_logger, settings

logger = get_logger(__name__)


class JobQueue:
    """
    Redis-based job queue with priority support.

    Uses Redis sorted sets for priority queue implementation.
    Jobs are stored in PostgreSQL, Redis is used for signaling/coordination.
    """

    # Redis key prefixes
    KEY_PREFIX = "docvector:jobs"
    QUEUE_KEY = f"{KEY_PREFIX}:queue"
    PROCESSING_KEY = f"{KEY_PREFIX}:processing"
    CHANNEL_KEY = f"{KEY_PREFIX}:notifications"

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize job queue."""
        self.redis_url = redis_url or settings.redis_url
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self._redis is not None:
            return

        self._redis = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

        # Test connection
        await self._redis.ping()
        logger.info("Job queue initialized", redis_url=self.redis_url)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._pubsub:
            await self._pubsub.close()
            self._pubsub = None

        if self._redis:
            await self._redis.close()
            self._redis = None

        logger.info("Job queue closed")

    async def enqueue(
        self,
        job_id: UUID,
        priority: int = 0,
        job_type: Optional[str] = None,
    ) -> None:
        """
        Add a job to the queue.

        Args:
            job_id: Job UUID
            priority: Priority score (higher = more priority)
            job_type: Optional job type for logging
        """
        if self._redis is None:
            await self.initialize()

        # Use negative timestamp + priority for scoring
        # This ensures FIFO within same priority
        score = -priority * 1_000_000_000 + datetime.utcnow().timestamp()

        await self._redis.zadd(self.QUEUE_KEY, {str(job_id): score})

        # Publish notification for workers
        await self._redis.publish(
            self.CHANNEL_KEY,
            json.dumps({"event": "job_enqueued", "job_id": str(job_id), "type": job_type}),
        )

        logger.debug("Job enqueued", job_id=str(job_id), priority=priority)

    async def dequeue(self, count: int = 1) -> List[str]:
        """
        Dequeue jobs from the queue.

        Returns list of job IDs (as strings).
        """
        if self._redis is None:
            await self.initialize()

        # Get jobs with lowest scores (highest priority, oldest)
        jobs = await self._redis.zrange(self.QUEUE_KEY, 0, count - 1)

        if jobs:
            # Remove from queue atomically
            await self._redis.zrem(self.QUEUE_KEY, *jobs)

            # Add to processing set
            now = datetime.utcnow().timestamp()
            processing = {job: now for job in jobs}
            await self._redis.zadd(self.PROCESSING_KEY, processing)

        return jobs

    async def mark_completed(self, job_id: UUID) -> None:
        """Mark a job as completed (remove from processing)."""
        if self._redis is None:
            await self.initialize()

        await self._redis.zrem(self.PROCESSING_KEY, str(job_id))

        # Publish notification
        await self._redis.publish(
            self.CHANNEL_KEY,
            json.dumps({"event": "job_completed", "job_id": str(job_id)}),
        )

    async def mark_failed(self, job_id: UUID, will_retry: bool = False) -> None:
        """Mark a job as failed."""
        if self._redis is None:
            await self.initialize()

        await self._redis.zrem(self.PROCESSING_KEY, str(job_id))

        # Publish notification
        await self._redis.publish(
            self.CHANNEL_KEY,
            json.dumps({
                "event": "job_failed",
                "job_id": str(job_id),
                "will_retry": will_retry,
            }),
        )

    async def requeue_for_retry(
        self,
        job_id: UUID,
        delay_seconds: int = 0,
    ) -> None:
        """Requeue a job for retry after delay."""
        if self._redis is None:
            await self.initialize()

        # Remove from processing
        await self._redis.zrem(self.PROCESSING_KEY, str(job_id))

        if delay_seconds > 0:
            # Schedule for later (use future timestamp as score)
            score = datetime.utcnow().timestamp() + delay_seconds
            await self._redis.zadd(f"{self.KEY_PREFIX}:delayed", {str(job_id): score})
        else:
            # Requeue immediately with low priority
            await self.enqueue(job_id, priority=-1)

    async def get_queue_length(self) -> int:
        """Get number of jobs in queue."""
        if self._redis is None:
            await self.initialize()

        return await self._redis.zcard(self.QUEUE_KEY)

    async def get_processing_count(self) -> int:
        """Get number of jobs currently being processed."""
        if self._redis is None:
            await self.initialize()

        return await self._redis.zcard(self.PROCESSING_KEY)

    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        if self._redis is None:
            await self.initialize()

        return {
            "queued": await self.get_queue_length(),
            "processing": await self.get_processing_count(),
            "delayed": await self._redis.zcard(f"{self.KEY_PREFIX}:delayed"),
        }

    async def process_delayed_jobs(self) -> int:
        """Move delayed jobs that are ready to the main queue."""
        if self._redis is None:
            await self.initialize()

        now = datetime.utcnow().timestamp()
        delayed_key = f"{self.KEY_PREFIX}:delayed"

        # Get jobs that are ready (score <= now)
        ready_jobs = await self._redis.zrangebyscore(delayed_key, "-inf", now)

        if ready_jobs:
            # Remove from delayed
            await self._redis.zrem(delayed_key, *ready_jobs)

            # Add to main queue
            for job_id in ready_jobs:
                await self.enqueue(UUID(job_id), priority=-1)

        return len(ready_jobs)

    async def subscribe(self) -> "redis.client.PubSub":
        """Subscribe to job notifications."""
        if self._redis is None:
            await self.initialize()

        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(self.CHANNEL_KEY)
        return self._pubsub

    async def recover_stale_processing(
        self,
        stale_threshold_seconds: int = 600,
    ) -> int:
        """
        Recover jobs that have been processing too long.

        Returns count of recovered jobs.
        """
        if self._redis is None:
            await self.initialize()

        threshold = datetime.utcnow().timestamp() - stale_threshold_seconds

        # Get stale processing jobs
        stale_jobs = await self._redis.zrangebyscore(
            self.PROCESSING_KEY, "-inf", threshold
        )

        if stale_jobs:
            # Remove from processing
            await self._redis.zrem(self.PROCESSING_KEY, *stale_jobs)

            # Requeue them
            for job_id in stale_jobs:
                await self.enqueue(UUID(job_id), priority=-1)

            logger.warning("Recovered stale jobs", count=len(stale_jobs))

        return len(stale_jobs)

    async def clear_queue(self) -> int:
        """Clear all jobs from queue (use with caution)."""
        if self._redis is None:
            await self.initialize()

        count = await self._redis.zcard(self.QUEUE_KEY)
        await self._redis.delete(self.QUEUE_KEY)
        return count

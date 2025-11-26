"""Job repository for database operations."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from docvector.core import get_logger
from docvector.models import Job

logger = get_logger(__name__)


class JobRepository:
    """Repository for job database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        job_type: str,
        source_id: Optional[UUID] = None,
        config: Optional[Dict] = None,
        priority: int = 0,
        max_retries: int = 3,
    ) -> Job:
        """Create a new job."""
        job = Job(
            type=job_type,
            source_id=source_id,
            config=config or {},
            priority=priority,
            max_retries=max_retries,
            status=Job.STATUS_PENDING,
        )
        self.session.add(job)
        await self.session.flush()

        logger.info("Job created", job_id=str(job.id), type=job_type)
        return job

    async def get_by_id(self, job_id: UUID) -> Optional[Job]:
        """Get job by ID."""
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def get_pending_jobs(
        self,
        limit: int = 10,
        job_types: Optional[List[str]] = None,
    ) -> List[Job]:
        """Get pending jobs ready for processing."""
        now = datetime.utcnow()

        query = select(Job).where(
            or_(
                # Pending jobs
                Job.status == Job.STATUS_PENDING,
                # Queued jobs
                Job.status == Job.STATUS_QUEUED,
                # Retrying jobs that are ready
                and_(
                    Job.status == Job.STATUS_RETRYING,
                    or_(Job.next_retry_at.is_(None), Job.next_retry_at <= now),
                ),
                # Stale locked jobs (lock expired)
                and_(
                    Job.status == Job.STATUS_RUNNING,
                    Job.lock_expires_at.is_not(None),
                    Job.lock_expires_at < now,
                ),
            )
        )

        if job_types:
            query = query.where(Job.type.in_(job_types))

        query = query.order_by(Job.priority.desc(), Job.created_at.asc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def lock_job(
        self,
        job_id: UUID,
        worker_id: str,
        lock_duration_seconds: int = 300,
    ) -> bool:
        """
        Attempt to lock a job for processing.

        Returns True if lock was acquired, False otherwise.
        """
        now = datetime.utcnow()
        lock_expires = now + timedelta(seconds=lock_duration_seconds)

        # Atomic update with optimistic locking
        result = await self.session.execute(
            update(Job)
            .where(
                and_(
                    Job.id == job_id,
                    or_(
                        Job.status.in_([Job.STATUS_PENDING, Job.STATUS_QUEUED, Job.STATUS_RETRYING]),
                        and_(
                            Job.status == Job.STATUS_RUNNING,
                            Job.lock_expires_at < now,
                        ),
                    ),
                )
            )
            .values(
                status=Job.STATUS_RUNNING,
                worker_id=worker_id,
                locked_at=now,
                lock_expires_at=lock_expires,
                started_at=now,
                updated_at=now,
            )
        )
        await self.session.flush()

        locked = result.rowcount > 0
        if locked:
            logger.debug("Job locked", job_id=str(job_id), worker_id=worker_id)

        return locked

    async def update_progress(
        self,
        job_id: UUID,
        progress: Dict,
        extend_lock_seconds: int = 300,
    ) -> None:
        """Update job progress and extend lock."""
        now = datetime.utcnow()
        lock_expires = now + timedelta(seconds=extend_lock_seconds)

        await self.session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                progress=progress,
                lock_expires_at=lock_expires,
                updated_at=now,
            )
        )
        await self.session.flush()

    async def complete_job(
        self,
        job_id: UUID,
        result: Optional[Dict] = None,
    ) -> None:
        """Mark job as completed."""
        now = datetime.utcnow()

        await self.session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(
                status=Job.STATUS_COMPLETED,
                result=result or {},
                completed_at=now,
                locked_at=None,
                lock_expires_at=None,
                updated_at=now,
            )
        )
        await self.session.flush()

        logger.info("Job completed", job_id=str(job_id))

    async def fail_job(
        self,
        job_id: UUID,
        error_message: str,
        schedule_retry: bool = True,
    ) -> Job:
        """Mark job as failed, optionally scheduling a retry."""
        now = datetime.utcnow()

        # Get current job state
        job = await self.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        new_retry_count = job.retry_count + 1
        can_retry = new_retry_count < job.max_retries and schedule_retry

        if can_retry:
            # Exponential backoff: 30s, 2min, 8min, 32min...
            delay_seconds = 30 * (4 ** job.retry_count)
            next_retry = now + timedelta(seconds=delay_seconds)

            await self.session.execute(
                update(Job)
                .where(Job.id == job_id)
                .values(
                    status=Job.STATUS_RETRYING,
                    retry_count=new_retry_count,
                    next_retry_at=next_retry,
                    last_error=error_message,
                    error_message=error_message,
                    locked_at=None,
                    lock_expires_at=None,
                    updated_at=now,
                )
            )
            logger.warning(
                "Job failed, scheduling retry",
                job_id=str(job_id),
                retry=new_retry_count,
                next_retry=next_retry.isoformat(),
            )
        else:
            await self.session.execute(
                update(Job)
                .where(Job.id == job_id)
                .values(
                    status=Job.STATUS_FAILED,
                    retry_count=new_retry_count,
                    error_message=error_message,
                    last_error=error_message,
                    completed_at=now,
                    locked_at=None,
                    lock_expires_at=None,
                    updated_at=now,
                )
            )
            logger.error("Job failed permanently", job_id=str(job_id), error=error_message)

        await self.session.flush()

        # Return updated job
        return await self.get_by_id(job_id)

    async def cancel_job(self, job_id: UUID) -> None:
        """Cancel a pending or running job."""
        now = datetime.utcnow()

        await self.session.execute(
            update(Job)
            .where(
                and_(
                    Job.id == job_id,
                    Job.status.in_([Job.STATUS_PENDING, Job.STATUS_QUEUED, Job.STATUS_RUNNING, Job.STATUS_RETRYING]),
                )
            )
            .values(
                status=Job.STATUS_CANCELLED,
                completed_at=now,
                locked_at=None,
                lock_expires_at=None,
                updated_at=now,
            )
        )
        await self.session.flush()

        logger.info("Job cancelled", job_id=str(job_id))

    async def get_jobs_by_source(
        self,
        source_id: UUID,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[Job]:
        """Get jobs for a specific source."""
        query = select(Job).where(Job.source_id == source_id)

        if status:
            query = query.where(Job.status == status)

        query = query.order_by(Job.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recent_jobs(
        self,
        limit: int = 50,
        job_types: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
    ) -> List[Job]:
        """Get recent jobs with optional filtering."""
        query = select(Job)

        if job_types:
            query = query.where(Job.type.in_(job_types))

        if statuses:
            query = query.where(Job.status.in_(statuses))

        query = query.order_by(Job.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def cleanup_stale_jobs(
        self,
        stale_threshold_hours: int = 24,
    ) -> int:
        """Clean up stale running jobs that have expired locks."""
        now = datetime.utcnow()
        threshold = now - timedelta(hours=stale_threshold_hours)

        result = await self.session.execute(
            update(Job)
            .where(
                and_(
                    Job.status == Job.STATUS_RUNNING,
                    Job.locked_at < threshold,
                )
            )
            .values(
                status=Job.STATUS_FAILED,
                error_message="Job timed out (stale lock)",
                completed_at=now,
                locked_at=None,
                lock_expires_at=None,
                updated_at=now,
            )
        )
        await self.session.flush()

        cleaned = result.rowcount
        if cleaned > 0:
            logger.warning("Cleaned up stale jobs", count=cleaned)

        return cleaned

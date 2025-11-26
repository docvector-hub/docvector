"""Job management API routes."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from docvector.api.dependencies import get_session
from docvector.api.schemas.job import (
    CrawlSourceRequest,
    CrawlUrlRequest,
    JobCreate,
    JobListResponse,
    JobResponse,
    JobStatsResponse,
)
from docvector.core import DocVectorException, get_logger
from docvector.db.repositories import SourceRepository
from docvector.models import Job
from docvector.queue import JobQueue, JobRepository

logger = get_logger(__name__)

router = APIRouter()


async def get_job_queue() -> JobQueue:
    """Get job queue instance."""
    queue = JobQueue()
    await queue.initialize()
    return queue


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    request: JobCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new job.

    Jobs are queued for processing by background workers.
    Use this endpoint for custom job types or advanced configuration.
    """
    try:
        job_repo = JobRepository(session)
        job_queue = await get_job_queue()

        try:
            # Validate source if provided
            if request.source_id:
                source_repo = SourceRepository(session)
                source = await source_repo.get_by_id(request.source_id)
                if not source:
                    raise HTTPException(status_code=404, detail="Source not found")

            # Create job in database
            job = await job_repo.create(
                job_type=request.type,
                source_id=request.source_id,
                config=request.config,
                priority=request.priority,
                max_retries=request.max_retries,
            )
            await session.commit()

            # Enqueue for processing
            await job_queue.enqueue(job.id, priority=request.priority, job_type=request.type)

            logger.info("Job created and enqueued", job_id=str(job.id), type=request.type)

            return JobResponse.model_validate(job)

        finally:
            await job_queue.close()

    except HTTPException:
        raise
    except DocVectorException as e:
        raise HTTPException(status_code=400, detail=e.to_dict()) from e
    except Exception as e:
        logger.error("Failed to create job", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/crawl/source", response_model=JobResponse, status_code=201)
async def create_crawl_source_job(
    request: CrawlSourceRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a job to crawl an entire source.

    This will discover and index all pages from the source URL,
    respecting robots.txt and configured limits.
    """
    try:
        job_repo = JobRepository(session)
        job_queue = await get_job_queue()

        try:
            # Validate source
            source_repo = SourceRepository(session)
            source = await source_repo.get_by_id(request.source_id)
            if not source:
                raise HTTPException(status_code=404, detail="Source not found")

            # Build config
            config = {
                "access_level": request.access_level,
            }
            if request.max_depth is not None:
                config["max_depth"] = request.max_depth
            if request.max_pages is not None:
                config["max_pages"] = request.max_pages

            # Create job
            job = await job_repo.create(
                job_type=Job.TYPE_CRAWL_SOURCE,
                source_id=request.source_id,
                config=config,
                priority=request.priority,
            )
            await session.commit()

            # Enqueue
            await job_queue.enqueue(job.id, priority=request.priority, job_type=Job.TYPE_CRAWL_SOURCE)

            logger.info(
                "Crawl source job created",
                job_id=str(job.id),
                source_id=str(request.source_id),
            )

            return JobResponse.model_validate(job)

        finally:
            await job_queue.close()

    except HTTPException:
        raise
    except DocVectorException as e:
        raise HTTPException(status_code=400, detail=e.to_dict()) from e
    except Exception as e:
        logger.error("Failed to create crawl source job", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/crawl/url", response_model=JobResponse, status_code=201)
async def create_crawl_url_job(
    request: CrawlUrlRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a job to crawl a single URL.

    Use this for indexing individual pages.
    """
    try:
        job_repo = JobRepository(session)
        job_queue = await get_job_queue()

        try:
            # Validate source
            source_repo = SourceRepository(session)
            source = await source_repo.get_by_id(request.source_id)
            if not source:
                raise HTTPException(status_code=404, detail="Source not found")

            # Create job
            job = await job_repo.create(
                job_type=Job.TYPE_CRAWL_URL,
                source_id=request.source_id,
                config={
                    "url": request.url,
                    "access_level": request.access_level,
                },
                priority=request.priority,
            )
            await session.commit()

            # Enqueue
            await job_queue.enqueue(job.id, priority=request.priority, job_type=Job.TYPE_CRAWL_URL)

            logger.info(
                "Crawl URL job created",
                job_id=str(job.id),
                url=request.url,
            )

            return JobResponse.model_validate(job)

        finally:
            await job_queue.close()

    except HTTPException:
        raise
    except DocVectorException as e:
        raise HTTPException(status_code=400, detail=e.to_dict()) from e
    except Exception as e:
        logger.error("Failed to create crawl URL job", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("", response_model=JobListResponse)
async def list_jobs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    source_id: Optional[UUID] = Query(None, description="Filter by source"),
    session: AsyncSession = Depends(get_session),
):
    """
    List jobs with optional filtering.

    Returns jobs sorted by creation date (newest first).
    """
    try:
        # Build query
        query = select(Job)

        if status:
            query = query.where(Job.status == status)
        if job_type:
            query = query.where(Job.type == job_type)
        if source_id:
            query = query.where(Job.source_id == source_id)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        query = query.order_by(Job.created_at.desc()).offset(offset).limit(limit)

        result = await session.execute(query)
        jobs = list(result.scalars().all())

        return JobListResponse(
            jobs=[JobResponse.model_validate(j) for j in jobs],
            total=total,
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error("Failed to list jobs", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/stats", response_model=JobStatsResponse)
async def get_job_stats(
    session: AsyncSession = Depends(get_session),
):
    """
    Get job queue statistics.

    Returns counts for queued, processing, and completed jobs.
    """
    try:
        job_queue = await get_job_queue()

        try:
            # Get Redis queue stats
            queue_stats = await job_queue.get_stats()

            # Get database stats
            status_counts = {}
            for status in [Job.STATUS_PENDING, Job.STATUS_RUNNING, Job.STATUS_COMPLETED, Job.STATUS_FAILED]:
                count_result = await session.execute(
                    select(func.count()).where(Job.status == status)
                )
                status_counts[status] = count_result.scalar_one()

            return JobStatsResponse(
                queued=queue_stats.get("queued", 0),
                processing=queue_stats.get("processing", 0),
                delayed=queue_stats.get("delayed", 0),
                pending_db=status_counts.get(Job.STATUS_PENDING, 0),
                running_db=status_counts.get(Job.STATUS_RUNNING, 0),
                completed_db=status_counts.get(Job.STATUS_COMPLETED, 0),
                failed_db=status_counts.get(Job.STATUS_FAILED, 0),
            )

        finally:
            await job_queue.close()

    except Exception as e:
        logger.error("Failed to get job stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get a specific job by ID.

    Returns job details including status, progress, and result.
    """
    try:
        job_repo = JobRepository(session)
        job = await job_repo.get_by_id(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobResponse.model_validate(job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job", job_id=str(job_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{job_id}", status_code=204)
async def cancel_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Cancel a pending or running job.

    Jobs that have already completed cannot be cancelled.
    """
    try:
        job_repo = JobRepository(session)
        job = await job_repo.get_by_id(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status in [Job.STATUS_COMPLETED, Job.STATUS_FAILED, Job.STATUS_CANCELLED]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job with status: {job.status}",
            )

        await job_repo.cancel_job(job_id)
        await session.commit()

        logger.info("Job cancelled", job_id=str(job_id))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel job", job_id=str(job_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{job_id}/retry", response_model=JobResponse, status_code=200)
async def retry_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Retry a failed job.

    Resets the job status and requeues it for processing.
    """
    try:
        job_repo = JobRepository(session)
        job_queue = await get_job_queue()

        try:
            job = await job_repo.get_by_id(job_id)

            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            if job.status not in [Job.STATUS_FAILED, Job.STATUS_CANCELLED]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot retry job with status: {job.status}",
                )

            # Reset job status
            from datetime import datetime

            from sqlalchemy import update

            await session.execute(
                update(Job)
                .where(Job.id == job_id)
                .values(
                    status=Job.STATUS_PENDING,
                    retry_count=0,
                    error_message=None,
                    last_error=None,
                    next_retry_at=None,
                    worker_id=None,
                    locked_at=None,
                    lock_expires_at=None,
                    started_at=None,
                    completed_at=None,
                    updated_at=datetime.utcnow(),
                )
            )
            await session.commit()

            # Requeue
            await job_queue.enqueue(job_id, priority=job.priority, job_type=job.type)

            # Fetch updated job
            updated_job = await job_repo.get_by_id(job_id)

            logger.info("Job retry initiated", job_id=str(job_id))

            return JobResponse.model_validate(updated_job)

        finally:
            await job_queue.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retry job", job_id=str(job_id), error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e

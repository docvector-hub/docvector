"""Background worker for processing crawl jobs."""

import asyncio
import signal
import traceback
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from docvector.core import get_logger, setup_logging
from docvector.db import get_engine
from docvector.db.repositories import SourceRepository
from docvector.models import Job
from docvector.queue import JobQueue, JobRepository
from docvector.services.ingestion_service import IngestionService

logger = get_logger(__name__)


class CrawlWorker:
    """
    Background worker that processes crawl jobs from the queue.

    Features:
    - Polls for pending jobs
    - Locks jobs during processing
    - Handles retries with exponential backoff
    - Updates progress in real-time
    - Graceful shutdown support
    """

    def __init__(
        self,
        worker_id: Optional[str] = None,
        poll_interval: float = 5.0,
        lock_duration: int = 300,
        batch_size: int = 1,
    ):
        """
        Initialize the worker.

        Args:
            worker_id: Unique worker identifier
            poll_interval: Seconds between queue polls
            lock_duration: Job lock duration in seconds
            batch_size: Number of jobs to process concurrently
        """
        self.worker_id = worker_id or f"worker-{uuid4().hex[:8]}"
        self.poll_interval = poll_interval
        self.lock_duration = lock_duration
        self.batch_size = batch_size

        self._running = False
        self._shutdown_event = asyncio.Event()
        self._job_queue: Optional[JobQueue] = None
        self._session_factory = None

    async def start(self) -> None:
        """Start the worker."""
        logger.info("Starting crawl worker", worker_id=self.worker_id)

        # Initialize components
        self._job_queue = JobQueue()
        await self._job_queue.initialize()

        # Create session factory
        engine = get_engine()
        self._session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self._running = True

        # Setup signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._handle_shutdown)

        logger.info("Crawl worker started", worker_id=self.worker_id)

        # Start the main loop
        await self._run_loop()

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        logger.info("Stopping crawl worker", worker_id=self.worker_id)

        self._running = False
        self._shutdown_event.set()

        if self._job_queue:
            await self._job_queue.close()

        logger.info("Crawl worker stopped", worker_id=self.worker_id)

    def _handle_shutdown(self) -> None:
        """Handle shutdown signal."""
        logger.info("Shutdown signal received", worker_id=self.worker_id)
        self._running = False
        self._shutdown_event.set()

    async def _run_loop(self) -> None:
        """Main processing loop."""
        while self._running:
            try:
                # Process delayed jobs
                await self._job_queue.process_delayed_jobs()

                # Recover stale jobs
                await self._job_queue.recover_stale_processing()

                # Poll for jobs
                job_ids = await self._job_queue.dequeue(self.batch_size)

                if job_ids:
                    # Process jobs concurrently
                    tasks = [self._process_job(UUID(job_id)) for job_id in job_ids]
                    await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    # Wait before next poll
                    try:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(),
                            timeout=self.poll_interval,
                        )
                    except asyncio.TimeoutError:
                        pass

            except Exception as e:
                logger.error("Error in worker loop", error=str(e))
                await asyncio.sleep(self.poll_interval)

    async def _process_job(self, job_id: UUID) -> None:
        """Process a single job."""
        async with self._session_factory() as session:
            job_repo = JobRepository(session)

            try:
                # Try to lock the job
                locked = await job_repo.lock_job(
                    job_id=job_id,
                    worker_id=self.worker_id,
                    lock_duration_seconds=self.lock_duration,
                )

                if not locked:
                    logger.debug("Could not lock job", job_id=str(job_id))
                    return

                await session.commit()

                # Get job details
                job = await job_repo.get_by_id(job_id)
                if not job:
                    logger.error("Job not found after locking", job_id=str(job_id))
                    return

                logger.info(
                    "Processing job",
                    job_id=str(job_id),
                    type=job.type,
                    retry=job.retry_count,
                )

                # Process based on job type
                if job.type == Job.TYPE_CRAWL_SOURCE:
                    await self._process_crawl_source(session, job_repo, job)
                elif job.type == Job.TYPE_CRAWL_URL:
                    await self._process_crawl_url(session, job_repo, job)
                else:
                    raise ValueError(f"Unknown job type: {job.type}")

                # Mark as completed
                await job_repo.complete_job(job_id, result=job.progress)
                await self._job_queue.mark_completed(job_id)
                await session.commit()

                logger.info("Job completed successfully", job_id=str(job_id))

            except Exception as e:
                logger.error(
                    "Job failed",
                    job_id=str(job_id),
                    error=str(e),
                    traceback=traceback.format_exc(),
                )

                # Mark as failed with retry
                job = await job_repo.fail_job(
                    job_id=job_id,
                    error_message=str(e),
                    schedule_retry=True,
                )
                await session.commit()

                will_retry = job and job.status == Job.STATUS_RETRYING
                await self._job_queue.mark_failed(job_id, will_retry=will_retry)

                if will_retry:
                    # Calculate delay for retry queue
                    delay = 30 * (4 ** (job.retry_count - 1))
                    await self._job_queue.requeue_for_retry(job_id, delay_seconds=delay)

    async def _process_crawl_source(
        self,
        session: AsyncSession,
        job_repo: JobRepository,
        job: Job,
    ) -> None:
        """Process a crawl_source job."""
        source_repo = SourceRepository(session)
        source = await source_repo.get_by_id(job.source_id)

        if not source:
            raise ValueError(f"Source not found: {job.source_id}")

        # Initialize ingestion service
        ingestion_service = IngestionService(session)
        await ingestion_service.initialize()

        try:
            # Update progress
            await job_repo.update_progress(job.id, {"status": "crawling", "started_at": datetime.utcnow().isoformat()})
            await session.commit()

            # Get config from job or source
            config = {**source.config, **job.config}

            # Perform crawl
            stats = await ingestion_service.ingest_source(
                source=source,
                access_level=config.get("access_level", "private"),
            )

            # Update progress with results
            job.progress = {
                "status": "completed",
                "stats": stats,
                "completed_at": datetime.utcnow().isoformat(),
            }

        finally:
            await ingestion_service.close()

    async def _process_crawl_url(
        self,
        session: AsyncSession,
        job_repo: JobRepository,
        job: Job,
    ) -> None:
        """Process a crawl_url job."""
        config = job.config
        url = config.get("url")
        source_id = job.source_id

        if not url:
            raise ValueError("URL not specified in job config")

        source_repo = SourceRepository(session)
        source = await source_repo.get_by_id(source_id)

        if not source:
            raise ValueError(f"Source not found: {source_id}")

        # Initialize ingestion service
        ingestion_service = IngestionService(session)
        await ingestion_service.initialize()

        try:
            # Update progress
            await job_repo.update_progress(job.id, {"status": "fetching", "url": url})
            await session.commit()

            # Ingest single URL
            document = await ingestion_service.ingest_url(
                source=source,
                url=url,
                access_level=config.get("access_level", "private"),
            )

            # Update progress with results
            job.progress = {
                "status": "completed",
                "document_id": str(document.id),
                "title": document.title,
                "chunks": document.chunk_count,
            }

        finally:
            await ingestion_service.close()


async def run_worker():
    """Run the worker (entry point for CLI)."""
    setup_logging()

    worker = CrawlWorker()

    try:
        await worker.start()
    except KeyboardInterrupt:
        pass
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(run_worker())

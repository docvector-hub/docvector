"""IngestionJob model - track ingestion and processing jobs."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class IngestionJob(Base, UUIDMixin, TimestampMixin):
    """
    Ingestion job tracking.

    Tracks the progress and status of document ingestion and processing jobs.
    """

    __tablename__ = "ingestion_jobs"

    # Foreign keys (nullable if source is deleted)
    source_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Job details
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )

    # Progress tracking
    total_documents: Mapped[int] = mapped_column(Integer, default=0)
    processed_documents: Mapped[int] = mapped_column(Integer, default=0)
    failed_documents: Mapped[int] = mapped_column(Integer, default=0)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0)

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Celery task ID
    task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Configuration used for this job
    config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    source = relationship("Source", back_populates="jobs")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "job_type IN ('full_sync', 'incremental', 'manual')",
            name="valid_job_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="valid_job_status",
        ),
    )

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_documents == 0:
            return 0.0
        return (self.processed_documents / self.total_documents) * 100

    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status in ("pending", "running")

    @property
    def is_finished(self) -> bool:
        """Check if job is finished."""
        return self.status in ("completed", "failed", "cancelled")

    def __repr__(self) -> str:
        return f"<IngestionJob(id={self.id}, type='{self.job_type}', status='{self.status}')>"

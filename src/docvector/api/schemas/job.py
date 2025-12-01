"""Job API schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    """Request to create a new job."""

    type: str = Field(
        ...,
        description="Job type: 'crawl_source', 'crawl_url', or 'reindex'",
        pattern="^(crawl_source|crawl_url|reindex)$",
    )
    source_id: Optional[UUID] = Field(None, description="Source ID for the job")
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Job configuration (e.g., url, access_level)",
    )
    priority: int = Field(0, ge=-10, le=10, description="Job priority (-10 to 10)")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")


class JobResponse(BaseModel):
    """Job response schema."""

    id: UUID
    type: str
    status: str
    source_id: Optional[UUID] = None
    config: Dict[str, Any] = {}
    priority: int = 0
    progress: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    """Response for listing jobs."""

    jobs: List[JobResponse]
    total: int
    limit: int
    offset: int


class JobStatsResponse(BaseModel):
    """Job queue statistics."""

    queued: int = Field(..., description="Jobs waiting in queue")
    processing: int = Field(..., description="Jobs currently being processed")
    delayed: int = Field(..., description="Jobs waiting for retry")
    pending_db: int = Field(0, description="Jobs pending in database")
    running_db: int = Field(0, description="Jobs running in database")
    completed_db: int = Field(0, description="Completed jobs in database")
    failed_db: int = Field(0, description="Failed jobs in database")


class CrawlSourceRequest(BaseModel):
    """Request to create a crawl source job."""

    source_id: UUID = Field(..., description="Source ID to crawl")
    access_level: str = Field(
        "private",
        description="Access level: 'public' or 'private'",
        pattern="^(public|private)$",
    )
    priority: int = Field(0, ge=-10, le=10, description="Job priority")
    max_depth: Optional[int] = Field(None, ge=1, le=10, description="Maximum crawl depth")
    max_pages: Optional[int] = Field(None, ge=1, le=10000, description="Maximum pages to crawl")


class CrawlUrlRequest(BaseModel):
    """Request to create a crawl URL job."""

    source_id: UUID = Field(..., description="Source ID this URL belongs to")
    url: str = Field(..., description="URL to crawl")
    access_level: str = Field(
        "private",
        description="Access level: 'public' or 'private'",
        pattern="^(public|private)$",
    )
    priority: int = Field(0, ge=-10, le=10, description="Job priority")

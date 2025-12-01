"""API schemas (Pydantic models)."""

from .common import HealthResponse
from .ingestion import IngestionResponse, IngestSourceRequest, IngestUrlRequest
from .job import (
    CrawlSourceRequest,
    CrawlUrlRequest,
    JobCreate,
    JobListResponse,
    JobResponse,
    JobStatsResponse,
)
from .search import SearchRequest, SearchResponse, SearchResultSchema
from .source import SourceCreate, SourceResponse, SourceUpdate

__all__ = [
    "SearchRequest",
    "SearchResponse",
    "SearchResultSchema",
    "SourceCreate",
    "SourceResponse",
    "SourceUpdate",
    "HealthResponse",
    "IngestSourceRequest",
    "IngestUrlRequest",
    "IngestionResponse",
    "JobCreate",
    "JobResponse",
    "JobListResponse",
    "JobStatsResponse",
    "CrawlSourceRequest",
    "CrawlUrlRequest",
]

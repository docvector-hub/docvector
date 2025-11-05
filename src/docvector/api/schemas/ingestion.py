"""Ingestion API schemas."""

from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class IngestSourceRequest(BaseModel):
    """Request to ingest entire source."""

    source_id: UUID = Field(..., description="Source ID to ingest")
    access_level: str = Field(
        "private",
        description="Access level: 'public' or 'private'",
        pattern="^(public|private)$",
    )


class IngestUrlRequest(BaseModel):
    """Request to ingest a single URL."""

    source_id: UUID = Field(..., description="Source ID this URL belongs to")
    url: HttpUrl = Field(..., description="URL to ingest")
    access_level: str = Field(
        "private",
        description="Access level: 'public' or 'private'",
        pattern="^(public|private)$",
    )


class IngestionResponse(BaseModel):
    """Ingestion response."""

    success: bool = True
    message: str
    stats: Optional[Dict] = None
    document_id: Optional[UUID] = None


class IngestionStatsResponse(BaseModel):
    """Ingestion statistics response."""

    fetched: int = Field(..., description="Number of documents fetched")
    processed: int = Field(..., description="Number of documents processed")
    chunks_created: int = Field(..., description="Number of chunks created")
    errors: int = Field(..., description="Number of errors")

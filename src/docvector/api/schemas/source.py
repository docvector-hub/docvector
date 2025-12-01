"""Source API schemas."""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SourceCreate(BaseModel):
    """Create source request."""

    name: str = Field(..., description="Source name", min_length=1, max_length=255)
    type: str = Field(
        ...,
        description="Source type: web, git, file, api",
        pattern="^(web|git|file|api)$",
    )
    config: Dict = Field(..., description="Source configuration")
    sync_frequency: Optional[str] = Field(
        None, description="Sync frequency: manual, hourly, daily, weekly"
    )


class SourceUpdate(BaseModel):
    """Update source request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    config: Optional[Dict] = None
    sync_frequency: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|error)$")


class SourceResponse(BaseModel):
    """Source response."""

    id: UUID
    name: str
    type: str
    config: Dict
    status: str
    sync_frequency: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

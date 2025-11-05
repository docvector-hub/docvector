"""Search API schemas."""

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Search request."""

    query: str = Field(..., description="Search query text", min_length=1)
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)
    search_type: str = Field(
        "hybrid",
        description="Search type: 'vector', 'hybrid'",
        pattern="^(vector|hybrid)$",
    )
    access_level: Optional[str] = Field(
        None,
        description="Filter by access level: 'public', 'private', or None for all",
        pattern="^(public|private)$",
    )
    filters: Optional[Dict] = Field(None, description="Optional filters")
    score_threshold: Optional[float] = Field(
        None, description="Minimum similarity score", ge=0, le=1
    )


class SearchResultSchema(BaseModel):
    """Single search result."""

    chunk_id: str
    document_id: str
    score: float
    content: str
    title: Optional[str] = None
    url: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Search response."""

    success: bool = True
    query: str
    results: List[SearchResultSchema]
    total: int
    search_type: str

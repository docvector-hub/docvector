"""Search API routes."""

from fastapi import APIRouter, Depends, HTTPException

from docvector.api.dependencies import get_search_service
from docvector.api.schemas import SearchRequest, SearchResponse, SearchResultSchema
from docvector.core import get_logger
from docvector.services import SearchService

logger = get_logger(__name__)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service),
):
    """
    Search for documents.

    Performs vector similarity search or hybrid search across indexed documents.
    """
    try:
        # Build filters
        filters = request.filters or {}
        if request.access_level:
            filters["access_level"] = request.access_level
        if request.topic:
            filters["topics"] = request.topic
        if request.library_id:
            filters["library_id"] = request.library_id
        if request.version:
            filters["version"] = request.version

        results = await search_service.search(
            query=request.query,
            limit=request.limit,
            search_type=request.search_type,
            filters=filters if filters else None,
            score_threshold=request.score_threshold,
            use_reranking=request.use_reranking,
            max_tokens=request.max_tokens,
        )

        # Convert to schema
        result_schemas = [SearchResultSchema(**r) for r in results]

        return SearchResponse(
            success=True,
            query=request.query,
            results=result_schemas,
            total=len(result_schemas),
            search_type=request.search_type,
        )

    except Exception as e:
        logger.error("Search failed", error=str(e), query=request.query)
        raise HTTPException(status_code=500, detail=str(e)) from e

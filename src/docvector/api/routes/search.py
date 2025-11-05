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
        results = await search_service.search(
            query=request.query,
            limit=request.limit,
            search_type=request.search_type,
            filters=request.filters,
            score_threshold=request.score_threshold,
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
        raise HTTPException(status_code=500, detail=str(e))

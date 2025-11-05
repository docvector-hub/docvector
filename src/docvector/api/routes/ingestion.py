"""Ingestion API routes."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from docvector.api.dependencies import get_session
from docvector.api.schemas import IngestSourceRequest, IngestUrlRequest, IngestionResponse
from docvector.core import get_logger, DocVectorException
from docvector.db.repositories import SourceRepository
from docvector.services import IngestionService

logger = get_logger(__name__)

router = APIRouter()


@router.post("/ingest/source", response_model=IngestionResponse, status_code=202)
async def ingest_source(
    request: IngestSourceRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """
    Ingest all documents from a source.

    This endpoint triggers ingestion in the background and returns immediately.
    The source will be crawled and all discovered documents will be indexed.
    """
    try:
        # Get source
        source_repo = SourceRepository(session)
        source = await source_repo.get_by_id(request.source_id)

        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        # Trigger ingestion in background
        async def run_ingestion():
            try:
                ingestion_service = IngestionService(session)
                await ingestion_service.ingest_source(
                    source=source,
                    access_level=request.access_level,
                )
                await ingestion_service.close()
            except Exception as e:
                logger.error(
                    "Background ingestion failed",
                    source_id=str(source.id),
                    error=str(e),
                )

        background_tasks.add_task(run_ingestion)

        return IngestionResponse(
            success=True,
            message=f"Ingestion started for source: {source.name}",
        )

    except HTTPException:
        raise
    except DocVectorException as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        logger.error("Failed to start ingestion", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/url", response_model=IngestionResponse, status_code=201)
async def ingest_url(
    request: IngestUrlRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Ingest a single URL.

    This endpoint indexes a specific URL and waits for completion.
    Use this for indexing individual pages with specific access levels.

    Example:
    - Index a public documentation page: access_level="public"
    - Index a private internal doc: access_level="private"
    """
    try:
        # Get source
        source_repo = SourceRepository(session)
        source = await source_repo.get_by_id(request.source_id)

        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        # Ingest URL
        ingestion_service = IngestionService(session)
        document = await ingestion_service.ingest_url(
            source=source,
            url=str(request.url),
            access_level=request.access_level,
        )
        await ingestion_service.close()

        return IngestionResponse(
            success=True,
            message=f"URL ingested successfully: {request.url}",
            document_id=document.id,
        )

    except HTTPException:
        raise
    except DocVectorException as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        logger.error("Failed to ingest URL", url=str(request.url), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

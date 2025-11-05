"""Source management API routes."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from docvector.api.dependencies import get_session
from docvector.api.schemas import SourceCreate, SourceResponse, SourceUpdate
from docvector.core import get_logger, DocVectorException
from docvector.services import SourceService

logger = get_logger(__name__)

router = APIRouter()


@router.post("", response_model=SourceResponse, status_code=201)
async def create_source(
    request: SourceCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new documentation source."""
    try:
        service = SourceService(session)
        source = await service.create_source(
            name=request.name,
            type=request.type,
            config=request.config,
            sync_frequency=request.sync_frequency,
        )

        return SourceResponse.model_validate(source)

    except DocVectorException as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        logger.error("Failed to create source", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[SourceResponse])
async def list_sources(
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """List all documentation sources."""
    try:
        service = SourceService(session)
        sources = await service.list_sources(limit=limit, offset=offset)

        return [SourceResponse.model_validate(s) for s in sources]

    except Exception as e:
        logger.error("Failed to list sources", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a documentation source by ID."""
    try:
        service = SourceService(session)
        source = await service.get_source(source_id)

        return SourceResponse.model_validate(source)

    except DocVectorException as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except Exception as e:
        logger.error("Failed to get source", error=str(e), source_id=str(source_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: UUID,
    request: SourceUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a documentation source."""
    try:
        service = SourceService(session)
        source = await service.update_source(
            source_id=source_id,
            name=request.name,
            config=request.config,
            sync_frequency=request.sync_frequency,
            status=request.status,
        )

        return SourceResponse.model_validate(source)

    except DocVectorException as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except Exception as e:
        logger.error("Failed to update source", error=str(e), source_id=str(source_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete a documentation source."""
    try:
        service = SourceService(session)
        success = await service.delete_source(source_id)

        if not success:
            raise HTTPException(status_code=404, detail="Source not found")

    except DocVectorException as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete source", error=str(e), source_id=str(source_id))
        raise HTTPException(status_code=500, detail=str(e))

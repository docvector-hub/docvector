"""Health check routes."""

from datetime import datetime

from fastapi import APIRouter

from docvector.api.schemas import HealthResponse
from docvector.core import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
@router.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns system health status and dependency checks.
    """
    # TODO: Add actual dependency health checks
    # - PostgreSQL connection test
    # - Redis connection test
    # - Qdrant connection test

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.utcnow(),
        dependencies={
            "postgres": {"status": "unknown"},
            "redis": {"status": "unknown"},
            "qdrant": {"status": "unknown"},
        },
    )

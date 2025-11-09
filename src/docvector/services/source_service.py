"""Source management service."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from docvector.core import DocVectorException, get_logger
from docvector.db.repositories import SourceRepository
from docvector.models import Source

logger = get_logger(__name__)


class SourceService:
    """Source management service."""

    def __init__(self, session: AsyncSession):
        """Initialize service."""
        self.session = session
        self.repo = SourceRepository(session)

    async def create_source(
        self,
        name: str,
        type: str,
        config: dict,
        sync_frequency: Optional[str] = None,
    ) -> Source:
        """
        Create a new source.

        Args:
            name: Source name
            type: Source type (web, git, file, api)
            config: Source configuration
            sync_frequency: Sync frequency

        Returns:
            Created source
        """
        logger.info("Creating source", name=name, type=type)

        # Check if name already exists
        existing = await self.repo.get_by_name(name)
        if existing:
            raise DocVectorException(
                code="SOURCE_EXISTS",
                message=f"Source with name '{name}' already exists",
                details={"name": name},
            )

        # Create source
        source = Source(
            name=name,
            type=type,
            config=config,
            sync_frequency=sync_frequency or "manual",
            status="active",
        )

        source = await self.repo.create(source)
        await self.session.commit()

        logger.info("Source created", source_id=str(source.id), name=name)

        return source

    async def get_source(self, source_id: UUID) -> Source:
        """Get source by ID."""
        source = await self.repo.get_by_id(source_id)

        if not source:
            raise DocVectorException(
                code="SOURCE_NOT_FOUND",
                message="Source not found",
                details={"source_id": str(source_id)},
            )

        return source

    async def list_sources(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Source]:
        """List all sources."""
        return await self.repo.list_all(limit=limit, offset=offset)

    async def update_source(
        self,
        source_id: UUID,
        name: Optional[str] = None,
        config: Optional[dict] = None,
        sync_frequency: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Source:
        """Update source."""
        source = await self.get_source(source_id)

        if name:
            source.name = name
        if config:
            source.config = config
        if sync_frequency:
            source.sync_frequency = sync_frequency
        if status:
            source.status = status

        source = await self.repo.update(source)
        await self.session.commit()

        logger.info("Source updated", source_id=str(source_id))

        return source

    async def delete_source(self, source_id: UUID) -> bool:
        """Delete source."""
        logger.info("Deleting source", source_id=str(source_id))

        success = await self.repo.delete(source_id)
        if success:
            await self.session.commit()

        return success

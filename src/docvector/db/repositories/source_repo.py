"""Source repository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from docvector.models import Source


class SourceRepository:
    """Repository for Source model."""

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        self.session = session

    async def create(self, source: Source) -> Source:
        """Create a new source."""
        self.session.add(source)
        await self.session.flush()
        await self.session.refresh(source)
        return source

    async def get_by_id(self, source_id: UUID) -> Optional[Source]:
        """Get source by ID."""
        result = await self.session.execute(
            select(Source).where(Source.id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Source]:
        """Get source by name."""
        result = await self.session.execute(
            select(Source).where(Source.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Source]:
        """List all sources."""
        result = await self.session.execute(
            select(Source)
            .order_by(Source.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_active(self) -> List[Source]:
        """List active sources."""
        result = await self.session.execute(
            select(Source)
            .where(Source.status == "active")
            .order_by(Source.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, source: Source) -> Source:
        """Update source."""
        await self.session.flush()
        await self.session.refresh(source)
        return source

    async def delete(self, source_id: UUID) -> bool:
        """Delete source."""
        source = await self.get_by_id(source_id)
        if source:
            await self.session.delete(source)
            await self.session.flush()
            return True
        return False

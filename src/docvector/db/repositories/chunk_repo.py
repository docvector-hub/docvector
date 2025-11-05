"""Chunk repository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from docvector.models import Chunk


class ChunkRepository:
    """Repository for Chunk model."""

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        self.session = session

    async def create(self, chunk: Chunk) -> Chunk:
        """Create a new chunk."""
        self.session.add(chunk)
        await self.session.flush()
        await self.session.refresh(chunk)
        return chunk

    async def create_many(self, chunks: List[Chunk]) -> List[Chunk]:
        """Create multiple chunks."""
        self.session.add_all(chunks)
        await self.session.flush()

        for chunk in chunks:
            await self.session.refresh(chunk)

        return chunks

    async def get_by_id(self, chunk_id: UUID) -> Optional[Chunk]:
        """Get chunk by ID."""
        result = await self.session.execute(
            select(Chunk).where(Chunk.id == chunk_id)
        )
        return result.scalar_one_or_none()

    async def list_by_document(
        self,
        document_id: UUID,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Chunk]:
        """List chunks for a document."""
        result = await self.session.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.index.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update(self, chunk: Chunk) -> Chunk:
        """Update chunk."""
        await self.session.flush()
        await self.session.refresh(chunk)
        return chunk

    async def delete(self, chunk_id: UUID) -> bool:
        """Delete chunk."""
        chunk = await self.get_by_id(chunk_id)
        if chunk:
            await self.session.delete(chunk)
            await self.session.flush()
            return True
        return False

    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all chunks for a document."""
        result = await self.session.execute(
            select(Chunk).where(Chunk.document_id == document_id)
        )
        chunks = result.scalars().all()

        for chunk in chunks:
            await self.session.delete(chunk)

        await self.session.flush()
        return len(chunks)

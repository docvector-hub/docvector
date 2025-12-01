"""Document repository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from docvector.models import Document


class DocumentRepository:
    """Repository for Document model."""

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        self.session = session

    async def create(self, document: Document) -> Document:
        """Create a new document."""
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID."""
        result = await self.session.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def get_by_url(self, source_id: UUID, url: str) -> Optional[Document]:
        """Get document by source and URL."""
        result = await self.session.execute(
            select(Document).where(
                Document.source_id == source_id,
                Document.url == url,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_content_hash(
        self,
        source_id: UUID,
        content_hash: str,
    ) -> Optional[Document]:
        """Get document by content hash."""
        result = await self.session.execute(
            select(Document).where(
                Document.source_id == source_id,
                Document.content_hash == content_hash,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_source(
        self,
        source_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Document]:
        """List documents for a source."""
        result = await self.session.execute(
            select(Document)
            .where(Document.source_id == source_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_status(
        self,
        status: str,
        limit: int = 100,
    ) -> List[Document]:
        """List documents by status."""
        result = await self.session.execute(
            select(Document)
            .where(Document.status == status)
            .order_by(Document.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_source(self, source_id: UUID) -> int:
        """Count documents for a source."""
        result = await self.session.execute(
            select(func.count(Document.id)).where(Document.source_id == source_id)
        )
        return result.scalar() or 0

    async def update(self, document: Document) -> Document:
        """Update document."""
        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def delete(self, document_id: UUID) -> bool:
        """Delete document."""
        document = await self.get_by_id(document_id)
        if document:
            await self.session.delete(document)
            await self.session.flush()
            return True
        return False

    async def delete_by_source(self, source_id: UUID) -> int:
        """Delete all documents for a source."""
        result = await self.session.execute(select(Document).where(Document.source_id == source_id))
        documents = result.scalars().all()

        for doc in documents:
            await self.session.delete(doc)

        await self.session.flush()
        return len(documents)

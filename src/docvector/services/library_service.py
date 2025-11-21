"""Library resolution and management service."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from docvector.core import get_logger
from docvector.models import Library

logger = get_logger(__name__)


class LibraryService:
    """Service for resolving library names to IDs and managing libraries."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the library service.

        Args:
            db: Database session
        """
        self.db = db

    async def resolve_library_id(self, library_name: str) -> Optional[str]:
        """
        Resolve a library name to its Context7-compatible library ID.

        Examples:
            "mongodb" -> "mongodb/docs"
            "next.js" -> "vercel/next.js"
            "react" -> "facebook/react"

        Args:
            library_name: Library name to resolve

        Returns:
            Library ID string or None if not found
        """
        library_name_lower = library_name.lower().strip()

        # Query by name or aliases
        stmt = select(Library).where(
            or_(
                Library.name.ilike(f"%{library_name_lower}%"),
                Library.library_id.ilike(f"%{library_name_lower}%"),
            )
        )

        result = await self.db.execute(stmt)
        library = result.scalar_one_or_none()

        if library:
            return library.library_id

        # Check aliases (stored as array)
        stmt = select(Library).where(Library.aliases.contains([library_name_lower]))
        result = await self.db.execute(stmt)
        library = result.scalar_one_or_none()

        if library:
            return library.library_id

        logger.warning(f"Library not found: {library_name}")
        return None

    async def get_library_by_id(self, library_id: str) -> Optional[Library]:
        """
        Get a library by its ID.

        Args:
            library_id: Library ID (e.g., "mongodb/docs")

        Returns:
            Library object or None
        """
        stmt = select(Library).where(Library.library_id == library_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_library(
        self,
        library_id: str,
        name: str,
        description: Optional[str] = None,
        homepage_url: Optional[str] = None,
        repository_url: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ) -> Library:
        """
        Create a new library entry.

        Args:
            library_id: Unique library ID (e.g., "mongodb/docs")
            name: Human-readable name
            description: Library description
            homepage_url: Homepage URL
            repository_url: Repository URL
            aliases: Alternative names for the library

        Returns:
            Created Library object
        """
        library = Library(
            library_id=library_id,
            name=name,
            description=description,
            homepage_url=homepage_url,
            repository_url=repository_url,
            aliases=aliases or [],
        )

        self.db.add(library)
        await self.db.commit()
        await self.db.refresh(library)

        logger.info(f"Created library: {library_id}")
        return library

    async def update_library(
        self,
        library_id: str,
        **updates,
    ) -> Optional[Library]:
        """
        Update a library entry.

        Args:
            library_id: Library ID to update
            **updates: Fields to update

        Returns:
            Updated Library object or None if not found
        """
        library = await self.get_library_by_id(library_id)

        if not library:
            return None

        for key, value in updates.items():
            if hasattr(library, key):
                setattr(library, key, value)

        await self.db.commit()
        await self.db.refresh(library)

        logger.info(f"Updated library: {library_id}")
        return library

    async def delete_library(self, library_id: str) -> bool:
        """
        Delete a library entry.

        Args:
            library_id: Library ID to delete

        Returns:
            True if deleted, False if not found
        """
        library = await self.get_library_by_id(library_id)

        if not library:
            return False

        await self.db.delete(library)
        await self.db.commit()

        logger.info(f"Deleted library: {library_id}")
        return True

    async def list_libraries(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Library]:
        """
        List all libraries.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Library objects
        """
        stmt = select(Library).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search_libraries(self, query: str, limit: int = 10) -> List[Library]:
        """
        Search libraries by name or description.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching Library objects
        """
        query_lower = query.lower()

        stmt = (
            select(Library)
            .where(
                or_(
                    Library.name.ilike(f"%{query_lower}%"),
                    Library.library_id.ilike(f"%{query_lower}%"),
                    Library.description.ilike(f"%{query_lower}%"),
                )
            )
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

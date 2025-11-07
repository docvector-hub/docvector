"""Database connection and session management."""

from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from docvector.core import get_logger, settings

logger = get_logger(__name__)

# Global engine instance
_engine: Optional[AsyncEngine] = None


def get_engine() -> AsyncEngine:
    """
    Get or create the database engine.

    Returns:
        AsyncEngine instance
    """
    global _engine

    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.environment == "development",
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        logger.info("Database engine created", url=settings.database_url)

    return _engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session.

    Yields:
        AsyncSession instance
    """
    engine = get_engine()

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db() -> None:
    """Close the database connection."""
    global _engine

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("Database connection closed")

"""Initialize the database by creating all tables."""

import asyncio
from sqlalchemy import text
from docvector.db import get_engine
from docvector.models import Base
from docvector.core import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


async def init_db():
    """Create all database tables."""
    engine = get_engine()
    
    logger.info("Creating database tables...")
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created successfully!")
    
    # Verify tables
    async with engine.connect() as conn:
        # Check if we're using PostgreSQL or SQLite
        if "postgresql" in str(engine.url):
            result = await conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;")
            )
        else:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            )
        tables = result.fetchall()
        logger.info(f"Created tables: {[t[0] for t in tables]}")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())

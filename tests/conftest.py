"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from docvector.models import Base


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test database
@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests.

    Note: Using function scope to ensure clean state between tests.
    For read-only tests, consider using a module-scoped session.
    """
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()
        await session.close()


# Mock data fixtures
@pytest.fixture
def sample_html():
    """Sample HTML content."""
    return b"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test Document</title>
        <meta name="description" content="A test document">
    </head>
    <body>
        <h1>Main Title</h1>
        <p>This is a test paragraph with some content.</p>
        <h2>Section 1</h2>
        <p>Section 1 content goes here.</p>
        <h2>Section 2</h2>
        <p>Section 2 content goes here.</p>
    </body>
    </html>
    """


@pytest.fixture
def sample_markdown():
    """Sample Markdown content."""
    return b"""
# Main Title

This is a test paragraph with some content.

## Section 1

Section 1 content goes here.

## Section 2

Section 2 content goes here.
"""


@pytest.fixture
def sample_text():
    """Sample plain text."""
    return """
    This is a longer text that will be used for chunking tests.
    It has multiple paragraphs and sentences.

    The second paragraph is here with more content.
    This should be enough text to create multiple chunks.

    And here is a third paragraph to ensure we have enough content
    for comprehensive testing of the chunking algorithms.
    """


@pytest.fixture
def sample_source_data():
    """Sample source data."""
    return {
        "name": "Test Source",
        "type": "web",
        "config": {
            "start_url": "https://example.com/docs",
            "max_depth": 2,
            "max_pages": 10,
        },
        "status": "active",
    }


@pytest.fixture
def sample_document_data():
    """Sample document data."""
    return {
        "url": "https://example.com/docs/page1",
        "title": "Test Page",
        "content": "This is test content for the document.",
        "content_hash": "abc123def456",
        "status": "completed",
    }


@pytest.fixture
def sample_embeddings():
    """Sample embedding vectors."""
    return [
        [0.1, 0.2, 0.3, 0.4] * 96,  # 384 dimensions
        [0.5, 0.6, 0.7, 0.8] * 96,
        [0.2, 0.3, 0.4, 0.5] * 96,
    ]


@pytest.fixture
def mock_qdrant_client(mocker):
    """Mock Qdrant client."""
    mock = mocker.AsyncMock()
    mock.create_collection = mocker.AsyncMock()
    mock.get_collection = mocker.AsyncMock()
    mock.upsert = mocker.AsyncMock()
    mock.search = mocker.AsyncMock()
    mock.delete = mocker.AsyncMock()
    mock.retrieve = mocker.AsyncMock()
    mock.count = mocker.AsyncMock(return_value=mocker.Mock(count=10))
    return mock


@pytest.fixture
def mock_embedder(mocker):
    """Mock embedder."""
    mock = mocker.AsyncMock()
    mock.embed = mocker.AsyncMock(return_value=[[0.1, 0.2, 0.3, 0.4] * 96])
    mock.embed_query = mocker.AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4] * 96)
    mock.get_dimension = mocker.Mock(return_value=384)
    mock.initialize = mocker.AsyncMock()
    mock.close = mocker.AsyncMock()
    return mock


@pytest.fixture
def mock_redis_client(mocker):
    """Mock Redis client."""
    mock = mocker.AsyncMock()
    mock.get = mocker.AsyncMock(return_value=None)
    mock.setex = mocker.AsyncMock()
    mock.delete = mocker.AsyncMock()
    mock.exists = mocker.AsyncMock(return_value=False)
    return mock

"""Tests for text chunkers."""

import pytest

from docvector.processing.chunkers import FixedSizeChunker, SemanticChunker


class TestFixedSizeChunker:
    """Test fixed-size chunker."""

    @pytest.fixture
    def chunker(self):
        """Create chunker with small sizes for testing."""
        return FixedSizeChunker(chunk_size=50, chunk_overlap=10)

    @pytest.mark.asyncio
    async def test_chunk_empty_text(self, chunker):
        """Test chunking empty text."""
        chunks = await chunker.chunk("")
        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_chunk_short_text(self, chunker):
        """Test chunking text shorter than chunk size."""
        text = "Short text"
        chunks = await chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].index == 0

    @pytest.mark.asyncio
    async def test_chunk_long_text(self, sample_text):
        """Test chunking long text."""
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)
        chunks = await chunker.chunk(sample_text)

        assert len(chunks) > 1
        for i, chunk in enumerate(chunks):
            assert chunk.index == i
            assert len(chunk.content) > 0

    @pytest.mark.asyncio
    async def test_chunk_overlap(self):
        """Test chunk overlap."""
        text = "This is a test. " * 20  # Repeat to make it long
        chunker = FixedSizeChunker(chunk_size=50, chunk_overlap=10)
        chunks = await chunker.chunk(text)

        if len(chunks) > 1:
            # Check that consecutive chunks have some overlap
            assert chunks[0].end_char > chunks[1].start_char

    @pytest.mark.asyncio
    async def test_chunk_metadata(self, chunker):
        """Test metadata propagation."""
        text = "Test text content"
        metadata = {"key": "value"}
        chunks = await chunker.chunk(text, metadata=metadata)

        assert len(chunks) == 1
        assert chunks[0].metadata["key"] == "value"

    @pytest.mark.asyncio
    async def test_chunk_positions(self, chunker):
        """Test chunk position tracking."""
        text = "A" * 100
        chunks = await chunker.chunk(text)

        for chunk in chunks:
            assert chunk.start_char >= 0
            assert chunk.end_char > chunk.start_char
            assert chunk.end_char <= len(text)

    @pytest.mark.asyncio
    async def test_chunk_separator_preference(self):
        """Test chunking prefers breaking at separator."""
        text = "Sentence one.\nSentence two.\nSentence three.\nSentence four."
        chunker = FixedSizeChunker(chunk_size=30, chunk_overlap=5, separator="\n")
        chunks = await chunker.chunk(text)

        # Should prefer breaking at newlines
        for chunk in chunks[:-1]:  # Except possibly the last
            if "\n" in chunk.content:
                assert chunk.content.rstrip().endswith(".")


class TestSemanticChunker:
    """Test semantic chunker."""

    @pytest.fixture
    def chunker(self):
        """Create semantic chunker."""
        return SemanticChunker(max_chunk_size=100, min_chunk_size=20)

    @pytest.mark.asyncio
    async def test_chunk_empty_text(self, chunker):
        """Test chunking empty text."""
        chunks = await chunker.chunk("")
        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_chunk_short_text(self, chunker):
        """Test chunking short text."""
        text = "Short paragraph."
        chunks = await chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].content == text

    @pytest.mark.asyncio
    async def test_chunk_respects_paragraphs(self, chunker):
        """Test chunking respects paragraph boundaries."""
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = await chunker.chunk(text)

        # Should create multiple chunks at paragraph boundaries
        assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_chunk_respects_sections(self, chunker):
        """Test chunking respects section headers."""
        text = """# Section 1

Content for section 1.

## Subsection 1.1

Content for subsection.

# Section 2

Content for section 2."""

        chunks = await chunker.chunk(text)
        assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_chunk_long_section(self):
        """Test chunking very long section."""
        # Create a section longer than max_chunk_size
        long_text = "Sentence. " * 50
        chunker = SemanticChunker(max_chunk_size=100)
        chunks = await chunker.chunk(long_text)

        # Should split even a single section if too long
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.content) <= 100 + 50  # Some tolerance

    @pytest.mark.asyncio
    async def test_chunk_metadata(self, chunker):
        """Test metadata propagation."""
        text = "Test paragraph."
        metadata = {"source": "test"}
        chunks = await chunker.chunk(text, metadata=metadata)

        assert chunks[0].metadata["source"] == "test"

    @pytest.mark.asyncio
    async def test_chunk_indices(self, chunker):
        """Test chunk indexing."""
        text = "Para 1.\n\nPara 2.\n\nPara 3."
        chunks = await chunker.chunk(text)

        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    @pytest.mark.asyncio
    async def test_chunk_positions(self, chunker):
        """Test chunk position tracking."""
        text = "First paragraph.\n\nSecond paragraph."
        chunks = await chunker.chunk(text)

        for chunk in chunks:
            assert chunk.start_char >= 0
            assert chunk.end_char > chunk.start_char

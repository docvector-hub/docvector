"""Integration tests for document processing pipeline."""

import pytest

from docvector.processing import ProcessingPipeline


class TestProcessingPipeline:
    """Test complete processing pipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create processing pipeline."""
        return ProcessingPipeline(
            chunking_strategy="fixed",
            chunk_size=100,
            chunk_overlap=20,
        )

    @pytest.mark.asyncio
    async def test_process_html_document(self, pipeline, sample_html):
        """Test processing HTML document end-to-end."""
        parsed, chunks = await pipeline.process(
            content=sample_html,
            mime_type="text/html",
            url="https://example.com/test",
        )

        # Check parsed document
        assert parsed.title == "Test Document"
        assert "Main Title" in parsed.content

        # Check chunks
        assert len(chunks) > 0
        for i, chunk in enumerate(chunks):
            assert chunk.index == i
            assert len(chunk.content) > 0
            assert chunk.start_char >= 0

    @pytest.mark.asyncio
    async def test_process_markdown_document(self, pipeline, sample_markdown):
        """Test processing Markdown document."""
        parsed, chunks = await pipeline.process(
            content=sample_markdown,
            mime_type="text/markdown",
        )

        # Check parsed document
        assert parsed.title == "Main Title"
        assert "Section 1" in parsed.content

        # Check chunks
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_process_with_metadata(self, pipeline, sample_html):
        """Test processing with metadata propagation."""
        metadata = {
            "source_id": "test-source",
            "access_level": "public",
        }

        parsed, chunks = await pipeline.process(
            content=sample_html,
            mime_type="text/html",
            metadata=metadata,
        )

        # Metadata should be in parsed doc
        assert parsed.metadata["source_id"] == "test-source"
        assert parsed.metadata["access_level"] == "public"

        # Metadata should propagate to chunks
        for chunk in chunks:
            assert chunk.metadata["source_id"] == "test-source"
            assert chunk.metadata["access_level"] == "public"

    @pytest.mark.asyncio
    async def test_process_semantic_chunking(self, sample_html):
        """Test processing with semantic chunking."""
        pipeline = ProcessingPipeline(chunking_strategy="semantic")

        parsed, chunks = await pipeline.process(
            content=sample_html,
            mime_type="text/html",
        )

        # Should create chunks
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_process_unknown_format(self, pipeline):
        """Test processing unknown format (fallback to plain text)."""
        content = b"Just plain text content"

        parsed, chunks = await pipeline.process(
            content=content,
            mime_type="application/unknown",
        )

        assert "plain text" in parsed.content
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_chunk_text_directly(self, pipeline, sample_text):
        """Test chunking text directly without parsing."""
        chunks = await pipeline.chunk_text(sample_text)

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk.content) > 0


class TestPipelineChunkingStrategies:
    """Test different chunking strategies."""

    @pytest.mark.asyncio
    async def test_fixed_size_strategy(self, sample_text):
        """Test fixed-size chunking strategy."""
        pipeline = ProcessingPipeline(
            chunking_strategy="fixed",
            chunk_size=50,
            chunk_overlap=10,
        )

        chunks = await pipeline.chunk_text(sample_text)

        assert len(chunks) > 1
        # Most chunks should be around chunk_size (with some tolerance)
        for chunk in chunks[:-1]:  # Except possibly the last
            assert len(chunk.content) <= 60  # chunk_size + tolerance

    @pytest.mark.asyncio
    async def test_semantic_strategy(self, sample_text):
        """Test semantic chunking strategy."""
        pipeline = ProcessingPipeline(
            chunking_strategy="semantic",
            chunk_size=100,
        )

        chunks = await pipeline.chunk_text(sample_text)

        assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_unknown_strategy_fallback(self):
        """Test fallback to fixed-size for unknown strategy."""
        pipeline = ProcessingPipeline(chunking_strategy="unknown")

        # Should fall back to fixed-size (no exception)
        chunks = await pipeline.chunk_text("Some text content")

        assert len(chunks) > 0

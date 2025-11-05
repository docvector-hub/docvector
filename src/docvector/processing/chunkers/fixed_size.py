"""Fixed-size text chunker with overlap."""

from typing import Dict, List, Optional

from docvector.core import get_logger, settings

from .base import BaseChunker, TextChunk

logger = get_logger(__name__)


class FixedSizeChunker(BaseChunker):
    """Chunk text into fixed-size pieces with overlap."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separator: str = "\n",
    ):
        """
        Initialize fixed-size chunker.

        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks
            separator: Preferred separator for splitting (newline, space, etc.)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.separator = separator

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

    async def chunk(self, text: str, metadata: Optional[Dict] = None) -> List[TextChunk]:
        """Chunk text with fixed size and overlap."""
        if not text:
            return []

        chunks = []
        start = 0
        index = 0

        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size

            # If this is not the last chunk, try to break at separator
            if end < len(text):
                # Look for separator near the end
                separator_pos = text.rfind(self.separator, start, end)

                # If found and not too far back, use it
                if separator_pos > start + (self.chunk_size // 2):
                    end = separator_pos + len(self.separator)

            # Extract chunk
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk = TextChunk(
                    content=chunk_text,
                    index=index,
                    start_char=start,
                    end_char=end,
                    metadata=metadata.copy() if metadata else {},
                )
                chunks.append(chunk)
                index += 1

            # Move start position (with overlap)
            start = end - self.chunk_overlap

            # Prevent infinite loop
            if start <= end - self.chunk_size:
                start = end

        logger.debug(
            "Fixed-size chunking completed",
            text_length=len(text),
            chunks=len(chunks),
            chunk_size=self.chunk_size,
        )

        return chunks

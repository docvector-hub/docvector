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

        # Run chunking synchronously - it's fast enough for typical document sizes
        chunks = self._chunk_sync(text, metadata)

        logger.debug(
            "Fixed-size chunking completed",
            text_length=len(text),
            chunks=len(chunks),
        )

        return chunks

    def _chunk_sync(self, text: str, metadata: Optional[Dict]) -> List[TextChunk]:
        """Synchronous chunking implementation."""
        chunks = []
        start = 0
        index = 0
        text_len = len(text)
        chunk_size = self.chunk_size
        chunk_overlap = self.chunk_overlap
        separator = self.separator
        sep_len = len(separator)

        # Create shared metadata to avoid repeated copies
        chunk_metadata = metadata.copy() if metadata else {}

        while start < text_len:
            # Calculate end position
            end = min(start + chunk_size, text_len)

            # If this is not the last chunk, try to break at separator
            if end < text_len:
                # Look for separator near the end
                separator_pos = text.rfind(separator, start, end)

                # If found and not too far back, use it
                if separator_pos > start + (chunk_size // 2):
                    end = separator_pos + sep_len

            # Extract chunk
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        content=chunk_text,
                        index=index,
                        start_char=start,
                        end_char=end,
                        metadata=chunk_metadata,
                    )
                )
                index += 1

            # If we've reached the end, stop
            if end >= text_len:
                break

            # Move start position (with overlap)
            # Ensure we always advance by at least 1 character
            new_start = end - chunk_overlap
            if new_start <= start:
                new_start = start + 1
            start = new_start

        return chunks

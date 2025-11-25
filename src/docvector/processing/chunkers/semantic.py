"""Semantic text chunker."""

import re
from typing import Dict, List, Optional

from docvector.core import get_logger, settings

from .base import BaseChunker, TextChunk

logger = get_logger(__name__)

# Pre-compiled regex pattern for section splitting
_SECTION_PATTERN = re.compile(r"\n(?=#{1,6}\s)|(?:\n\n+)")


class SemanticChunker(BaseChunker):
    """
    Chunk text based on semantic boundaries.

    Tries to respect document structure (paragraphs, sections).
    """

    def __init__(
        self,
        max_chunk_size: Optional[int] = None,
        min_chunk_size: int = 100,
    ):
        """
        Initialize semantic chunker.

        Args:
            max_chunk_size: Maximum size of chunks
            min_chunk_size: Minimum size of chunks
        """
        self.max_chunk_size = max_chunk_size or settings.chunk_size
        self.min_chunk_size = min_chunk_size

    async def chunk(self, text: str, metadata: Optional[Dict] = None) -> List[TextChunk]:
        """Chunk text at semantic boundaries."""
        if not text:
            return []

        # Run chunking synchronously - it's fast enough for typical document sizes
        chunks = self._chunk_sync(text, metadata)

        logger.debug(
            "Semantic chunking completed",
            text_length=len(text),
            chunks=len(chunks),
        )

        return chunks

    def _chunk_sync(self, text: str, metadata: Optional[Dict]) -> List[TextChunk]:
        """Synchronous chunking implementation for thread pool execution."""
        # Split into sections (by headers or double newlines)
        sections = _SECTION_PATTERN.split(text)
        sections = [s.strip() for s in sections if s.strip()]

        chunks: List[TextChunk] = []
        index = 0
        char_offset = 0

        # Create a shared metadata dict to avoid repeated copies
        chunk_metadata = metadata.copy() if metadata else {}

        for section in sections:
            section_chunks = self._chunk_section(
                section, char_offset, index, chunk_metadata
            )
            chunks.extend(section_chunks)
            index += len(section_chunks)
            char_offset += len(section) + 2  # +2 for double newline

        return chunks

    def _chunk_section(
        self,
        section: str,
        start_offset: int,
        start_index: int,
        metadata: Dict,
    ) -> List[TextChunk]:
        """Chunk a single section."""
        max_size = self.max_chunk_size

        # If section is small enough, return as single chunk
        if len(section) <= max_size:
            return [
                TextChunk(
                    content=section,
                    index=start_index,
                    start_char=start_offset,
                    end_char=start_offset + len(section),
                    metadata=metadata,
                )
            ]

        # Split large sections into paragraphs
        paragraphs = [p.strip() for p in section.split("\n") if p.strip()]

        chunks: List[TextChunk] = []
        current_chunk: List[str] = []
        current_size = 0
        chunk_start = start_offset

        for para in paragraphs:
            para_size = len(para)

            # If single paragraph is too large, split it by fixed size
            if para_size > max_size:
                # First, save any accumulated chunk
                if current_chunk:
                    chunk_text = "\n".join(current_chunk)
                    chunks.append(
                        TextChunk(
                            content=chunk_text,
                            index=start_index + len(chunks),
                            start_char=chunk_start,
                            end_char=chunk_start + len(chunk_text),
                            metadata=metadata,
                        )
                    )
                    current_chunk = []
                    current_size = 0
                    chunk_start = chunk_start + len(chunk_text) + 1

                # Split oversized paragraph into fixed-size chunks
                para_start = chunk_start
                for i in range(0, para_size, max_size):
                    para_chunk = para[i : i + max_size]
                    chunks.append(
                        TextChunk(
                            content=para_chunk,
                            index=start_index + len(chunks),
                            start_char=para_start + i,
                            end_char=para_start + i + len(para_chunk),
                            metadata=metadata,
                        )
                    )

                # Update position including newline separator
                chunk_start = para_start + para_size + 1
                continue

            # If adding this paragraph exceeds max size
            if current_size + para_size > max_size and current_chunk:
                # Save current chunk
                chunk_text = "\n".join(current_chunk)
                chunks.append(
                    TextChunk(
                        content=chunk_text,
                        index=start_index + len(chunks),
                        start_char=chunk_start,
                        end_char=chunk_start + len(chunk_text),
                        metadata=metadata,
                    )
                )

                # Start new chunk
                current_chunk = [para]
                current_size = para_size
                chunk_start = chunk_start + len(chunk_text) + 1
            else:
                current_chunk.append(para)
                current_size += para_size + 1  # +1 for newline

        # Add final chunk
        if current_chunk:
            chunk_text = "\n".join(current_chunk)
            chunks.append(
                TextChunk(
                    content=chunk_text,
                    index=start_index + len(chunks),
                    start_char=chunk_start,
                    end_char=chunk_start + len(chunk_text),
                    metadata=metadata,
                )
            )

        return chunks

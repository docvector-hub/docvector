"""Semantic text chunker."""

import re
from typing import Dict, List, Optional

from docvector.core import get_logger, settings

from .base import BaseChunker, TextChunk

logger = get_logger(__name__)


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

        # Split into sections (by headers or double newlines)
        sections = self._split_into_sections(text)

        chunks = []
        index = 0
        char_offset = 0

        for section in sections:
            section_chunks = self._chunk_section(section, char_offset, index, metadata)
            chunks.extend(section_chunks)
            index += len(section_chunks)
            char_offset += len(section) + 2  # +2 for double newline

        logger.debug(
            "Semantic chunking completed",
            text_length=len(text),
            sections=len(sections),
            chunks=len(chunks),
        )

        return chunks

    def _split_into_sections(self, text: str) -> List[str]:
        """Split text into sections by headers or paragraphs."""
        # Split by markdown headers or double newlines
        # Headers: # Title, ## Subtitle, etc.
        pattern = r"\n(?=#{1,6}\s)|(?:\n\n+)"

        sections = re.split(pattern, text)

        # Filter out empty sections
        sections = [s.strip() for s in sections if s.strip()]

        return sections

    def _chunk_section(
        self,
        section: str,
        start_offset: int,
        start_index: int,
        metadata: Optional[Dict],
    ) -> List[TextChunk]:
        """Chunk a single section."""
        # If section is small enough, return as single chunk
        if len(section) <= self.max_chunk_size:
            chunk = TextChunk(
                content=section,
                index=start_index,
                start_char=start_offset,
                end_char=start_offset + len(section),
                metadata=metadata.copy() if metadata else {},
            )
            return [chunk]

        # Split large sections into paragraphs
        paragraphs = section.split("\n")
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk = []
        current_size = 0
        chunk_start = start_offset

        for para in paragraphs:
            para_size = len(para)

            # If single paragraph is too large, split it by sentences or fixed size
            if para_size > self.max_chunk_size:
                # First, save any accumulated chunk
                if current_chunk:
                    chunk_text = "\n".join(current_chunk)
                    chunk = TextChunk(
                        content=chunk_text,
                        index=start_index + len(chunks),
                        start_char=chunk_start,
                        end_char=chunk_start + len(chunk_text),
                        metadata=metadata.copy() if metadata else {},
                    )
                    chunks.append(chunk)
                    current_chunk = []
                    current_size = 0
                    chunk_start = chunk_start + len(chunk_text) + 1

                # Split oversized paragraph into fixed-size chunks
                para_start = chunk_start
                for i in range(0, len(para), self.max_chunk_size):
                    para_chunk = para[i : i + self.max_chunk_size]
                    chunk = TextChunk(
                        content=para_chunk,
                        index=start_index + len(chunks),
                        start_char=para_start + i,
                        end_char=para_start + i + len(para_chunk),
                        metadata=metadata.copy() if metadata else {},
                    )
                    chunks.append(chunk)

                # Update position including newline separator
                chunk_start = para_start + len(para) + 1
                # Skip subsequent elif/else since we've fully processed this paragraph
                continue

            # If adding this paragraph exceeds max size
            elif current_size + para_size > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunk_text = "\n".join(current_chunk)
                chunk = TextChunk(
                    content=chunk_text,
                    index=start_index + len(chunks),
                    start_char=chunk_start,
                    end_char=chunk_start + len(chunk_text),
                    metadata=metadata.copy() if metadata else {},
                )
                chunks.append(chunk)

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
            chunk = TextChunk(
                content=chunk_text,
                index=start_index + len(chunks),
                start_char=chunk_start,
                end_char=chunk_start + len(chunk_text),
                metadata=metadata.copy() if metadata else {},
            )
            chunks.append(chunk)

        return chunks

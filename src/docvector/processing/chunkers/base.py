"""Base chunker interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class TextChunk:
    """A chunk of text from a document."""

    content: str
    index: int  # Position in document
    start_char: int  # Starting character position
    end_char: int  # Ending character position
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def length(self) -> int:
        """Get chunk length in characters."""
        return len(self.content)


class BaseChunker(ABC):
    """Abstract base class for text chunkers."""

    @abstractmethod
    async def chunk(self, text: str, metadata: Optional[Dict] = None) -> List[TextChunk]:
        """
        Chunk text into smaller pieces.

        Args:
            text: Text to chunk
            metadata: Optional metadata to add to chunks

        Returns:
            List of text chunks
        """
        pass

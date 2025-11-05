"""Base interface for embedding generators."""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbedder(ABC):
    """Abstract base class for embedding generators."""

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this embedder.

        Returns:
            Embedding dimension
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the embedder (load models, etc.)."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close and cleanup resources."""
        pass

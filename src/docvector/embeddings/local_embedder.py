"""Local embedding generation using sentence-transformers."""

import asyncio
from functools import partial
from typing import List, Optional

from sentence_transformers import SentenceTransformer

from docvector.core import get_logger, settings

from .base import BaseEmbedder

logger = get_logger(__name__)


class LocalEmbedder(BaseEmbedder):
    """Local embedding generator using sentence-transformers."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        batch_size: Optional[int] = None,
    ):
        """
        Initialize local embedder.

        Args:
            model_name: Name of the sentence-transformers model
            device: Device to use (cpu, cuda, mps)
            batch_size: Batch size for encoding
        """
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        self.batch_size = batch_size or settings.embedding_batch_size
        self.model: Optional[SentenceTransformer] = None
        self._dimension: Optional[int] = None

    async def initialize(self) -> None:
        """Load the sentence-transformers model."""
        if self.model is not None:
            return

        logger.info(
            "Loading sentence-transformers model",
            model=self.model_name,
            device=self.device,
        )

        # Load model in executor to avoid blocking
        loop = asyncio.get_event_loop()
        self.model = await loop.run_in_executor(
            None,
            partial(
                SentenceTransformer,
                self.model_name,
                device=self.device,
            ),
        )

        # Get embedding dimension
        self._dimension = self.model.get_sentence_embedding_dimension()

        logger.info(
            "Model loaded successfully",
            model=self.model_name,
            dimension=self._dimension,
        )

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        await self.initialize()

        if not texts:
            return []

        logger.debug("Generating embeddings", count=len(texts))

        # Encode in executor to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            partial(
                self.model.encode,
                texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,  # Normalize for cosine similarity
            ),
        )

        # Convert to list of lists
        result = embeddings.tolist()

        logger.debug("Embeddings generated", count=len(result))

        return result

    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query text."""
        result = await self.embed([text])
        return result[0] if result else []

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        if self._dimension is None:
            raise RuntimeError("Model not initialized. Call initialize() first.")
        return self._dimension

    async def close(self) -> None:
        """Cleanup resources."""
        self.model = None
        logger.info("Local embedder closed")

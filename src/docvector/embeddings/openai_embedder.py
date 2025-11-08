"""OpenAI embedding generation."""

from typing import List, Optional

import httpx

from docvector.core import DocVectorException, get_logger, settings

from .base import BaseEmbedder

logger = get_logger(__name__)


class OpenAIEmbedder(BaseEmbedder):
    """OpenAI embedding generator using their API."""

    # Model dimensions
    MODEL_DIMENSIONS = {
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
    ):
        """
        Initialize OpenAI embedder.

        Args:
            api_key: OpenAI API key
            model: OpenAI embedding model name
            batch_size: Batch size for API calls
        """
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise DocVectorException(
                code="MISSING_API_KEY",
                message="OpenAI API key is required",
                details={"provider": "openai"},
            )

        self.model = model
        self.batch_size = batch_size
        self.client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        if self.client is not None:
            return

        self.client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

        logger.info("OpenAI embedder initialized", model=self.model)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        await self.initialize()

        if not texts:
            return []

        logger.debug("Generating OpenAI embeddings", count=len(texts))

        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batch_embeddings = await self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)

        logger.debug("OpenAI embeddings generated", count=len(all_embeddings))

        return all_embeddings

    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a single batch."""
        try:
            response = await self.client.post(
                "/embeddings",
                json={
                    "input": texts,
                    "model": self.model,
                },
            )
            response.raise_for_status()

            data = response.json()
            embeddings = [item["embedding"] for item in data["data"]]

            return embeddings

        except httpx.HTTPStatusError as e:
            logger.error("OpenAI API error", status=e.response.status_code, error=str(e))
            raise DocVectorException(
                code="OPENAI_API_ERROR",
                message="Failed to generate embeddings",
                details={
                    "status_code": e.response.status_code,
                    "error": str(e),
                },
            )

        except Exception as e:
            logger.error("Unexpected error calling OpenAI API", error=str(e))
            raise DocVectorException(
                code="EMBEDDING_ERROR",
                message="Failed to generate embeddings",
                details={"error": str(e)},
            )

    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query text."""
        result = await self.embed([text])
        return result[0] if result else []

    def get_dimension(self) -> int:
        """Get embedding dimension for the model."""
        return self.MODEL_DIMENSIONS.get(self.model, 1536)

    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.info("OpenAI embedder closed")

"""Search service."""

from typing import Dict, List, Optional

from docvector.core import DocVectorException, get_logger, settings
from docvector.embeddings import BaseEmbedder, LocalEmbedder, OpenAIEmbedder
from docvector.search import HybridSearch, VectorSearch
from docvector.vectordb import BaseVectorDB, QdrantVectorDB

logger = get_logger(__name__)


class SearchService:
    """
    Search service - orchestrates search operations.
    """

    def __init__(self):
        """Initialize search service."""
        self.vectordb: Optional[BaseVectorDB] = None
        self.embedder: Optional[BaseEmbedder] = None
        self.vector_search: Optional[VectorSearch] = None
        self.hybrid_search: Optional[HybridSearch] = None

    async def initialize(self) -> None:
        """Initialize search components."""
        if self.vector_search is not None:
            return

        logger.info("Initializing search service")

        # Initialize vector database
        self.vectordb = QdrantVectorDB()
        await self.vectordb.initialize()

        # Initialize embedder
        if settings.embedding_provider == "openai":
            self.embedder = OpenAIEmbedder()
        else:
            self.embedder = LocalEmbedder()

        await self.embedder.initialize()

        # Initialize search implementations
        self.vector_search = VectorSearch(
            vectordb=self.vectordb,
            embedder=self.embedder,
        )

        self.hybrid_search = HybridSearch(
            vector_search=self.vector_search,
        )

        logger.info("Search service initialized")

    async def search(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "hybrid",
        filters: Optional[Dict] = None,
        score_threshold: Optional[float] = None,
    ) -> List[Dict]:
        """
        Perform search.

        Args:
            query: Search query
            limit: Maximum results
            search_type: 'vector' or 'hybrid'
            filters: Optional filters
            score_threshold: Minimum score

        Returns:
            List of search results as dicts
        """
        await self.initialize()

        logger.info("Performing search", query=query[:50], type=search_type)

        # Choose search implementation
        if search_type == "vector":
            if self.vector_search is None:
                raise DocVectorException(
                    code="SERVICE_NOT_INITIALIZED",
                    message="Vector search not initialized",
                )
            results = await self.vector_search.search(
                query=query,
                limit=limit,
                filters=filters,
                score_threshold=score_threshold,
            )
        else:  # hybrid
            if self.hybrid_search is None:
                raise DocVectorException(
                    code="SERVICE_NOT_INITIALIZED",
                    message="Hybrid search not initialized",
                )
            results = await self.hybrid_search.search(
                query=query,
                limit=limit,
                filters=filters,
                score_threshold=score_threshold,
            )

        # Convert to dict
        results_dict = [
            {
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "score": r.score,
                "content": r.content,
                "title": r.title,
                "url": r.url,
                "metadata": r.metadata,
            }
            for r in results
        ]

        logger.info("Search completed", results=len(results_dict))

        return results_dict

    async def close(self) -> None:
        """Close search service."""
        if self.vectordb:
            await self.vectordb.close()
        if self.embedder:
            await self.embedder.close()

        logger.info("Search service closed")

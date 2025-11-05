"""Vector similarity search."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from docvector.core import get_logger, settings
from docvector.embeddings import BaseEmbedder
from docvector.vectordb import BaseVectorDB, SearchResult

logger = get_logger(__name__)


@dataclass
class SearchResultItem:
    """A single search result."""

    chunk_id: str
    document_id: str
    score: float
    content: str
    title: Optional[str] = None
    url: Optional[str] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class VectorSearch:
    """Vector similarity search."""

    def __init__(
        self,
        vectordb: BaseVectorDB,
        embedder: BaseEmbedder,
        collection_name: Optional[str] = None,
    ):
        """
        Initialize vector search.

        Args:
            vectordb: Vector database client
            embedder: Embedding generator
            collection_name: Name of collection to search
        """
        self.vectordb = vectordb
        self.embedder = embedder
        self.collection_name = collection_name or settings.qdrant_collection

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict] = None,
        score_threshold: Optional[float] = None,
    ) -> List[SearchResultItem]:
        """
        Search for similar documents using vector similarity.

        Args:
            query: Search query text
            limit: Maximum number of results
            filters: Optional filters (source_id, language, etc.)
            score_threshold: Minimum similarity score

        Returns:
            List of search results
        """
        logger.debug(
            "Vector search",
            query=query[:100],
            limit=limit,
            has_filters=filters is not None,
        )

        # Generate query embedding
        query_vector = await self.embedder.embed_query(query)

        # Apply score threshold from settings if not provided
        if score_threshold is None:
            score_threshold = settings.search_min_score

        # Search vector database
        results = await self.vectordb.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            filter=filters,
            score_threshold=score_threshold,
        )

        # Convert to SearchResultItem
        search_results = []
        for result in results:
            item = SearchResultItem(
                chunk_id=result.payload.get("chunk_id", result.id),
                document_id=result.payload.get("document_id", ""),
                score=result.score,
                content=result.payload.get("content", ""),
                title=result.payload.get("title"),
                url=result.payload.get("url"),
                metadata=result.payload,
            )
            search_results.append(item)

        logger.debug("Vector search completed", results=len(search_results))

        return search_results

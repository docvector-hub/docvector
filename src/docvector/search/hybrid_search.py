"""Hybrid search combining vector and keyword search."""

from typing import Dict, List, Optional

from docvector.core import get_logger, settings

from .vector_search import SearchResultItem, VectorSearch

logger = get_logger(__name__)


class HybridSearch:
    """
    Hybrid search combining vector similarity and keyword search.

    Currently implements vector search with weighted scoring.
    Full BM25 keyword search can be added later.
    """

    def __init__(
        self,
        vector_search: VectorSearch,
        vector_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None,
    ):
        """
        Initialize hybrid search.

        Args:
            vector_search: Vector search instance
            vector_weight: Weight for vector scores (0-1)
            keyword_weight: Weight for keyword scores (0-1)
        """
        self.vector_search = vector_search
        self.vector_weight = vector_weight or settings.search_vector_weight
        self.keyword_weight = keyword_weight or settings.search_keyword_weight

        # Normalize weights
        total = self.vector_weight + self.keyword_weight
        self.vector_weight = self.vector_weight / total
        self.keyword_weight = self.keyword_weight / total

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict] = None,
        score_threshold: Optional[float] = None,
    ) -> List[SearchResultItem]:
        """
        Perform hybrid search.

        Args:
            query: Search query
            limit: Maximum results
            filters: Optional filters
            score_threshold: Minimum score threshold

        Returns:
            List of search results
        """
        logger.debug("Hybrid search", query=query[:100], limit=limit)

        # For now, we primarily use vector search
        # In a full implementation, we would also:
        # 1. Run keyword search (BM25) on PostgreSQL full-text search
        # 2. Combine and rerank results

        # Get vector search results
        vector_results = await self.vector_search.search(
            query=query,
            limit=limit * 2,  # Get more to account for reranking
            filters=filters,
            score_threshold=score_threshold,
        )

        # Apply hybrid weighting
        for result in vector_results:
            # In full implementation, combine with keyword score
            # For now, just weight the vector score
            result.score = result.score * self.vector_weight

        # Sort by score and limit
        vector_results.sort(key=lambda x: x.score, reverse=True)
        results = vector_results[:limit]

        logger.debug("Hybrid search completed", results=len(results))

        return results

"""Base interface for vector databases."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class SearchResult:
    """Search result from vector database."""

    def __init__(
        self,
        id: str,
        score: float,
        payload: Dict,
        vector: Optional[List[float]] = None,
    ):
        self.id = id
        self.score = score
        self.payload = payload
        self.vector = vector

    def __repr__(self) -> str:
        return f"<SearchResult(id={self.id}, score={self.score:.4f})>"


class BaseVectorDB(ABC):
    """Abstract base class for vector database implementations."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector database connection and create collections if needed."""
        pass

    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "Cosine",
    ) -> None:
        """
        Create a new collection.

        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors
            distance: Distance metric (Cosine, Euclidean, Dot)
        """
        pass

    @abstractmethod
    async def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        pass

    @abstractmethod
    async def upsert(
        self,
        collection_name: str,
        ids: List[str],
        vectors: List[List[float]],
        payloads: List[Dict],
    ) -> None:
        """
        Insert or update vectors.

        Args:
            collection_name: Name of the collection
            ids: List of point IDs
            vectors: List of vector embeddings
            payloads: List of metadata payloads
        """
        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        filter: Optional[Dict] = None,
        score_threshold: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Search for similar vectors.

        Args:
            collection_name: Name of the collection
            query_vector: Query vector embedding
            limit: Maximum number of results
            filter: Filter conditions
            score_threshold: Minimum similarity score

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    async def delete(
        self,
        collection_name: str,
        ids: List[str],
    ) -> None:
        """
        Delete vectors by IDs.

        Args:
            collection_name: Name of the collection
            ids: List of point IDs to delete
        """
        pass

    @abstractmethod
    async def delete_by_filter(
        self,
        collection_name: str,
        filter: Dict,
    ) -> None:
        """
        Delete vectors by filter.

        Args:
            collection_name: Name of the collection
            filter: Filter conditions
        """
        pass

    @abstractmethod
    async def get(
        self,
        collection_name: str,
        ids: List[str],
    ) -> List[Dict]:
        """
        Get vectors by IDs.

        Args:
            collection_name: Name of the collection
            ids: List of point IDs

        Returns:
            List of points with vectors and payloads
        """
        pass

    @abstractmethod
    async def count(
        self,
        collection_name: str,
        filter: Optional[Dict] = None,
    ) -> int:
        """
        Count vectors in collection.

        Args:
            collection_name: Name of the collection
            filter: Optional filter conditions

        Returns:
            Number of vectors
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the database connection."""
        pass

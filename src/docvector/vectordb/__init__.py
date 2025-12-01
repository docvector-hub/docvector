"""Vector database abstraction layer."""

from .base import BaseVectorDB, SearchResult
from .qdrant_client import QdrantVectorDB

__all__ = ["BaseVectorDB", "QdrantVectorDB", "SearchResult"]

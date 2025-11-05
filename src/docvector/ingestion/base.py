"""Base interface for document fetchers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class FetchedDocument:
    """A document fetched from a source."""

    url: str
    content: bytes
    mime_type: str
    title: Optional[str] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseFetcher(ABC):
    """Abstract base class for document fetchers."""

    @abstractmethod
    async def fetch(self, config: Dict) -> List[FetchedDocument]:
        """
        Fetch documents from a source.

        Args:
            config: Source configuration

        Returns:
            List of fetched documents
        """
        pass

    @abstractmethod
    async def fetch_single(self, url: str, config: Optional[Dict] = None) -> FetchedDocument:
        """
        Fetch a single document.

        Args:
            url: Document URL
            config: Optional configuration

        Returns:
            Fetched document
        """
        pass

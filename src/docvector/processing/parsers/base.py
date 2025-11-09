"""Base parser interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ParsedDocument:
    """Result of parsing a document."""

    content: str
    title: Optional[str] = None
    language: str = "en"
    metadata: Optional[Dict] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    async def parse(self, content: bytes, url: Optional[str] = None) -> ParsedDocument:
        """
        Parse document content.

        Args:
            content: Raw document bytes
            url: Optional URL of the document

        Returns:
            Parsed document
        """
        pass

    @abstractmethod
    def can_parse(self, mime_type: str, file_extension: Optional[str] = None) -> bool:
        """
        Check if this parser can handle the given content type.

        Args:
            mime_type: MIME type of the content
            file_extension: Optional file extension

        Returns:
            True if parser can handle this content
        """
        pass

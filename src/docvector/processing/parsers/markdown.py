"""Markdown document parser."""

from typing import Optional

from markdown_it import MarkdownIt

from docvector.core import get_logger
from docvector.utils import clean_text

from .base import BaseParser, ParsedDocument

logger = get_logger(__name__)


class MarkdownParser(BaseParser):
    """Parse Markdown documents."""

    MIME_TYPES = {"text/markdown", "text/x-markdown"}
    EXTENSIONS = {".md", ".markdown", ".mkd"}

    def __init__(self):
        """Initialize Markdown parser."""
        self.md = MarkdownIt()

    async def parse(self, content: bytes, url: Optional[str] = None) -> ParsedDocument:
        """Parse Markdown content."""
        try:
            # Decode content
            text = content.decode("utf-8", errors="ignore")

            # Extract title (first # heading)
            title = self._extract_title(text)

            # Clean text but preserve structure
            cleaned_text = clean_text(text, remove_html=False)

            metadata = {}
            if url:
                metadata["url"] = url

            return ParsedDocument(
                content=cleaned_text,
                title=title,
                language="en",
                metadata=metadata,
            )

        except Exception as e:
            logger.error("Failed to parse Markdown", error=str(e), url=url)
            raise

    def can_parse(self, mime_type: str, file_extension: Optional[str] = None) -> bool:
        """Check if can parse Markdown."""
        if mime_type in self.MIME_TYPES:
            return True

        if file_extension and file_extension.lower() in self.EXTENSIONS:
            return True

        return False

    def _extract_title(self, text: str) -> Optional[str]:
        """Extract title from Markdown (first heading)."""
        lines = text.split("\n")

        for i, line in enumerate(lines):
            line = line.strip()

            # # Heading style
            if line.startswith("#"):
                # Remove leading #'s
                title = line.lstrip("#").strip()
                if title:
                    return title

            # Underline style
            # Title
            # =====
            if line and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and all(c in "=-" for c in next_line):
                    return line

        return None

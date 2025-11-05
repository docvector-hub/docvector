"""HTML document parser."""

from typing import Optional

from bs4 import BeautifulSoup
from trafilatura import extract

from docvector.core import get_logger
from docvector.utils import clean_text

from .base import BaseParser, ParsedDocument

logger = get_logger(__name__)


class HTMLParser(BaseParser):
    """Parse HTML documents."""

    MIME_TYPES = {"text/html", "application/xhtml+xml"}
    EXTENSIONS = {".html", ".htm", ".xhtml"}

    def __init__(self, use_trafilatura: bool = True):
        """
        Initialize HTML parser.

        Args:
            use_trafilatura: Use trafilatura for better content extraction
        """
        self.use_trafilatura = use_trafilatura

    async def parse(self, content: bytes, url: Optional[str] = None) -> ParsedDocument:
        """Parse HTML content."""
        try:
            # Try trafilatura first for better content extraction
            if self.use_trafilatura:
                text = extract(
                    content,
                    include_links=False,
                    include_images=False,
                    include_tables=True,
                    include_comments=False,
                    output_format="txt",
                )

                if text:
                    # Parse with BeautifulSoup for metadata
                    soup = BeautifulSoup(content, "html.parser")
                    title = self._extract_title(soup)
                    language = self._extract_language(soup)
                    metadata = self._extract_metadata(soup, url)

                    return ParsedDocument(
                        content=clean_text(text),
                        title=title,
                        language=language,
                        metadata=metadata,
                    )

            # Fallback to BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")

            # Remove unwanted elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            # Extract text
            text = soup.get_text(separator="\n", strip=True)

            # Extract metadata
            title = self._extract_title(soup)
            language = self._extract_language(soup)
            metadata = self._extract_metadata(soup, url)

            return ParsedDocument(
                content=clean_text(text),
                title=title,
                language=language,
                metadata=metadata,
            )

        except Exception as e:
            logger.error("Failed to parse HTML", error=str(e), url=url)
            raise

    def can_parse(self, mime_type: str, file_extension: Optional[str] = None) -> bool:
        """Check if can parse HTML."""
        if mime_type in self.MIME_TYPES:
            return True

        if file_extension and file_extension.lower() in self.EXTENSIONS:
            return True

        return False

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title from HTML."""
        # Try <title> tag
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        # Try <h1> tag
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        # Try og:title meta tag
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        return None

    def _extract_language(self, soup: BeautifulSoup) -> str:
        """Extract language from HTML."""
        # Try <html lang="...">
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            lang = html_tag["lang"].strip().lower()
            # Take first part (e.g., "en-US" -> "en")
            return lang.split("-")[0]

        # Try meta tag
        lang_meta = soup.find("meta", attrs={"http-equiv": "Content-Language"})
        if lang_meta and lang_meta.get("content"):
            lang = lang_meta["content"].strip().lower()
            return lang.split("-")[0]

        return "en"

    def _extract_metadata(
        self, soup: BeautifulSoup, url: Optional[str]
    ) -> dict:
        """Extract metadata from HTML."""
        metadata = {}

        if url:
            metadata["url"] = url

        # Extract meta tags
        meta_tags = soup.find_all("meta")
        for tag in meta_tags:
            # og: tags
            if tag.get("property") and tag.get("property").startswith("og:"):
                key = tag["property"].replace("og:", "")
                metadata[key] = tag.get("content", "")

            # twitter: tags
            elif tag.get("name") and tag.get("name").startswith("twitter:"):
                key = tag["name"].replace("twitter:", "")
                metadata[key] = tag.get("content", "")

            # Standard meta tags
            elif tag.get("name") in {"description", "keywords", "author"}:
                metadata[tag["name"]] = tag.get("content", "")

        return metadata

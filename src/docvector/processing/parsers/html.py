"""HTML document parser."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Optional

from bs4 import BeautifulSoup

from docvector.core import get_logger
from docvector.utils import clean_text

from .base import BaseParser, ParsedDocument

logger = get_logger(__name__)

# Shared thread pool for CPU-intensive parsing operations
_thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="html-parser")


class HTMLParser(BaseParser):
    """Parse HTML documents."""

    MIME_TYPES = {"text/html", "application/xhtml+xml"}
    EXTENSIONS = {".html", ".htm", ".xhtml"}

    # Tags to remove (navigation, ads, etc.)
    REMOVE_TAGS = {
        "script", "style", "nav", "footer", "header", "aside",
        "noscript", "iframe", "form", "button", "input",
        "svg", "canvas", "video", "audio", "advertisement",
    }

    # Tags to keep for main content
    CONTENT_TAGS = {
        "article", "main", "section", "div", "p", "h1", "h2", "h3",
        "h4", "h5", "h6", "pre", "code", "blockquote", "ul", "ol",
        "li", "table", "tr", "td", "th", "dl", "dt", "dd",
    }

    def __init__(self):
        """Initialize HTML parser."""
        pass

    async def parse(self, content: bytes, url: Optional[str] = None) -> ParsedDocument:
        """Parse HTML content."""
        try:
            # Run parsing in thread pool to avoid blocking event loop
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                _thread_pool,
                partial(self._parse_sync, content, url),
            )
            return result

        except Exception as e:
            logger.error("Failed to parse HTML", error=str(e), url=url)
            raise

    def _parse_sync(self, content: bytes, url: Optional[str] = None) -> ParsedDocument:
        """Synchronous parsing implementation for thread pool execution."""
        # Parse HTML with BeautifulSoup (lxml is faster if available)
        try:
            soup = BeautifulSoup(content, "lxml")
        except Exception:
            # Fallback to html.parser if lxml not available
            soup = BeautifulSoup(content, "html.parser")

        # Extract metadata first (before removing elements)
        title = self._extract_title(soup)
        language = self._extract_language(soup)
        metadata = self._extract_metadata(soup, url)

        # Remove unwanted elements
        for tag in soup.find_all(self.REMOVE_TAGS):
            tag.decompose()

        # Try to find main content area
        main_content = self._find_main_content(soup)

        if main_content:
            text = self._extract_text_from_element(main_content)
        else:
            # Fallback: extract from body
            body = soup.find("body")
            if body:
                text = self._extract_text_from_element(body)
            else:
                text = soup.get_text(separator="\n", strip=True)

        return ParsedDocument(
            content=clean_text(text),
            title=title,
            language=language,
            metadata=metadata,
        )

    def _find_main_content(self, soup: BeautifulSoup):
        """Find the main content area of the page."""
        # Priority order for finding main content
        selectors = [
            ("article", {}),
            ("main", {}),
            ("div", {"role": "main"}),
            ("div", {"id": "content"}),
            ("div", {"id": "main-content"}),
            ("div", {"class": "content"}),
            ("div", {"class": "main-content"}),
            ("div", {"class": "article"}),
            ("div", {"class": "post"}),
            ("div", {"class": "documentation"}),
            ("div", {"class": "docs"}),
        ]

        for tag, attrs in selectors:
            element = soup.find(tag, attrs) if attrs else soup.find(tag)
            if element:
                # Verify it has substantial content
                text_length = len(element.get_text(strip=True))
                if text_length > 200:  # Minimum content threshold
                    return element

        return None

    def _extract_text_from_element(self, element) -> str:
        """Extract text from an element, preserving structure."""
        # Use get_text with newline separator - much faster than iterating descendants
        return element.get_text(separator="\n", strip=True)

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
            return str(soup.title.string).strip()

        # Try <h1> tag
        h1 = soup.find("h1")
        if h1:
            return str(h1.get_text(strip=True))

        # Try og:title meta tag
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            content = og_title["content"]
            return str(content).strip() if content else None

        return None

    def _extract_language(self, soup: BeautifulSoup) -> str:
        """Extract language from HTML."""
        # Try <html lang="...">
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            lang_attr = html_tag["lang"]
            if lang_attr:
                lang = str(lang_attr).strip().lower()
                # Take first part (e.g., "en-US" -> "en")
                return lang.split("-")[0]

        # Try meta tag
        lang_meta = soup.find("meta", attrs={"http-equiv": "Content-Language"})
        if lang_meta and lang_meta.get("content"):
            content = lang_meta["content"]
            if content:
                lang = str(content).strip().lower()
                return lang.split("-")[0]

        return "en"

    def _extract_metadata(self, soup: BeautifulSoup, url: Optional[str]) -> dict:
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

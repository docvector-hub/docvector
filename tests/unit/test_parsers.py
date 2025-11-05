"""Tests for document parsers."""

import pytest

from docvector.processing.parsers import HTMLParser, MarkdownParser


class TestHTMLParser:
    """Test HTML parser."""

    @pytest.fixture
    def parser(self):
        """Create HTML parser."""
        return HTMLParser()

    def test_can_parse_html_mime_type(self, parser):
        """Test HTML MIME type detection."""
        assert parser.can_parse("text/html")
        assert parser.can_parse("application/xhtml+xml")

    def test_can_parse_html_extension(self, parser):
        """Test HTML extension detection."""
        assert parser.can_parse("text/plain", ".html")
        assert parser.can_parse("text/plain", ".htm")

    def test_cannot_parse_other_types(self, parser):
        """Test rejection of other types."""
        assert not parser.can_parse("text/plain", ".txt")
        assert not parser.can_parse("application/pdf")

    @pytest.mark.asyncio
    async def test_parse_basic_html(self, parser, sample_html):
        """Test parsing basic HTML."""
        result = await parser.parse(sample_html)

        assert result.content is not None
        assert result.title == "Test Document"
        assert "Main Title" in result.content
        assert "Section 1" in result.content

    @pytest.mark.asyncio
    async def test_parse_html_extracts_title(self, parser):
        """Test title extraction from HTML."""
        html = b"<html><head><title>My Title</title></head><body>Content</body></html>"
        result = await parser.parse(html)

        assert result.title == "My Title"

    @pytest.mark.asyncio
    async def test_parse_html_no_title_uses_h1(self, parser):
        """Test fallback to h1 when no title."""
        html = b"<html><body><h1>Heading Title</h1><p>Content</p></body></html>"
        result = await parser.parse(html)

        assert result.title == "Heading Title"

    @pytest.mark.asyncio
    async def test_parse_html_removes_script_tags(self, parser):
        """Test removal of script tags."""
        html = b"<html><body><script>alert('hi')</script><p>Content</p></body></html>"
        result = await parser.parse(html)

        assert "alert" not in result.content
        assert "Content" in result.content

    @pytest.mark.asyncio
    async def test_parse_html_removes_style_tags(self, parser):
        """Test removal of style tags."""
        html = b"<html><body><style>body{color:red}</style><p>Content</p></body></html>"
        result = await parser.parse(html)

        assert "color:red" not in result.content
        assert "Content" in result.content

    @pytest.mark.asyncio
    async def test_parse_html_extracts_language(self, parser):
        """Test language extraction."""
        html = b'<html lang="fr"><body>Content</body></html>'
        result = await parser.parse(html)

        assert result.language == "fr"

    @pytest.mark.asyncio
    async def test_parse_html_default_language(self, parser):
        """Test default language when not specified."""
        html = b"<html><body>Content</body></html>"
        result = await parser.parse(html)

        assert result.language == "en"

    @pytest.mark.asyncio
    async def test_parse_html_extracts_metadata(self, parser):
        """Test metadata extraction."""
        html = b"""
        <html>
        <head>
            <meta name="description" content="Test description">
            <meta property="og:title" content="OG Title">
        </head>
        <body>Content</body>
        </html>
        """
        result = await parser.parse(html)

        assert "description" in result.metadata
        assert result.metadata["description"] == "Test description"
        assert "title" in result.metadata
        assert result.metadata["title"] == "OG Title"


class TestMarkdownParser:
    """Test Markdown parser."""

    @pytest.fixture
    def parser(self):
        """Create Markdown parser."""
        return MarkdownParser()

    def test_can_parse_markdown_mime_type(self, parser):
        """Test Markdown MIME type detection."""
        assert parser.can_parse("text/markdown")
        assert parser.can_parse("text/x-markdown")

    def test_can_parse_markdown_extension(self, parser):
        """Test Markdown extension detection."""
        assert parser.can_parse("text/plain", ".md")
        assert parser.can_parse("text/plain", ".markdown")
        assert parser.can_parse("text/plain", ".mkd")

    def test_cannot_parse_other_types(self, parser):
        """Test rejection of other types."""
        assert not parser.can_parse("text/plain", ".txt")
        assert not parser.can_parse("text/html")

    @pytest.mark.asyncio
    async def test_parse_basic_markdown(self, parser, sample_markdown):
        """Test parsing basic Markdown."""
        result = await parser.parse(sample_markdown)

        assert result.content is not None
        assert "Main Title" in result.content
        assert "Section 1" in result.content

    @pytest.mark.asyncio
    async def test_parse_markdown_extracts_title(self, parser):
        """Test title extraction from first heading."""
        markdown = b"# Document Title\n\nContent goes here."
        result = await parser.parse(markdown)

        assert result.title == "Document Title"

    @pytest.mark.asyncio
    async def test_parse_markdown_underline_heading(self, parser):
        """Test title extraction from underline-style heading."""
        markdown = b"Document Title\n==============\n\nContent goes here."
        result = await parser.parse(markdown)

        assert result.title == "Document Title"

    @pytest.mark.asyncio
    async def test_parse_markdown_no_title(self, parser):
        """Test parsing when no heading present."""
        markdown = b"Just plain text with no heading."
        result = await parser.parse(markdown)

        assert result.title is None
        assert "Just plain text" in result.content

    @pytest.mark.asyncio
    async def test_parse_markdown_default_language(self, parser):
        """Test default language."""
        markdown = b"# Title\n\nContent"
        result = await parser.parse(markdown)

        assert result.language == "en"

    @pytest.mark.asyncio
    async def test_parse_markdown_with_url(self, parser):
        """Test URL in metadata."""
        url = "https://example.com/doc.md"
        markdown = b"# Title\n\nContent"
        result = await parser.parse(markdown, url=url)

        assert result.metadata["url"] == url

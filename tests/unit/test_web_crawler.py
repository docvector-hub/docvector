"""Tests for web crawler."""

import pytest
from aioresponses import aioresponses

from docvector.ingestion import WebCrawler


class TestWebCrawler:
    """Test web crawler."""

    @pytest.fixture
    async def crawler(self):
        """Create web crawler."""
        crawler_instance = WebCrawler(
            max_depth=2,
            max_pages=10,
            concurrent_requests=2,
        )
        yield crawler_instance
        # Cleanup: close the session if it was created
        await crawler_instance.close()

    @pytest.mark.asyncio
    async def test_fetch_single_url(self, crawler):
        """Test fetching a single URL."""
        with aioresponses() as m:
            m.get(
                "https://example.com/test",
                status=200,
                body=b"<html><head><title>Test</title></head><body>Content</body></html>",
                headers={"Content-Type": "text/html"},
            )

            doc = await crawler.fetch_single("https://example.com/test")

            assert doc.url == "https://example.com/test"
            assert doc.content is not None
            assert doc.mime_type == "text/html"
            assert doc.title == "Test"

    @pytest.mark.asyncio
    async def test_fetch_single_handles_error(self, crawler):
        """Test handling fetch errors."""
        from aiohttp import ClientResponseError

        with aioresponses() as m:
            m.get("https://example.com/error", status=404)

            with pytest.raises(ClientResponseError):
                await crawler.fetch_single("https://example.com/error")

    @pytest.mark.asyncio
    async def test_should_crawl_http_urls(self, crawler):
        """Test that HTTP/HTTPS URLs are crawlable."""
        assert crawler._should_crawl("https://example.com/page", [])
        assert crawler._should_crawl("http://example.com/page", [])

    @pytest.mark.asyncio
    async def test_should_not_crawl_other_schemes(self, crawler):
        """Test that non-HTTP schemes are rejected."""
        assert not crawler._should_crawl("ftp://example.com/file", [])
        assert not crawler._should_crawl("mailto:test@example.com", [])
        assert not crawler._should_crawl("javascript:void(0)", [])

    @pytest.mark.asyncio
    async def test_should_crawl_respects_allowed_domains(self, crawler):
        """Test domain filtering."""
        allowed_domains = ["example.com"]

        assert crawler._should_crawl("https://example.com/page", allowed_domains)
        assert crawler._should_crawl("https://docs.example.com/page", allowed_domains)
        assert not crawler._should_crawl("https://other.com/page", allowed_domains)

    @pytest.mark.asyncio
    async def test_fetch_sitemap_parses_urls(self, crawler):
        """Test sitemap parsing."""
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://example.com/page1</loc></url>
            <url><loc>https://example.com/page2</loc></url>
            <url><loc>https://example.com/page3</loc></url>
        </urlset>
        """

        with aioresponses() as m:
            m.get(
                "https://example.com/sitemap.xml",
                status=200,
                body=sitemap_xml.encode(),
            )

            urls = await crawler._fetch_sitemap("https://example.com")

            assert len(urls) == 3
            assert "https://example.com/page1" in urls
            assert "https://example.com/page2" in urls

    @pytest.mark.asyncio
    async def test_fetch_sitemap_handles_missing(self, crawler):
        """Test handling missing sitemap."""
        with aioresponses() as m:
            m.get("https://example.com/sitemap.xml", status=404)

            urls = await crawler._fetch_sitemap("https://example.com")

            assert len(urls) == 0

    @pytest.mark.asyncio
    async def test_crawl_config_validation(self, crawler):
        """Test config validation."""
        from docvector.core import DocVectorException

        # Missing start_url
        config = {"max_pages": 10}

        with pytest.raises(DocVectorException) as exc_info:
            await crawler.fetch(config)

        assert "start_url" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_url_metadata(self, crawler):
        """Test that metadata is captured."""
        with aioresponses() as m:
            m.get(
                "https://example.com/test",
                status=200,
                body=b"<html><body>Test</body></html>",
                headers={
                    "Content-Type": "text/html; charset=utf-8",
                    "Server": "TestServer",
                },
            )

            doc = await crawler.fetch_single("https://example.com/test")

            assert doc.metadata["status_code"] == 200
            assert "headers" in doc.metadata
            assert doc.metadata["headers"]["Server"] == "TestServer"


class TestWebCrawlerInit:
    """Test web crawler initialization."""

    def test_crawler_default_settings(self):
        """Test crawler with default settings."""
        crawler = WebCrawler()

        assert crawler.max_depth > 0
        assert crawler.max_pages > 0
        assert crawler.concurrent_requests > 0

    def test_crawler_custom_settings(self):
        """Test crawler with custom settings."""
        crawler = WebCrawler(
            max_depth=5,
            max_pages=100,
            concurrent_requests=20,
            user_agent="CustomBot/1.0",
        )

        assert crawler.max_depth == 5
        assert crawler.max_pages == 100
        assert crawler.concurrent_requests == 20
        assert crawler.user_agent == "CustomBot/1.0"

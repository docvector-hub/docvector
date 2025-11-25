"""Crawl4AI-based web crawler for fast, AI-optimized document fetching."""

import asyncio
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

from docvector.core import DocVectorException, get_logger, settings

from .base import BaseFetcher, FetchedDocument

logger = get_logger(__name__)


class Crawl4AICrawler(BaseFetcher):
    """
    Crawl4AI-based web crawler for fast document fetching.

    Features:
    - AI-optimized content extraction
    - JavaScript rendering support
    - Clean markdown output
    - Concurrent crawling
    - Much faster than traditional crawlers
    """

    def __init__(
        self,
        max_pages: Optional[int] = None,
        concurrent_requests: Optional[int] = None,
        headless: bool = True,
    ):
        """
        Initialize Crawl4AI crawler.

        Args:
            max_pages: Maximum pages to fetch
            concurrent_requests: Number of concurrent requests
            headless: Run browser in headless mode
        """
        self.max_pages = max_pages or settings.crawler_max_pages
        self.concurrent_requests = concurrent_requests or settings.crawler_concurrent_requests
        self.headless = headless
        self._crawler: Optional[AsyncWebCrawler] = None

    async def _get_crawler(self) -> AsyncWebCrawler:
        """Get or create the crawler instance."""
        if self._crawler is None:
            browser_config = BrowserConfig(
                headless=self.headless,
                verbose=False,
            )
            self._crawler = AsyncWebCrawler(config=browser_config)
            await self._crawler.start()
        return self._crawler

    async def close(self) -> None:
        """Close crawler and cleanup resources."""
        if self._crawler:
            await self._crawler.close()
            self._crawler = None

    async def fetch(self, config: Dict) -> List[FetchedDocument]:
        """
        Fetch documents from a website using Crawl4AI.

        Config format:
        {
            "start_url": "https://docs.example.com",
            "max_pages": 100,
            "allowed_domains": ["docs.example.com"],
        }
        """
        start_url = config.get("start_url")
        if not start_url:
            raise DocVectorException(
                code="INVALID_CONFIG",
                message="start_url is required in config",
            )

        max_pages = config.get("max_pages", self.max_pages)
        allowed_domains = config.get("allowed_domains", [])

        logger.info(
            "Starting Crawl4AI crawl",
            start_url=start_url,
            max_pages=max_pages,
        )

        try:
            crawler = await self._get_crawler()

            # First, fetch the start page and extract links
            urls_to_fetch = await self._discover_urls(
                crawler, start_url, max_pages, allowed_domains
            )

            # Fetch all discovered URLs
            documents = await self._fetch_urls(crawler, urls_to_fetch)

            logger.info("Crawl4AI crawl completed", documents=len(documents))
            return documents

        except Exception as e:
            logger.error("Crawl4AI crawl failed", error=str(e))
            raise

    async def fetch_single(self, url: str, config: Optional[Dict] = None) -> FetchedDocument:
        """Fetch a single URL using Crawl4AI."""
        logger.info("Fetching single URL with Crawl4AI", url=url)

        try:
            crawler = await self._get_crawler()

            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                process_iframes=False,
                remove_overlay_elements=True,
                exclude_external_links=True,
            )

            result = await crawler.arun(url=url, config=run_config)

            if not result.success:
                raise DocVectorException(
                    code="FETCH_FAILED",
                    message=f"Failed to fetch {url}: {result.error_message}",
                )

            # Use markdown content (cleaner for AI processing)
            content = result.markdown.raw_markdown if result.markdown else ""

            return FetchedDocument(
                url=url,
                content=content.encode("utf-8"),
                mime_type="text/markdown",  # Crawl4AI returns markdown
                title=result.metadata.get("title") if result.metadata else None,
                metadata={
                    "status_code": result.status_code,
                    "crawl4ai": True,
                },
            )

        except Exception as e:
            logger.error("Failed to fetch URL with Crawl4AI", url=url, error=str(e))
            raise

    async def _discover_urls(
        self,
        crawler: AsyncWebCrawler,
        start_url: str,
        max_pages: int,
        allowed_domains: List[str],
    ) -> List[str]:
        """Discover URLs from the start page."""
        discovered: Set[str] = {start_url}

        try:
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
            )

            result = await crawler.arun(url=start_url, config=run_config)

            if result.success and result.links:
                # Extract internal links
                internal_links = result.links.get("internal", [])

                for link_info in internal_links:
                    link_url = link_info.get("href", "") if isinstance(link_info, dict) else str(link_info)

                    if self._should_crawl(link_url, allowed_domains):
                        discovered.add(link_url)

                    if len(discovered) >= max_pages:
                        break

            logger.info("Discovered URLs", count=len(discovered))

        except Exception as e:
            logger.warning("Failed to discover URLs", error=str(e))

        return list(discovered)[:max_pages]

    def _should_crawl(self, url: str, allowed_domains: List[str]) -> bool:
        """Check if URL should be crawled."""
        if not url:
            return False

        parsed = urlparse(url)

        # Skip non-http(s) URLs
        if parsed.scheme not in ("http", "https"):
            return False

        # Skip fragments and query strings for cleaner crawling
        if parsed.fragment:
            return False

        # Check allowed domains
        if allowed_domains:
            if not any(parsed.netloc.endswith(domain) for domain in allowed_domains):
                return False

        return True

    async def _fetch_urls(
        self, crawler: AsyncWebCrawler, urls: List[str]
    ) -> List[FetchedDocument]:
        """Fetch multiple URLs concurrently."""
        semaphore = asyncio.Semaphore(self.concurrent_requests)

        async def fetch_with_semaphore(url: str) -> Optional[FetchedDocument]:
            async with semaphore:
                try:
                    run_config = CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        process_iframes=False,
                        remove_overlay_elements=True,
                    )

                    result = await crawler.arun(url=url, config=run_config)

                    if not result.success:
                        logger.warning("Failed to fetch", url=url, error=result.error_message)
                        return None

                    content = result.markdown.raw_markdown if result.markdown else ""

                    return FetchedDocument(
                        url=url,
                        content=content.encode("utf-8"),
                        mime_type="text/markdown",
                        title=result.metadata.get("title") if result.metadata else None,
                        metadata={
                            "status_code": result.status_code,
                            "crawl4ai": True,
                        },
                    )

                except Exception as e:
                    logger.warning("Failed to fetch URL", url=url, error=str(e))
                    return None

        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks)

        # Filter out None results
        documents = [doc for doc in results if doc is not None]

        return documents

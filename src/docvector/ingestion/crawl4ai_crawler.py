"""Crawl4AI-based web crawler for fast, AI-optimized document fetching."""

import asyncio
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# Try to import URL seeding (available in newer versions)
try:
    from crawl4ai import AsyncUrlSeeder, SeedingConfig
    HAS_URL_SEEDER = True
except ImportError:
    HAS_URL_SEEDER = False

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
        max_depth: Optional[int] = None,
        concurrent_requests: Optional[int] = None,
        respect_robots: bool = True,
        headless: bool = True,
    ):
        """
        Initialize Crawl4AI crawler.

        Args:
            max_pages: Maximum pages to fetch
            max_depth: Maximum crawl depth from start URL
            concurrent_requests: Number of concurrent requests
            respect_robots: Whether to respect robots.txt
            headless: Run browser in headless mode
        """
        self.max_pages = max_pages or settings.crawler_max_pages
        self.max_depth = max_depth or settings.crawler_max_depth
        self.concurrent_requests = concurrent_requests or settings.crawler_concurrent_requests
        self.respect_robots = respect_robots
        self.headless = headless
        self._crawler: Optional[AsyncWebCrawler] = None
        self._robots_cache: Dict[str, RobotFileParser] = {}

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
        Fetch documents from a website using Crawl4AI with BFS crawling.

        Config format:
        {
            "start_url": "https://docs.example.com",
            "max_pages": 100,
            "max_depth": 3,
            "allowed_domains": ["docs.example.com"],
            "respect_robots": true,
        }
        """
        start_url = config.get("start_url")
        if not start_url:
            raise DocVectorException(
                code="INVALID_CONFIG",
                message="start_url is required in config",
            )

        max_pages = config.get("max_pages", self.max_pages)
        max_depth = config.get("max_depth", self.max_depth)
        allowed_domains = config.get("allowed_domains", [])
        respect_robots = config.get("respect_robots", self.respect_robots)

        # Auto-detect allowed domain from start URL if not specified
        if not allowed_domains:
            parsed = urlparse(start_url)
            allowed_domains = [parsed.netloc]

        logger.info(
            "Starting Crawl4AI crawl",
            start_url=start_url,
            max_pages=max_pages,
            max_depth=max_depth,
            respect_robots=respect_robots,
        )

        try:
            crawler = await self._get_crawler()

            # Load robots.txt if respecting it
            if respect_robots:
                await self._load_robots_txt(start_url)

            # Try sitemap-based discovery first (more efficient)
            urls_to_fetch = None
            use_sitemap = config.get("use_sitemap", True)

            if use_sitemap and HAS_URL_SEEDER:
                urls_to_fetch = await self._discover_from_sitemap(
                    start_url=start_url,
                    max_pages=max_pages,
                    url_pattern=config.get("url_pattern"),
                    respect_robots=respect_robots,
                )

            # If sitemap discovery found URLs, fetch them
            if urls_to_fetch:
                logger.info("Using sitemap-based crawling", urls=len(urls_to_fetch))
                documents = await self._fetch_urls_batch(
                    crawler=crawler,
                    urls=urls_to_fetch,
                    respect_robots=respect_robots,
                )
            else:
                # Fall back to BFS crawling
                logger.info("Using BFS-based crawling")
                documents = await self._crawl_bfs(
                    crawler=crawler,
                    start_url=start_url,
                    max_pages=max_pages,
                    max_depth=max_depth,
                    allowed_domains=allowed_domains,
                    respect_robots=respect_robots,
                )

            logger.info("Crawl4AI crawl completed", documents=len(documents))
            return documents

        except Exception as e:
            logger.error("Crawl4AI crawl failed", error=str(e))
            raise

    async def _load_robots_txt(self, url: str) -> None:
        """Load and cache robots.txt for the domain."""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        if base_url in self._robots_cache:
            return

        robots_url = f"{base_url}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)

        try:
            # Fetch robots.txt
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, rp.read)
            self._robots_cache[base_url] = rp
            logger.debug("Loaded robots.txt", url=robots_url)
        except Exception as e:
            logger.warning("Failed to load robots.txt", url=robots_url, error=str(e))
            # Create permissive parser on failure
            self._robots_cache[base_url] = rp

    def _can_fetch(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        if not self.respect_robots:
            return True

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        rp = self._robots_cache.get(base_url)
        if not rp:
            return True  # Allow if robots.txt not loaded

        return rp.can_fetch(settings.crawler_user_agent, url)

    async def _discover_from_sitemap(
        self,
        start_url: str,
        max_pages: int,
        url_pattern: Optional[str] = None,
        respect_robots: bool = True,
    ) -> Optional[List[str]]:
        """Discover URLs from sitemap.xml using Crawl4AI's AsyncUrlSeeder."""
        if not HAS_URL_SEEDER:
            return None

        parsed = urlparse(start_url)
        domain = parsed.netloc

        try:
            async with AsyncUrlSeeder() as seeder:
                seed_config = SeedingConfig(
                    source="sitemap",
                    pattern=url_pattern or "*",
                    max_urls=max_pages,
                    concurrency=self.concurrent_requests,
                )

                urls = await seeder.urls(domain, seed_config)

                if not urls:
                    logger.debug("No URLs found in sitemap", domain=domain)
                    return None

                # Filter by robots.txt if needed
                if respect_robots:
                    urls = [url for url in urls if self._can_fetch(url)]

                logger.info("Discovered URLs from sitemap", count=len(urls), domain=domain)
                return urls[:max_pages]

        except Exception as e:
            logger.warning("Sitemap discovery failed, will use BFS", error=str(e))
            return None

    async def _fetch_urls_batch(
        self,
        crawler: AsyncWebCrawler,
        urls: List[str],
        respect_robots: bool = True,
    ) -> List[FetchedDocument]:
        """Fetch multiple URLs concurrently in batches."""
        semaphore = asyncio.Semaphore(self.concurrent_requests)
        documents: List[FetchedDocument] = []

        async def fetch_one(url: str) -> Optional[FetchedDocument]:
            if respect_robots and not self._can_fetch(url):
                return None

            async with semaphore:
                try:
                    run_config = CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        process_iframes=False,
                        remove_overlay_elements=True,
                    )

                    result = await crawler.arun(url=url, config=run_config)

                    if not result.success:
                        logger.warning("Failed to fetch", url=url)
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

        # Fetch all URLs concurrently
        tasks = [fetch_one(url) for url in urls]
        results = await asyncio.gather(*tasks)

        # Filter out None results
        documents = [doc for doc in results if doc is not None]

        logger.info("Batch fetch completed", fetched=len(documents), total=len(urls))
        return documents

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

    async def _crawl_bfs(
        self,
        crawler: AsyncWebCrawler,
        start_url: str,
        max_pages: int,
        max_depth: int,
        allowed_domains: List[str],
        respect_robots: bool,
    ) -> List[FetchedDocument]:
        """
        Crawl website using BFS (breadth-first search).

        Returns documents as they are fetched.
        """
        visited: Set[str] = set()
        documents: List[FetchedDocument] = []

        # Queue: (url, depth)
        queue: List[tuple[str, int]] = [(self._normalize_url(start_url), 0)]

        semaphore = asyncio.Semaphore(self.concurrent_requests)

        while queue and len(documents) < max_pages:
            # Get batch of URLs at same depth level
            batch: List[tuple[str, int]] = []
            current_depth = queue[0][1] if queue else 0

            while queue and queue[0][1] == current_depth and len(batch) < self.concurrent_requests:
                url, depth = queue.pop(0)
                if url not in visited:
                    visited.add(url)
                    batch.append((url, depth))

            if not batch:
                continue

            logger.debug("Crawling batch", depth=current_depth, urls=len(batch))

            # Fetch batch concurrently
            async def fetch_and_extract(url: str, depth: int) -> Optional[tuple[FetchedDocument, List[str]]]:
                async with semaphore:
                    try:
                        run_config = CrawlerRunConfig(
                            cache_mode=CacheMode.BYPASS,
                            process_iframes=False,
                            remove_overlay_elements=True,
                        )

                        result = await crawler.arun(url=url, config=run_config)

                        if not result.success:
                            logger.warning("Failed to fetch", url=url)
                            return None

                        content = result.markdown.raw_markdown if result.markdown else ""

                        doc = FetchedDocument(
                            url=url,
                            content=content.encode("utf-8"),
                            mime_type="text/markdown",
                            title=result.metadata.get("title") if result.metadata else None,
                            metadata={
                                "status_code": result.status_code,
                                "crawl4ai": True,
                                "depth": depth,
                            },
                        )

                        # Extract links for next level
                        new_links = []
                        if depth < max_depth and result.links:
                            internal_links = result.links.get("internal", [])
                            for link_info in internal_links:
                                link_url = link_info.get("href", "") if isinstance(link_info, dict) else str(link_info)
                                normalized = self._normalize_url(link_url)
                                if normalized and self._should_crawl(normalized, allowed_domains, respect_robots):
                                    if normalized not in visited:
                                        new_links.append(normalized)

                        return (doc, new_links)

                    except Exception as e:
                        logger.warning("Failed to fetch URL", url=url, error=str(e))
                        return None

            # Fetch all URLs in batch
            tasks = [fetch_and_extract(url, depth) for url, depth in batch]
            results = await asyncio.gather(*tasks)

            # Process results
            for result in results:
                if result is None:
                    continue

                doc, new_links = result
                documents.append(doc)

                # Add new links to queue
                for link in new_links:
                    if link not in visited and len(visited) + len(queue) < max_pages * 2:
                        queue.append((link, doc.metadata.get("depth", 0) + 1))

                if len(documents) >= max_pages:
                    break

            logger.info("Crawl progress", fetched=len(documents), visited=len(visited), queue=len(queue))

        return documents

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes."""
        if not url:
            return ""

        parsed = urlparse(url)

        # Remove fragment
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # Remove trailing slash (except for root)
        if normalized.endswith("/") and parsed.path != "/":
            normalized = normalized[:-1]

        # Keep query string for pagination, etc.
        if parsed.query:
            normalized = f"{normalized}?{parsed.query}"

        return normalized

    def _should_crawl(self, url: str, allowed_domains: List[str], respect_robots: bool = True) -> bool:
        """Check if URL should be crawled."""
        if not url:
            return False

        parsed = urlparse(url)

        # Skip non-http(s) URLs
        if parsed.scheme not in ("http", "https"):
            return False

        # Skip common non-content extensions
        skip_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js", ".ico", ".woff", ".woff2", ".ttf", ".eot"}
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False

        # Check allowed domains
        if allowed_domains:
            if not any(parsed.netloc.endswith(domain) for domain in allowed_domains):
                return False

        # Check robots.txt
        if respect_robots and not self._can_fetch(url):
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

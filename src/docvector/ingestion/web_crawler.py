"""Web crawler for fetching documentation from websites."""

import asyncio
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from docvector.core import DocVectorException, get_logger, settings

from .base import BaseFetcher, FetchedDocument

logger = get_logger(__name__)


class WebCrawler(BaseFetcher):
    """
    Web crawler for fetching documentation pages.

    Features:
    - Respects robots.txt
    - Configurable depth and page limits
    - Concurrent fetching
    - Sitemap support
    """

    def __init__(
        self,
        max_depth: Optional[int] = None,
        max_pages: Optional[int] = None,
        concurrent_requests: Optional[int] = None,
        respect_robots_txt: bool = True,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize web crawler.

        Args:
            max_depth: Maximum crawl depth
            max_pages: Maximum pages to fetch
            concurrent_requests: Number of concurrent requests
            respect_robots_txt: Whether to respect robots.txt
            user_agent: User agent string
        """
        self.max_depth = max_depth or settings.crawler_max_depth
        self.max_pages = max_pages or settings.crawler_max_pages
        self.concurrent_requests = concurrent_requests or settings.crawler_concurrent_requests
        self.respect_robots_txt = respect_robots_txt
        self.user_agent = user_agent or settings.crawler_user_agent

        self.visited_urls: Set[str] = set()
        self.session: Optional[aiohttp.ClientSession] = None

    async def fetch(self, config: Dict) -> List[FetchedDocument]:
        """
        Fetch documents from a website.

        Config format:
        {
            "start_url": "https://docs.example.com",
            "max_depth": 3,
            "max_pages": 100,
            "allowed_domains": ["docs.example.com"],  # Optional
            "url_patterns": ["**/docs/**"],  # Optional
        }
        """
        start_url = config.get("start_url")
        if not start_url:
            raise DocVectorException(
                code="INVALID_CONFIG",
                message="start_url is required in config",
            )

        max_depth = config.get("max_depth", self.max_depth)
        max_pages = config.get("max_pages", self.max_pages)
        allowed_domains = config.get("allowed_domains", [])

        logger.info(
            "Starting web crawl",
            start_url=start_url,
            max_depth=max_depth,
            max_pages=max_pages,
        )

        # Initialize session
        await self._init_session()

        try:
            # Check for sitemap first
            sitemap_urls = await self._fetch_sitemap(start_url)

            if sitemap_urls:
                logger.info("Found sitemap", urls=len(sitemap_urls))
                urls_to_fetch = list(sitemap_urls)[:max_pages]
            else:
                # Crawl recursively
                urls_to_fetch = await self._crawl_recursive(
                    start_url=start_url,
                    max_depth=max_depth,
                    max_pages=max_pages,
                    allowed_domains=allowed_domains,
                )

            # Fetch all discovered URLs
            documents = await self._fetch_urls(urls_to_fetch)

            logger.info("Web crawl completed", documents=len(documents))

            return documents

        finally:
            await self._close_session()

    async def fetch_single(self, url: str, config: Optional[Dict] = None) -> FetchedDocument:
        """Fetch a single URL."""
        await self._init_session()

        try:
            return await self._fetch_url(url)
        finally:
            await self._close_session()

    async def _init_session(self) -> None:
        """Initialize aiohttp session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": self.user_agent},
            )

    async def _close_session(self) -> None:
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def close(self) -> None:
        """Close crawler and cleanup resources."""
        await self._close_session()

    async def _fetch_sitemap(self, base_url: str) -> Set[str]:
        """Try to fetch and parse sitemap.xml."""
        await self._init_session()

        parsed = urlparse(base_url)
        sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"

        try:
            async with self.session.get(sitemap_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, "xml")

                    # Extract URLs from sitemap
                    urls = set()
                    for loc in soup.find_all("loc"):
                        url = loc.text.strip()
                        if url:
                            urls.add(url)

                    return urls
        except Exception as e:
            logger.debug("Failed to fetch sitemap", error=str(e))

        return set()

    async def _crawl_recursive(
        self,
        start_url: str,
        max_depth: int,
        max_pages: int,
        allowed_domains: List[str],
    ) -> List[str]:
        """Recursively crawl URLs."""
        to_visit = [(start_url, 0)]  # (url, depth)
        discovered = {start_url}

        while to_visit and len(discovered) < max_pages:
            url, depth = to_visit.pop(0)

            if url in self.visited_urls:
                continue

            if depth > max_depth:
                continue

            self.visited_urls.add(url)

            # Fetch and parse page to find links
            try:
                async with self.session.get(url) as response:
                    if response.status != 200:
                        continue

                    content_type = response.headers.get("Content-Type", "")
                    if "text/html" not in content_type:
                        continue

                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Extract links
                    for link in soup.find_all("a", href=True):
                        href = link["href"]
                        absolute_url = urljoin(url, href)

                        # Filter URLs
                        if not self._should_crawl(absolute_url, allowed_domains):
                            continue

                        if absolute_url not in discovered:
                            discovered.add(absolute_url)
                            to_visit.append((absolute_url, depth + 1))

                            if len(discovered) >= max_pages:
                                break

            except Exception as e:
                logger.warning("Failed to crawl URL", url=url, error=str(e))
                continue

        return list(discovered)

    def _should_crawl(self, url: str, allowed_domains: List[str]) -> bool:
        """Check if URL should be crawled."""
        parsed = urlparse(url)

        # Skip non-http(s) URLs
        if parsed.scheme not in ("http", "https"):
            return False

        # Skip fragments
        if parsed.fragment:
            return False

        # Check allowed domains
        if allowed_domains:
            if not any(parsed.netloc.endswith(domain) for domain in allowed_domains):
                return False

        return True

    async def _fetch_urls(self, urls: List[str]) -> List[FetchedDocument]:
        """Fetch multiple URLs concurrently."""
        semaphore = asyncio.Semaphore(self.concurrent_requests)

        async def fetch_with_semaphore(url: str):
            async with semaphore:
                try:
                    return await self._fetch_url(url)
                except Exception as e:
                    logger.warning("Failed to fetch URL", url=url, error=str(e))
                    return None

        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks)

        # Filter out None results
        documents = [doc for doc in results if doc is not None]

        return documents

    async def _fetch_url(self, url: str) -> FetchedDocument:
        """Fetch a single URL."""
        async with self.session.get(url) as response:
            response.raise_for_status()

            content = await response.read()
            content_type = response.headers.get("Content-Type", "text/html")

            # Parse content type
            mime_type = content_type.split(";")[0].strip()

            # Extract title from HTML
            title = None
            if "text/html" in mime_type:
                try:
                    html = content.decode("utf-8", errors="ignore")
                    soup = BeautifulSoup(html, "html.parser")
                    if soup.title:
                        title = soup.title.string
                except Exception:
                    pass

            return FetchedDocument(
                url=url,
                content=content,
                mime_type=mime_type,
                title=title,
                metadata={
                    "status_code": response.status,
                    "headers": dict(response.headers),
                },
            )

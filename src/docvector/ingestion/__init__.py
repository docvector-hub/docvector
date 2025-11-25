"""Document ingestion components."""

from .base import BaseFetcher, FetchedDocument
from .web_crawler import WebCrawler
from .crawl4ai_crawler import Crawl4AICrawler

__all__ = ["BaseFetcher", "FetchedDocument", "WebCrawler", "Crawl4AICrawler"]

"""Document ingestion components."""

from .base import BaseFetcher, FetchedDocument
from .web_crawler import WebCrawler

__all__ = ["BaseFetcher", "FetchedDocument", "WebCrawler"]

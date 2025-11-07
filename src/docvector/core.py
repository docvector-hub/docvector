"""Core configuration, logging, and exceptions."""

import logging
import sys
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DocVectorException(Exception):
    """Base exception for DocVector."""
    pass


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="DOCVECTOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # Database
    database_url: str = Field(default="postgresql+asyncpg://localhost/docvector")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_max_connections: int = Field(default=10)

    # Qdrant
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_grpc_port: int = Field(default=6334)
    qdrant_use_grpc: bool = Field(default=False)
    qdrant_collection: str = Field(default="documents")

    # Embeddings
    embedding_provider: str = Field(default="local")  # "local" or "openai"
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_cache_enabled: bool = Field(default=True)
    openai_api_key: Optional[str] = Field(default=None)

    # Search
    search_min_score: float = Field(default=0.7)
    search_vector_weight: float = Field(default=0.7)
    search_keyword_weight: float = Field(default=0.3)

    # Crawler
    crawler_max_depth: int = Field(default=3)
    crawler_max_pages: int = Field(default=100)
    crawler_concurrent_requests: int = Field(default=5)
    crawler_user_agent: str = Field(
        default="DocVector/0.1.0 (https://github.com/docvector/docvector)"
    )


# Global settings instance
settings = Settings()


def setup_logging(level: Optional[str] = None) -> None:
    """
    Setup logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = level or settings.log_level

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)

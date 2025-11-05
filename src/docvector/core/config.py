"""
Configuration management for DocVector.

Loads settings from environment variables and config files.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "DocVector"
    app_version: str = "0.1.0"
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # API Server
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_workers: int = Field(default=4)
    api_reload: bool = Field(default=False)
    api_secret_key: str = Field(default="change-me-in-production-min-32-chars")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Database (PostgreSQL)
    database_url: str = Field(
        default="postgresql+asyncpg://docvector:docvector@localhost:5432/docvector"
    )
    db_pool_size: int = Field(default=20)
    db_max_overflow: int = Field(default=10)
    db_pool_timeout: int = Field(default=30)
    db_pool_recycle: int = Field(default=3600)
    db_echo: bool = Field(default=False)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_max_connections: int = Field(default=50)

    # Qdrant (Vector Database)
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_grpc_port: int = Field(default=6334)
    qdrant_collection: str = Field(default="documents")
    qdrant_use_grpc: bool = Field(default=False)

    # Embeddings
    embedding_provider: str = Field(default="local")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_dimension: int = Field(default=384)
    embedding_batch_size: int = Field(default=32)
    embedding_device: str = Field(default="cpu")
    embedding_cache_enabled: bool = Field(default=True)

    # OpenAI (optional)
    openai_api_key: Optional[str] = Field(default=None)

    # Cohere (optional)
    cohere_api_key: Optional[str] = Field(default=None)

    # Search
    search_default_limit: int = Field(default=10)
    search_max_limit: int = Field(default=100)
    search_hybrid_enabled: bool = Field(default=True)
    search_vector_weight: float = Field(default=0.7)
    search_keyword_weight: float = Field(default=0.3)
    search_min_score: float = Field(default=0.5)

    # Processing
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=50)
    chunking_strategy: str = Field(default="semantic")

    # Celery (Task Queue)
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/1")
    celery_task_always_eager: bool = Field(default=False)

    # Crawler
    crawler_max_depth: int = Field(default=3)
    crawler_max_pages: int = Field(default=1000)
    crawler_concurrent_requests: int = Field(default=10)
    crawler_respect_robots_txt: bool = Field(default=True)
    crawler_user_agent: str = Field(
        default="DocVector/1.0 (+https://github.com/docvector-hub/docvector)"
    )

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # Monitoring
    enable_metrics: bool = Field(default=True)
    metrics_port: int = Field(default=9090)

    # Sentry (optional)
    sentry_dsn: Optional[str] = Field(default=None)

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_search_per_minute: int = Field(default=100)
    rate_limit_ingestion_per_minute: int = Field(default=10)
    rate_limit_default_per_minute: int = Field(default=1000)

    # Storage
    storage_backend: str = Field(default="local")
    storage_local_path: str = Field(default="/app/uploads")

    # S3 (optional)
    s3_endpoint_url: Optional[str] = Field(default=None)
    s3_bucket: Optional[str] = Field(default=None)
    s3_access_key: Optional[str] = Field(default=None)
    s3_secret_key: Optional[str] = Field(default=None)
    s3_region: Optional[str] = Field(default="us-east-1")

    # Authentication
    auth_enabled: bool = Field(default=False)
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_minutes: int = Field(default=1440)

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()


# Convenience accessors
settings = get_settings()

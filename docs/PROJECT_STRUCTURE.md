# Project Structure

## Overview

DocVector follows a modular, layered architecture with clear separation of concerns.

## Directory Structure

```
docvector/
├── .github/
│   └── workflows/           # GitHub Actions CI/CD
│       ├── tests.yml
│       ├── build.yml
│       └── deploy.yml
│
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md
│   ├── API_DESIGN.md
│   ├── DATABASE_SCHEMA.md
│   ├── TECH_STACK.md
│   ├── DEPLOYMENT.md
│   └── CONTRIBUTING.md
│
├── src/
│   └── docvector/          # Main Python package
│       ├── __init__.py
│       │
│       ├── api/            # FastAPI application
│       │   ├── __init__.py
│       │   ├── main.py              # FastAPI app entry
│       │   ├── dependencies.py      # DI containers
│       │   ├── middleware.py        # Custom middleware
│       │   │
│       │   ├── routes/             # API route handlers
│       │   │   ├── __init__.py
│       │   │   ├── search.py       # Search endpoints
│       │   │   ├── sources.py      # Source management
│       │   │   ├── documents.py    # Document operations
│       │   │   ├── chunks.py       # Chunk operations
│       │   │   ├── jobs.py         # Job monitoring
│       │   │   ├── health.py       # Health checks
│       │   │   └── admin.py        # Admin endpoints
│       │   │
│       │   └── schemas/            # Pydantic models
│       │       ├── __init__.py
│       │       ├── search.py       # Search request/response
│       │       ├── source.py       # Source models
│       │       ├── document.py     # Document models
│       │       ├── chunk.py        # Chunk models
│       │       ├── job.py          # Job models
│       │       └── common.py       # Common schemas
│       │
│       ├── core/                   # Core business logic
│       │   ├── __init__.py
│       │   ├── config.py           # Configuration management
│       │   ├── security.py         # Auth & security
│       │   ├── exceptions.py       # Custom exceptions
│       │   └── logging.py          # Logging setup
│       │
│       ├── services/              # Service layer
│       │   ├── __init__.py
│       │   ├── search_service.py     # Search orchestration
│       │   ├── ingestion_service.py  # Ingestion orchestration
│       │   ├── embedding_service.py  # Embedding generation
│       │   ├── source_service.py     # Source management
│       │   └── job_service.py        # Job management
│       │
│       ├── ingestion/             # Document ingestion
│       │   ├── __init__.py
│       │   ├── base.py               # Base fetcher interface
│       │   ├── web_crawler.py        # Web crawling
│       │   ├── git_fetcher.py        # Git repo fetching
│       │   ├── file_uploader.py      # File uploads
│       │   ├── sitemap_parser.py     # Sitemap parsing
│       │   └── plugins/              # Source plugins
│       │       ├── __init__.py
│       │       ├── confluence.py
│       │       └── notion.py
│       │
│       ├── processing/            # Document processing
│       │   ├── __init__.py
│       │   ├── pipeline.py           # Processing pipeline
│       │   ├── parsers/              # Format parsers
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── markdown.py
│       │   │   ├── html.py
│       │   │   ├── pdf.py
│       │   │   └── docx.py
│       │   ├── chunkers/             # Chunking strategies
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── fixed_size.py
│       │   │   ├── semantic.py
│       │   │   └── hierarchical.py
│       │   └── cleaners/             # Text cleaning
│       │       ├── __init__.py
│       │       └── text_cleaner.py
│       │
│       ├── embeddings/            # Embedding generation
│       │   ├── __init__.py
│       │   ├── base.py               # Base embedder
│       │   ├── local_embedder.py     # Sentence transformers
│       │   ├── openai_embedder.py    # OpenAI API
│       │   ├── cache.py              # Embedding cache
│       │   └── batch_processor.py    # Batch processing
│       │
│       ├── vectordb/              # Vector database
│       │   ├── __init__.py
│       │   ├── base.py               # Base vector DB interface
│       │   ├── qdrant_client.py      # Qdrant implementation
│       │   └── pgvector_client.py    # pgvector (alternative)
│       │
│       ├── search/                # Search implementation
│       │   ├── __init__.py
│       │   ├── vector_search.py      # Vector similarity search
│       │   ├── keyword_search.py     # BM25/full-text search
│       │   ├── hybrid_search.py      # Hybrid search
│       │   ├── reranker.py           # Result reranking
│       │   └── filters.py            # Filter builders
│       │
│       ├── models/                # Database models (SQLAlchemy)
│       │   ├── __init__.py
│       │   ├── base.py               # Base model
│       │   ├── source.py             # Source model
│       │   ├── document.py           # Document model
│       │   ├── chunk.py              # Chunk model
│       │   ├── job.py                # Job model
│       │   └── cache.py              # Cache models
│       │
│       ├── db/                    # Database management
│       │   ├── __init__.py
│       │   ├── session.py            # Database sessions
│       │   ├── migrations/           # Alembic migrations
│       │   │   ├── env.py
│       │   │   ├── script.py.mako
│       │   │   └── versions/
│       │   └── repositories/         # Repository pattern
│       │       ├── __init__.py
│       │       ├── source_repo.py
│       │       ├── document_repo.py
│       │       └── chunk_repo.py
│       │
│       ├── tasks/                 # Celery tasks
│       │   ├── __init__.py
│       │   ├── celery_app.py         # Celery application
│       │   ├── ingestion_tasks.py    # Async ingestion
│       │   ├── embedding_tasks.py    # Async embedding
│       │   └── maintenance_tasks.py  # Cleanup, etc.
│       │
│       ├── cache/                 # Caching layer
│       │   ├── __init__.py
│       │   ├── redis_cache.py        # Redis implementation
│       │   └── decorators.py         # Cache decorators
│       │
│       └── utils/                 # Utilities
│           ├── __init__.py
│           ├── text_utils.py         # Text processing
│           ├── hash_utils.py         # Hashing
│           ├── validators.py         # Input validation
│           └── metrics.py            # Metrics/monitoring
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── unit/                   # Unit tests
│   │   ├── test_parsers.py
│   │   ├── test_chunkers.py
│   │   ├── test_embeddings.py
│   │   └── test_search.py
│   ├── integration/            # Integration tests
│   │   ├── test_api.py
│   │   ├── test_ingestion.py
│   │   └── test_pipeline.py
│   └── e2e/                    # End-to-end tests
│       └── test_workflows.py
│
├── scripts/                    # Utility scripts
│   ├── init_db.py              # Initialize database
│   ├── migrate.py              # Run migrations
│   ├── seed_data.py            # Seed test data
│   └── benchmark.py            # Performance benchmarks
│
├── deployment/                 # Deployment configs
│   ├── docker/
│   │   ├── Dockerfile          # Main Dockerfile
│   │   ├── Dockerfile.worker   # Worker Dockerfile
│   │   └── .dockerignore
│   ├── docker-compose.yml      # Local development
│   ├── docker-compose.prod.yml # Production setup
│   ├── k8s/                    # Kubernetes manifests
│   │   ├── api-deployment.yaml
│   │   ├── worker-deployment.yaml
│   │   ├── services.yaml
│   │   └── ingress.yaml
│   └── nginx/                  # Nginx configs
│       └── nginx.conf
│
├── config/                     # Configuration files
│   ├── config.yaml             # Default config
│   ├── config.dev.yaml         # Development config
│   └── config.prod.yaml        # Production config
│
├── .env.example                # Environment variables template
├── .gitignore
├── .pre-commit-config.yaml     # Pre-commit hooks
├── pyproject.toml              # Python project config
├── poetry.lock / requirements.txt
├── alembic.ini                 # Alembic config
├── pytest.ini                  # Pytest config
├── Makefile                    # Common commands
├── LICENSE
└── README.md
```

## Module Descriptions

### `/src/docvector/api/`

**FastAPI application and HTTP layer.**

- `main.py`: Application factory, CORS, middleware setup
- `routes/`: Endpoint handlers, request validation
- `schemas/`: Pydantic models for API contracts
- `dependencies.py`: Dependency injection (DB sessions, services)
- `middleware.py`: Request logging, auth, rate limiting

### `/src/docvector/core/`

**Core business logic and shared utilities.**

- `config.py`: Configuration loading from YAML/env
- `security.py`: JWT handling, API key validation
- `exceptions.py`: Custom exception hierarchy
- `logging.py`: Structured logging configuration

### `/src/docvector/services/`

**Service layer - orchestrates business logic.**

- `search_service.py`: Coordinates search operations
- `ingestion_service.py`: Manages ingestion workflows
- `embedding_service.py`: Generates and caches embeddings
- `source_service.py`: CRUD operations for sources
- `job_service.py`: Job lifecycle management

### `/src/docvector/ingestion/`

**Fetch documentation from various sources.**

- `base.py`: Abstract base class for fetchers
- `web_crawler.py`: HTTP crawling with sitemap support
- `git_fetcher.py`: Clone/pull Git repositories
- `plugins/`: Extensible source plugins

### `/src/docvector/processing/`

**Process and transform documents.**

- `pipeline.py`: Main processing pipeline
- `parsers/`: Extract text from various formats
- `chunkers/`: Split documents into chunks
- `cleaners/`: Clean and normalize text

### `/src/docvector/embeddings/`

**Generate vector embeddings.**

- `base.py`: Embedder interface
- `local_embedder.py`: Sentence transformers (default)
- `openai_embedder.py`: OpenAI API integration
- `cache.py`: Redis-backed embedding cache
- `batch_processor.py`: Efficient batch processing

### `/src/docvector/vectordb/`

**Vector database abstraction.**

- `base.py`: Vector DB interface
- `qdrant_client.py`: Qdrant implementation
- `pgvector_client.py`: Alternative PostgreSQL+pgvector

### `/src/docvector/search/`

**Search implementations.**

- `vector_search.py`: Semantic similarity search
- `keyword_search.py`: BM25 full-text search
- `hybrid_search.py`: Combine vector + keyword
- `reranker.py`: Cross-encoder reranking
- `filters.py`: Build search filters

### `/src/docvector/models/`

**SQLAlchemy ORM models.**

- Correspond to PostgreSQL tables
- Define relationships, indexes, constraints
- Include model methods and properties

### `/src/docvector/db/`

**Database management.**

- `session.py`: Async session factory
- `migrations/`: Alembic database migrations
- `repositories/`: Repository pattern for data access

### `/src/docvector/tasks/`

**Celery async tasks.**

- `celery_app.py`: Celery configuration
- `ingestion_tasks.py`: Background ingestion
- `embedding_tasks.py`: Async embedding generation
- `maintenance_tasks.py`: Periodic cleanup

### `/src/docvector/cache/`

**Caching layer.**

- `redis_cache.py`: Redis client wrapper
- `decorators.py`: `@cache` decorators for functions

### `/tests/`

**Comprehensive test suite.**

- `unit/`: Fast, isolated unit tests
- `integration/`: Test component interactions
- `e2e/`: Full workflow tests
- `conftest.py`: Shared fixtures and setup

## Key Files

### `pyproject.toml`

```toml
[tool.poetry]
name = "docvector"
version = "0.1.0"
description = "Self-hostable documentation vector search"
authors = ["DocVector Team"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
alembic = "^1.12.0"
asyncpg = "^0.29.0"
qdrant-client = "^1.7.0"
redis = "^5.0.0"
celery = "^5.3.0"
sentence-transformers = "^2.2.0"
torch = "^2.1.0"
pydantic = "^2.4.0"
pydantic-settings = "^2.0.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
aiohttp = "^3.9.0"
beautifulsoup4 = "^4.12.0"
trafilatura = "^1.6.0"
pypdf = "^3.17.0"
python-docx = "^1.1.0"
markdown-it-py = "^3.0.0"
structlog = "^23.2.0"
prometheus-client = "^0.19.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
httpx = "^0.25.0"
black = "^23.11.0"
ruff = "^0.1.5"
mypy = "^1.7.0"
pre-commit = "^3.5.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### `Makefile`

```makefile
.PHONY: help install dev test lint format docker-build docker-up

help:
	@echo "DocVector Development Commands"
	@echo "  make install      - Install dependencies"
	@echo "  make dev          - Run development server"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make docker-up    - Start Docker services"

install:
	poetry install

dev:
	poetry run uvicorn docvector.api.main:app --reload --host 0.0.0.0 --port 8000

test:
	poetry run pytest -v --cov=docvector

lint:
	poetry run ruff check src/
	poetry run mypy src/

format:
	poetry run black src/ tests/
	poetry run ruff check --fix src/

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	poetry run alembic upgrade head

migrate-create:
	poetry run alembic revision --autogenerate -m "$(message)"
```

## Configuration Files

### `config/config.yaml`

```yaml
# See ARCHITECTURE.md for full configuration reference
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
  reload: false

database:
  url: postgresql+asyncpg://user:pass@localhost:5432/docvector
  pool_size: 10
  echo: false

vector_db:
  type: qdrant
  host: localhost
  port: 6333
  collection: documents

redis:
  url: redis://localhost:6379/0

embeddings:
  provider: local
  model: sentence-transformers/all-MiniLM-L6-v2
  dimension: 384
  batch_size: 32

search:
  default_limit: 10
  max_limit: 100
  hybrid_enabled: true
  vector_weight: 0.7

processing:
  chunk_size: 512
  chunk_overlap: 50
  chunking_strategy: semantic
```

## Plugin System

### Creating a Custom Source Plugin

```python
# src/docvector/ingestion/plugins/custom_source.py

from docvector.ingestion.base import BaseFetcher
from docvector.models.document import Document

class CustomSourceFetcher(BaseFetcher):
    """Fetch documents from a custom source."""

    def __init__(self, config: dict):
        self.config = config

    async def fetch(self) -> list[Document]:
        """Fetch documents from the custom source."""
        # Implementation
        pass

    async def fetch_single(self, identifier: str) -> Document:
        """Fetch a single document."""
        pass

# Register plugin
from docvector.ingestion import register_plugin
register_plugin("custom_source", CustomSourceFetcher)
```

## Development Workflow

1. **Setup**: `make install`
2. **Run services**: `make docker-up`
3. **Run dev server**: `make dev`
4. **Run tests**: `make test`
5. **Format code**: `make format`
6. **Create migration**: `make migrate-create message="add new field"`
7. **Apply migrations**: `make migrate`

## Best Practices

1. **Layered Architecture**: API → Services → Repositories → Models
2. **Dependency Injection**: Use FastAPI's DI for services and DB sessions
3. **Async All the Way**: Use `async/await` for all I/O operations
4. **Type Hints**: Full type annotations for better IDE support
5. **Testing**: Aim for 80%+ code coverage
6. **Logging**: Use structured logging (JSON) for production
7. **Error Handling**: Catch exceptions at API layer, log at service layer
8. **Configuration**: Environment-specific configs, secrets in env vars

## Summary

This structure provides:
- **Clear Separation**: Each module has a specific responsibility
- **Scalability**: Easy to add new features and plugins
- **Testability**: Modular design enables comprehensive testing
- **Maintainability**: Well-organized code with consistent patterns
- **Extensibility**: Plugin architecture for customization

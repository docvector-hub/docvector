# Technology Stack - Detailed Justification

## Overview

This document provides detailed reasoning for technology choices in DocVector's architecture.

## Backend Framework: FastAPI

### Why FastAPI?

**Chosen**: FastAPI (Python 3.11+)

**Alternatives Considered**: Flask, Django, Express.js, NestJS

**Justification**:
1. **Performance**: Built on Starlette and Pydantic, offers excellent performance (comparable to Node.js)
2. **Async Native**: First-class async/await support, crucial for I/O-heavy operations
3. **Type Safety**: Pydantic models provide runtime validation and type hints
4. **Auto Documentation**: OpenAPI/Swagger docs generated automatically
5. **ML/AI Ecosystem**: Python's ML libraries (transformers, sentence-transformers) are industry-leading
6. **Developer Experience**: Modern Python with type hints, excellent IDE support
7. **Dependency Injection**: Built-in DI system for clean architecture

**Trade-offs**:
- Python's GIL can limit CPU-bound parallelism (mitigated by multiprocessing)
- Slightly higher memory footprint than Go/Rust
- But: For our use case (I/O bound, ML inference), Python is optimal

## Vector Database: Qdrant

### Why Qdrant?

**Chosen**: Qdrant

**Alternatives Considered**: Weaviate, Milvus, Pinecone, pgvector, ChromaDB

**Justification**:

| Feature | Qdrant | Weaviate | Milvus | pgvector | ChromaDB |
|---------|--------|----------|--------|----------|----------|
| Self-Hostable | ✓ | ✓ | ✓ | ✓ | ✓ |
| Open Source | ✓ | ✓ | ✓ | ✓ | ✓ |
| Performance | Excellent | Excellent | Excellent | Good | Good |
| Filtering | Rich | Rich | Limited | Limited | Basic |
| Docker-Friendly | ✓ | ✓ | Complex | ✓ | ✓ |
| Production-Ready | ✓ | ✓ | ✓ | ✓ | × (more for dev) |
| Horizontal Scaling | ✓ | ✓ | ✓ | × | × |
| Memory Efficiency | ✓ | ✓ | Moderate | ✓ | ✓ |

**Key Reasons for Qdrant**:
1. **Payload Filtering**: Rich filtering on metadata without secondary DB
2. **Performance**: HNSW algorithm with excellent recall/speed trade-off
3. **Simple Deployment**: Single Docker container, no complex setup
4. **Rust-Based**: Memory-safe, excellent performance
5. **Active Development**: Regular updates, responsive community
6. **API**: Clean REST and gRPC APIs, Python client
7. **Snapshots**: Built-in backup/restore capabilities

**When to Consider Alternatives**:
- **pgvector**: If you want everything in PostgreSQL (simpler stack but less performance)
- **Milvus**: If you need extreme scale (billions of vectors)
- **Weaviate**: If you need built-in GraphQL or specific ML model integrations

## Metadata Database: PostgreSQL

### Why PostgreSQL?

**Chosen**: PostgreSQL 15+

**Alternatives Considered**: MongoDB, MySQL, SQLite

**Justification**:
1. **Reliability**: Battle-tested, ACID compliant
2. **Rich Features**: JSONB, full-text search, arrays, CTEs
3. **pgvector Extension**: Can serve as vector DB if needed (hybrid approach)
4. **Performance**: Excellent query optimizer, indexing
5. **JSONB**: Store flexible metadata without schema rigidity
6. **Full-Text Search**: Built-in FTS for hybrid search
7. **Ecosystem**: Mature tools, ORMs (SQLAlchemy), monitoring
8. **Scalability**: Replication, partitioning, connection pooling

**Schema Strategy**:
- Use JSONB for flexible metadata
- Use traditional columns for queryable fields
- Indexes on frequently queried fields
- Partial indexes for specific use cases

## Task Queue: Celery + Redis

### Why Celery?

**Chosen**: Celery with Redis broker

**Alternatives Considered**: RQ, Dramatiq, BullMQ (Node.js), native asyncio

**Justification**:
1. **Mature**: Industry standard for Python async tasks
2. **Features**: Retry logic, scheduling, priorities, chains
3. **Monitoring**: Flower for web-based monitoring
4. **Distributed**: Horizontal scaling of workers
5. **Integration**: Works seamlessly with FastAPI
6. **Flexible Backends**: Redis (broker) + PostgreSQL (results)

**Why Redis as Broker**:
- Fast, in-memory message passing
- Also used for caching (dual purpose)
- Persistent queue with AOF/RDB
- Pub/Sub for real-time features

**Alternative Considered - RQ**:
- Simpler than Celery
- But lacks advanced features (canvas, chaining)
- Good for simpler use cases

## Caching: Redis

### Why Redis?

**Chosen**: Redis 7+

**Justification**:
1. **Speed**: In-memory, microsecond latency
2. **Data Structures**: Strings, hashes, lists, sets (flexible caching)
3. **TTL Support**: Automatic expiration
4. **Persistence**: RDB + AOF for durability
5. **Pub/Sub**: Real-time notifications
6. **Dual Role**: Cache + message broker

**Caching Strategy**:
```python
# Embedding cache
cache_key = f"emb:{hash(text)}"
ttl = 7 * 24 * 60 * 60  # 7 days

# Search result cache
cache_key = f"search:{hash(query)}:{filters}"
ttl = 60 * 60  # 1 hour

# Source metadata cache
cache_key = f"source:{source_id}"
ttl = 24 * 60 * 60  # 24 hours
```

## Embedding Models: Sentence Transformers

### Why Sentence Transformers?

**Chosen**: sentence-transformers (HuggingFace)

**Alternatives Considered**: OpenAI API, Cohere, local transformers, ONNX

**Default Model**: `all-MiniLM-L6-v2`

**Justification**:
1. **Self-Hosting**: Runs locally, no API costs
2. **Privacy**: Data never leaves your infrastructure
3. **Speed**: Optimized for sentence embeddings
4. **Quality**: State-of-the-art results
5. **Flexibility**: Easy to swap models
6. **Ecosystem**: HuggingFace hub for model discovery

**Model Comparison**:

| Model | Dimensions | Speed | Quality | Size |
|-------|------------|-------|---------|------|
| all-MiniLM-L6-v2 | 384 | Fast | Good | 80MB |
| all-mpnet-base-v2 | 768 | Medium | Better | 420MB |
| instructor-large | 768 | Slow | Best | 1.3GB |

**Recommended**:
- **Development/Small**: all-MiniLM-L6-v2
- **Production/Quality**: all-mpnet-base-v2
- **Enterprise/Best**: instructor-large or OpenAI ada-002

**Plugin Support**:
```python
# Easy to add OpenAI, Cohere, etc.
class OpenAIEmbedder:
    async def embed(self, texts: List[str]) -> List[Vector]:
        return await openai.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
```

## Web Scraping: Custom Solution

### Components

**Chosen**: aiohttp + BeautifulSoup4 + trafilatura

**Alternatives Considered**: Scrapy, Playwright, Selenium

**Justification**:
1. **aiohttp**: Async HTTP client, concurrent requests
2. **BeautifulSoup4**: HTML parsing, easy to use
3. **trafilatura**: Extract main content, remove boilerplate
4. **Lightweight**: No browser overhead (vs Playwright/Selenium)
5. **Fast**: Concurrent crawling with async

**When to Use Alternatives**:
- **Scrapy**: For large-scale, distributed crawling
- **Playwright**: For JS-heavy SPAs (future enhancement)

## Document Parsing

### Multi-Format Support

**Chosen Libraries**:

| Format | Library | Justification |
|--------|---------|---------------|
| Markdown | markdown-it-py | Fast, CommonMark compliant |
| HTML | BeautifulSoup4 | Industry standard |
| PDF | pypdf + pdfplumber | Pure Python, no system deps |
| DOCX | python-docx | Native .docx support |
| RST | docutils | Python ecosystem standard |
| EPUB | ebooklib | E-book support |

**Parsing Strategy**:
1. Detect format by extension and magic bytes
2. Extract text content
3. Preserve structure (headings, links)
4. Extract metadata
5. Convert to common Document model

## ORM: SQLAlchemy 2.0

### Why SQLAlchemy?

**Chosen**: SQLAlchemy 2.0 with async support

**Alternatives Considered**: raw SQL, Tortoise ORM, SQLModel, Django ORM

**Justification**:
1. **Async Support**: SQLAlchemy 2.0 with asyncio
2. **Flexibility**: Core (SQL builder) + ORM
3. **Type Safety**: Works with Pydantic via SQLModel
4. **Migrations**: Alembic integration
5. **Performance**: Query optimization, lazy loading
6. **Maturity**: Industry standard, huge ecosystem

**Example**:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_document(session: AsyncSession, doc_id: str):
    result = await session.execute(
        select(Document).where(Document.id == doc_id)
    )
    return result.scalar_one_or_none()
```

## Development Tools

### Code Quality
- **Linting**: ruff (fast Python linter)
- **Formatting**: black + isort
- **Type Checking**: mypy
- **Testing**: pytest + pytest-asyncio + pytest-cov
- **Pre-commit**: pre-commit hooks for quality gates

### Documentation
- **API Docs**: Auto-generated by FastAPI (OpenAPI)
- **Code Docs**: Sphinx + autodoc
- **Markdown**: MkDocs for user documentation

### CI/CD
- **GitHub Actions**: Automated testing, building, deployment
- **Docker**: Multi-stage builds for small images
- **Versioning**: Semantic versioning

## Deployment Stack

### Containerization: Docker

**Justification**:
1. **Consistency**: Same environment dev to prod
2. **Isolation**: Dependencies contained
3. **Portability**: Run anywhere
4. **Efficiency**: Layered caching

**Multi-stage Build**:
```dockerfile
# Builder stage
FROM python:3.11-slim as builder
# Install dependencies

# Runtime stage
FROM python:3.11-slim
# Copy only what's needed
```

### Orchestration: Docker Compose (Primary)

**For Self-Hosting**: Docker Compose

**Justification**:
1. **Simplicity**: Single YAML file
2. **Local Development**: Easy to run locally
3. **Service Discovery**: Automatic networking
4. **Volume Management**: Persistent data
5. **No Kubernetes Overhead**: Right-sized for most users

**Production Option**: Kubernetes

**When to Use K8s**:
- High availability requirements
- Auto-scaling needs
- Multi-region deployment
- Large-scale enterprise use

## Monitoring (Optional for Self-Host)

### Metrics: Prometheus + Grafana

**Justification**:
- **Prometheus**: Time-series metrics, PromQL
- **Grafana**: Beautiful dashboards, alerting
- **Integration**: Prometheus client for Python

### Logging: structlog

**Justification**:
- Structured logging (JSON)
- Context propagation
- Performance
- ELK stack integration (optional)

### Tracing: OpenTelemetry (Future)

**For Distributed Tracing**:
- Request tracing across services
- Performance bottleneck identification
- Production debugging

## Summary: Technology Decision Matrix

| Component | Technology | Maturity | Performance | Ease of Use | Self-Host |
|-----------|------------|----------|-------------|-------------|-----------|
| API Framework | FastAPI | ✓ | ✓ | ✓ | ✓ |
| Vector DB | Qdrant | ✓ | ✓ | ✓ | ✓ |
| RDBMS | PostgreSQL | ✓ | ✓ | ✓ | ✓ |
| Cache/Queue | Redis | ✓ | ✓ | ✓ | ✓ |
| Task Queue | Celery | ✓ | ✓ | ~ | ✓ |
| Embeddings | sentence-transformers | ✓ | ✓ | ✓ | ✓ |
| ORM | SQLAlchemy | ✓ | ✓ | ~ | N/A |
| Container | Docker | ✓ | ✓ | ✓ | ✓ |

**Legend**: ✓ Excellent, ~ Good, × Poor

## Conclusion

This technology stack is optimized for:
1. **Self-hosting**: All components run locally
2. **Performance**: Async I/O, efficient algorithms
3. **Maintainability**: Mature, well-documented tools
4. **Extensibility**: Plugin architecture, modular design
5. **Developer Experience**: Modern tools, type safety, good docs

The stack balances simplicity with power, making it accessible for small teams while providing a path to scale for larger deployments.

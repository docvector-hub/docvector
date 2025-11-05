# DocVector Open Source Architecture

## Overview

DocVector is a self-hostable documentation indexing and vector search system designed to help AI agents efficiently search through public and private documentation. This document outlines the architecture for the open-source component.

## System Goals

1. **Self-Hostable**: Easy to deploy and run on-premises or private cloud
2. **Scalable**: Handle thousands of documentation pages efficiently
3. **Extensible**: Plugin architecture for custom sources and formats
4. **Agent-Friendly**: Optimized APIs for AI agent consumption
5. **Hybrid Search**: Combine vector similarity with traditional keyword search
6. **Multi-Source**: Support various documentation formats and sources

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  (AI Agents, Web UI, CLI, API Clients)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      API Gateway                                 │
│  (FastAPI - REST API, WebSocket)                                │
└─────┬──────────────────┬────────────────────┬────────────────┘
      │                  │                    │
┌─────▼──────┐  ┌────────▼─────────┐  ┌──────▼──────────────┐
│  Search    │  │   Ingestion      │  │  Management         │
│  Service   │  │   Service        │  │  Service            │
└─────┬──────┘  └────────┬─────────┘  └──────┬──────────────┘
      │                  │                    │
      │         ┌────────▼─────────┐          │
      │         │  Processing      │          │
      │         │  Pipeline        │          │
      │         └────────┬─────────┘          │
      │                  │                    │
      │         ┌────────▼─────────┐          │
      │         │  Embedding       │          │
      │         │  Service         │          │
      │         └────────┬─────────┘          │
      │                  │                    │
┌─────▼──────────────────▼────────────────────▼──────────────────┐
│                     Storage Layer                               │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐   │
│  │ Vector DB    │  │ PostgreSQL    │  │ Object Storage   │   │
│  │ (Qdrant)     │  │ (Metadata)    │  │ (Documents)      │   │
│  └──────────────┘  └───────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
      │
┌─────▼─────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                          │
│  (Redis Cache, Message Queue, Monitoring)                     │
└───────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Gateway (FastAPI)

**Responsibilities:**
- Handle all external API requests
- Authentication and authorization
- Rate limiting
- Request validation and response formatting
- WebSocket connections for real-time updates

**Endpoints:**
- `/api/v1/search` - Vector and hybrid search
- `/api/v1/ingest` - Trigger documentation ingestion
- `/api/v1/documents` - Document CRUD operations
- `/api/v1/sources` - Manage documentation sources
- `/api/v1/health` - Health checks and status

### 2. Ingestion Service

**Responsibilities:**
- Crawl and fetch documentation from various sources
- Handle different authentication methods
- Schedule periodic updates
- Detect changes and incremental updates

**Supported Sources:**
- Web crawling (HTTP/HTTPS)
- Git repositories (GitHub, GitLab, Bitbucket)
- File uploads (ZIP, individual files)
- API integrations (Confluence, Notion, etc.)

**Components:**
- `WebCrawler`: Crawl documentation websites
- `GitFetcher`: Clone and pull from Git repositories
- `FileUploader`: Handle direct file uploads
- `SourceManager`: Manage source configurations

### 3. Processing Pipeline

**Responsibilities:**
- Parse various document formats
- Chunk documents intelligently
- Extract metadata and structure
- Clean and normalize text

**Pipeline Stages:**
1. **Format Detection**: Identify document type
2. **Parsing**: Extract content from format (HTML, MD, PDF, etc.)
3. **Cleaning**: Remove noise, normalize whitespace
4. **Chunking**: Split into semantically meaningful chunks
5. **Metadata Extraction**: Extract titles, headers, URLs, timestamps
6. **Enrichment**: Add contextual information

**Chunking Strategies:**
- Fixed-size with overlap (configurable)
- Semantic chunking (based on document structure)
- Hierarchical chunking (preserve document hierarchy)
- Custom chunkers via plugins

### 4. Embedding Service

**Responsibilities:**
- Generate vector embeddings for text chunks
- Support multiple embedding models
- Batch processing for efficiency
- Caching for duplicate content

**Supported Models:**
- **Local Models** (default for self-hosting):
  - `sentence-transformers/all-MiniLM-L6-v2` (lightweight, fast)
  - `sentence-transformers/all-mpnet-base-v2` (better quality)
  - Custom ONNX models
- **API-based Models** (optional):
  - OpenAI embeddings (ada-002, text-embedding-3)
  - Cohere embeddings
  - Voyage AI

**Features:**
- Model hot-swapping
- Dimension reduction
- Embedding caching with Redis
- Batch processing optimization

### 5. Vector Database (Qdrant)

**Why Qdrant:**
- Open source and self-hostable
- High performance with HNSW indexing
- Rich filtering capabilities
- Payload storage alongside vectors
- Docker-friendly
- Horizontal scaling support

**Schema Design:**
```json
{
  "collection": "documents",
  "vectors": {
    "size": 384,  // or 768, 1536 depending on model
    "distance": "Cosine"
  },
  "payload": {
    "doc_id": "string",
    "chunk_id": "string",
    "content": "string",
    "title": "string",
    "url": "string",
    "source": "string",
    "metadata": "object",
    "timestamp": "integer"
  }
}
```

### 6. PostgreSQL (Metadata & Configuration)

**Responsibilities:**
- Store document metadata
- Source configurations
- User settings
- Job history and logs
- Relationships between documents

**Key Tables:**
- `sources`: Documentation source configurations
- `documents`: Document metadata and status
- `chunks`: Chunk metadata and references
- `jobs`: Ingestion and processing job history
- `embeddings_cache`: Cache embeddings by content hash

### 7. Search Service

**Responsibilities:**
- Execute vector similarity searches
- Hybrid search (vector + keyword)
- Result ranking and reranking
- Context retrieval for RAG

**Search Types:**
1. **Vector Search**: Pure semantic similarity
2. **Keyword Search**: BM25 or PostgreSQL full-text
3. **Hybrid Search**: Combine both with configurable weights
4. **Filtered Search**: Filter by source, date, tags

**Advanced Features:**
- Query expansion
- Reranking with cross-encoders
- Context window extraction
- Relevance scoring

### 8. Management Service

**Responsibilities:**
- Configure and manage sources
- Monitor ingestion jobs
- System health and metrics
- Configuration management

## Data Flow

### Ingestion Flow

```
1. User configures source (URL, Git repo, upload)
   ↓
2. Ingestion Service fetches content
   ↓
3. Processing Pipeline parses and chunks
   ↓
4. Embedding Service generates vectors
   ↓
5. Store vectors in Qdrant + metadata in PostgreSQL
   ↓
6. Index ready for search
```

### Search Flow

```
1. Client sends search query
   ↓
2. Query embedding generated
   ↓
3. Vector search in Qdrant (+ optional keyword search)
   ↓
4. Results ranked and filtered
   ↓
5. Context retrieved and formatted
   ↓
6. Return results to client
```

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Async**: asyncio, aiohttp
- **Task Queue**: Celery + Redis
- **Testing**: pytest, pytest-asyncio

### Storage
- **Vector DB**: Qdrant (latest stable)
- **RDBMS**: PostgreSQL 15+ with pgvector extension
- **Cache**: Redis 7+
- **Object Storage**: Local filesystem / MinIO (S3-compatible)

### ML/NLP
- **Embeddings**: sentence-transformers, transformers
- **Model Runtime**: PyTorch (CPU/GPU), ONNX Runtime
- **Text Processing**: beautifulsoup4, markdownify, pypdf

### Web Crawling
- **HTTP Client**: aiohttp, httpx
- **Parsing**: beautifulsoup4, trafilatura
- **Sitemap**: advertools or custom

### DevOps
- **Containerization**: Docker, Docker Compose
- **Orchestration**: Kubernetes (optional)
- **Monitoring**: Prometheus, Grafana (optional)
- **Logging**: structlog, ELK stack (optional)

## Plugin Architecture

DocVector supports plugins for extensibility:

### Plugin Types
1. **Source Plugins**: Custom documentation sources
2. **Parser Plugins**: Custom document format parsers
3. **Chunker Plugins**: Custom chunking strategies
4. **Embedding Plugins**: Custom embedding models
5. **Reranker Plugins**: Custom reranking algorithms

### Plugin Interface
```python
class SourcePlugin:
    def fetch(self, config: dict) -> List[Document]: pass

class ParserPlugin:
    def parse(self, content: bytes, mime_type: str) -> Document: pass

class ChunkerPlugin:
    def chunk(self, document: Document) -> List[Chunk]: pass
```

## Configuration Management

### Configuration File (`config.yaml`)
```yaml
# Server settings
server:
  host: 0.0.0.0
  port: 8000
  workers: 4

# Vector database
vector_db:
  type: qdrant
  host: localhost
  port: 6333
  collection: documents

# Metadata database
metadata_db:
  type: postgresql
  host: localhost
  port: 5432
  database: docvector
  user: docvector
  password: ${DB_PASSWORD}

# Embedding configuration
embeddings:
  provider: local  # or 'openai', 'cohere'
  model: sentence-transformers/all-MiniLM-L6-v2
  dimension: 384
  batch_size: 32
  cache_enabled: true

# Search configuration
search:
  default_limit: 10
  max_limit: 100
  hybrid_enabled: true
  vector_weight: 0.7
  keyword_weight: 0.3

# Processing
processing:
  chunk_size: 512
  chunk_overlap: 50
  chunking_strategy: semantic  # or 'fixed', 'hierarchical'

# Crawler settings
crawler:
  max_depth: 3
  max_pages: 1000
  respect_robots_txt: true
  user_agent: DocVector/1.0
  concurrent_requests: 10
```

## Security Considerations

1. **Authentication**: JWT-based authentication
2. **API Keys**: For programmatic access
3. **Rate Limiting**: Prevent abuse
4. **Input Validation**: Strict validation on all inputs
5. **Secrets Management**: Environment variables, no hardcoded secrets
6. **Network Security**: TLS/SSL for production
7. **Access Control**: Role-based access control (RBAC)

## Deployment Architecture

### Docker Compose (Recommended for Self-Hosting)
```yaml
services:
  api:
    image: docvector/api:latest

  worker:
    image: docvector/worker:latest

  qdrant:
    image: qdrant/qdrant:latest

  postgres:
    image: postgres:15

  redis:
    image: redis:7
```

### Kubernetes (For Scale)
- Horizontal pod autoscaling
- Persistent volume claims for storage
- Service mesh (optional)

## Performance Optimization

1. **Embedding Caching**: Redis cache for embeddings
2. **Batch Processing**: Process documents in batches
3. **Async I/O**: All I/O operations are async
4. **Connection Pooling**: Database connection pools
5. **Query Optimization**: Indexed queries, query planning
6. **CDN**: Static assets via CDN (future)
7. **Result Caching**: Cache frequent queries

## Monitoring and Observability

### Metrics to Track
- Ingestion rate (docs/min)
- Search latency (p50, p95, p99)
- Embedding generation time
- Vector DB query time
- Cache hit rates
- Error rates by endpoint
- Queue lengths

### Health Checks
- `/health/live` - Liveness probe
- `/health/ready` - Readiness probe
- `/health/deps` - Dependency health

## Future Enhancements (Post-MVP)

1. **Issue Tracking Integration**: Index GitHub/GitLab issues
2. **Solution Tracking**: Track and rank solutions
3. **Feedback Loop**: Learn from user feedback
4. **Multi-Language Support**: Internationalization
5. **Collaborative Filtering**: Recommend related docs
6. **Graph Relationships**: Document relationship graphs
7. **Real-time Updates**: Live documentation updates via WebSocket
8. **Advanced Reranking**: Cross-encoder reranking
9. **Query Understanding**: Intent classification and query expansion

## Success Metrics

1. **Search Accuracy**: Relevance of top-k results
2. **Search Speed**: Sub-200ms response time (p95)
3. **Indexing Speed**: 100+ pages per minute
4. **Resource Efficiency**: Run on modest hardware (4GB RAM minimum)
5. **Uptime**: 99.9% availability

## Conclusion

This architecture provides a solid foundation for a self-hostable documentation vector search system. It balances simplicity with extensibility, making it suitable for both individual developers and small teams while providing a path to scale.

The modular design allows components to be swapped or upgraded as needed, and the plugin architecture ensures extensibility for future requirements.

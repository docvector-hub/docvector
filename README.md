# DocVector - Open Source Documentation Search & Indexing

**Self-hostable documentation vector search system designed for AI agents.**

DocVector enables AI agents to efficiently search through public and private documentation using state-of-the-art vector embeddings and hybrid search. Built for self-hosting with enterprise-grade features.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

## Features

- **Vector Search**: Semantic search using state-of-the-art embedding models
- **Hybrid Search**: Combine vector similarity with keyword search (BM25)
- **Multi-Source**: Index docs from websites, Git repos, files, APIs
- **Self-Hostable**: Deploy on-premises or in your private cloud
- **Agent-Optimized**: API designed for AI agent consumption
- **Extensible**: Plugin architecture for custom sources and parsers
- **Production-Ready**: Built with FastAPI, PostgreSQL, Qdrant, Redis
- **Open Source**: MIT licensed, community-driven

## Quick Start

### Prerequisites

- Docker 24.0+
- Docker Compose 2.20+
- 4GB RAM minimum (8GB recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/docvector.git
cd docvector

# Copy environment configuration
cp .env.example .env

# Edit .env and set secure passwords
nano .env

# Start all services
docker-compose up -d

# Check health
curl http://localhost:8000/api/v1/health
```

That's it! DocVector is now running at http://localhost:8000

### Your First Search

```bash
# Add a documentation source
curl -X POST http://localhost:8000/api/v1/sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Supabase Docs",
    "type": "web",
    "config": {
      "url": "https://supabase.com/docs",
      "max_depth": 3
    }
  }'

# Wait for indexing to complete (monitor in logs)
docker-compose logs -f worker

# Search the documentation
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how to authenticate users",
    "limit": 5
  }'
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  (AI Agents, Web UI, CLI, API Clients)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      API Gateway (FastAPI)                       │
└─────┬──────────────────┬────────────────────┬────────────────┘
      │                  │                    │
┌─────▼──────┐  ┌────────▼─────────┐  ┌──────▼──────────────┐
│  Search    │  │   Ingestion      │  │  Management         │
│  Service   │  │   Service        │  │  Service            │
└─────┬──────┘  └────────┬─────────┘  └─────────────────────┘
      │                  │
      │         ┌────────▼─────────┐
      │         │  Processing      │
      │         │  Pipeline        │
      │         └────────┬─────────┘
      │                  │
      │         ┌────────▼─────────┐
      │         │  Embedding       │
      │         │  Service         │
      │         └────────┬─────────┘
      │                  │
┌─────▼──────────────────▼────────────────────────────────────────┐
│                     Storage Layer                                │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐    │
│  │ Qdrant       │  │ PostgreSQL    │  │ Redis            │    │
│  │ (Vectors)    │  │ (Metadata)    │  │ (Cache/Queue)    │    │
│  └──────────────┘  └───────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Documentation

- **[Architecture](ARCHITECTURE.md)** - System design and components
- **[Technology Stack](docs/TECH_STACK.md)** - Detailed technology choices and rationale
- **[Database Schema](docs/DATABASE_SCHEMA.md)** - PostgreSQL and Qdrant schemas
- **[API Design](docs/API_DESIGN.md)** - Complete API reference
- **[Project Structure](docs/PROJECT_STRUCTURE.md)** - Code organization
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment strategies

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **API Framework** | FastAPI | High-performance async API |
| **Vector DB** | Qdrant | Fast similarity search |
| **Database** | PostgreSQL | Metadata and configuration |
| **Cache/Queue** | Redis | Caching and async tasks |
| **Task Queue** | Celery | Background job processing |
| **Embeddings** | Sentence Transformers | Local embedding generation |
| **Web Scraping** | aiohttp + BeautifulSoup | Documentation crawling |
| **Container** | Docker | Easy deployment |

## Use Cases

### For AI Agents

```python
# Agent searching documentation
response = await docvector_client.search(
    query="implement OAuth authentication",
    filters={"source": "supabase"},
    limit=3
)

for result in response.results:
    print(f"Title: {result.title}")
    print(f"Content: {result.content}")
    print(f"URL: {result.url}")
```

### For Development Teams

- **Centralized Docs**: Index all your stack's documentation in one place
- **Private Docs**: Index internal wikis, Confluence, Notion
- **Version Control**: Track documentation changes over time
- **Search Analytics**: Understand what your team searches for

### For Documentation Sites

- **Enhanced Search**: Better than basic keyword search
- **Semantic Understanding**: Find content even with different terminology
- **Multi-Language**: Support for international documentation

## Supported Documentation Sources

- **Web Crawling**: Any public documentation website
- **Git Repositories**: GitHub, GitLab, Bitbucket
- **File Uploads**: PDF, DOCX, Markdown, HTML
- **APIs**: Confluence, Notion (via plugins)
- **Custom**: Extensible plugin system

## API Examples

### Search Documentation

```bash
POST /api/v1/search
{
  "query": "database connection pooling",
  "search_type": "hybrid",
  "filters": {
    "source_ids": ["uuid"],
    "languages": ["en"]
  },
  "limit": 10
}
```

### Add Documentation Source

```bash
POST /api/v1/sources
{
  "name": "Next.js Docs",
  "type": "web",
  "config": {
    "url": "https://nextjs.org/docs",
    "max_depth": 3
  },
  "sync_frequency": "daily"
}
```

### Monitor Indexing

```bash
GET /api/v1/jobs/{job_id}
{
  "status": "running",
  "progress": {
    "processed_documents": 150,
    "total_documents": 500,
    "percentage": 30
  }
}
```

## Development

### Local Setup

```bash
# Install dependencies
poetry install

# Start infrastructure (Postgres, Qdrant, Redis)
docker-compose up -d postgres qdrant redis

# Run migrations
poetry run alembic upgrade head

# Start development server
poetry run uvicorn docvector.api.main:app --reload

# Run tests
poetry run pytest

# Format code
poetry run black src/ tests/
poetry run ruff check --fix src/
```

### Project Structure

```
docvector/
├── src/docvector/       # Main package
│   ├── api/             # FastAPI routes
│   ├── services/        # Business logic
│   ├── ingestion/       # Document fetching
│   ├── processing/      # Document processing
│   ├── embeddings/      # Embedding generation
│   ├── search/          # Search implementation
│   └── models/          # Database models
├── tests/               # Test suite
├── docs/                # Documentation
└── deployment/          # Docker, K8s configs
```

## Deployment

### Docker Compose (Recommended)

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# With monitoring
docker-compose --profile monitoring up -d
```

### Kubernetes

```bash
# Deploy to Kubernetes
kubectl apply -f deployment/k8s/
```

See [Deployment Guide](docs/DEPLOYMENT.md) for detailed instructions.

## Configuration

Key configuration options in `.env`:

```bash
# Embedding model (affects search quality vs. speed)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Search configuration
SEARCH_HYBRID_ENABLED=true
SEARCH_VECTOR_WEIGHT=0.7

# Processing
CHUNK_SIZE=512
CHUNKING_STRATEGY=semantic

# Performance
API_WORKERS=4
CELERY_WORKERS=4
```

## Performance

- **Search Latency**: < 100ms (p95) for vector search
- **Indexing Speed**: 100+ documents/minute
- **Concurrent Users**: 100+ with default configuration
- **Scale**: Millions of chunks with proper hardware

## Monitoring

Access monitoring tools:

- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **Flower (Celery)**: http://localhost:5555
- **Grafana**: http://localhost:3000 (with monitoring profile)

## Roadmap

- [x] Vector and hybrid search
- [x] Web crawling
- [x] Multiple embedding models
- [x] Docker deployment
- [ ] Issue tracking integration (GitHub, GitLab)
- [ ] Solution tracking and ranking
- [ ] Real-time updates via WebSocket
- [ ] Advanced reranking (cross-encoders)
- [ ] Multi-language support
- [ ] Query analytics dashboard
- [ ] Client SDKs (Python, JavaScript, Go)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/docvector/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/docvector/discussions)

## Acknowledgments

Built with amazing open-source projects:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Qdrant](https://qdrant.tech/)
- [Sentence Transformers](https://www.sbert.net/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)

---

**Made with ❤️ for the AI agent community**
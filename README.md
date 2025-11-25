# DocVector

A self-hostable documentation vector search system that enables semantic search across your documentation using embeddings and hybrid search capabilities.

## Features

- **Hybrid Search**: Combines vector similarity and keyword matching for accurate results
- **Multiple Embedding Providers**: Support for local sentence-transformers and OpenAI embeddings
- **Web Crawling**: Automatically crawl and index documentation websites
- **Flexible Chunking**: Fixed-size and semantic chunking strategies
- **Caching**: Redis-based caching for improved performance
- **RESTful API**: FastAPI-based REST API with OpenAPI documentation
- **Vector Database**: Qdrant for efficient vector storage and retrieval
- **Content Parsing**: Support for HTML and Markdown content

## Prerequisites

- Python 3.9 or higher
- Redis (for caching)
- Qdrant (for vector storage)
- PostgreSQL (optional, SQLite used by default)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd docvector
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install the package with dependencies
pip install -e .

# For development (includes testing and linting tools)
pip install -e ".[dev]"
```

### 3. Set Up External Services

#### Redis (Required)

**Using Docker:**
```bash
docker run -d --name docvector-redis -p 6379:6379 redis:latest
```

**Using Homebrew (macOS):**
```bash
brew install redis
brew services start redis
```

#### Qdrant (Required)

**Using Docker:**
```bash
docker run -d --name docvector-qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

**Using Docker Compose (Recommended):**

Create a `docker-compose.yml` file:
```yaml
version: '3.8'

services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage

volumes:
  redis_data:
  qdrant_storage:
```

Then run:
```bash
docker-compose up -d
```

### 4. Configure Environment

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` with your configuration. The default values work for local development with Docker services.

### 5. Initialize Database

```bash
python init_db.py
```

### 6. Start the Application

Using the startup script:
```bash
chmod +x start.sh
./start.sh
```

Or manually:
```bash
python -m docvector.api.main
```

The API will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/health`

## Configuration

All configuration is done via environment variables with the `DOCVECTOR_` prefix. See `.env` for all available options.

### Key Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `DOCVECTOR_DATABASE_URL` | Database connection URL | `sqlite+aiosqlite:///./docvector.db` |
| `DOCVECTOR_REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `DOCVECTOR_QDRANT_HOST` | Qdrant host | `localhost` |
| `DOCVECTOR_QDRANT_PORT` | Qdrant HTTP port | `6333` |
| `DOCVECTOR_EMBEDDING_PROVIDER` | Embedding provider (`local` or `openai`) | `local` |
| `DOCVECTOR_EMBEDDING_MODEL` | Embedding model name | `sentence-transformers/all-MiniLM-L6-v2` |
| `DOCVECTOR_API_PORT` | API server port | `8000` |
| `DOCVECTOR_LOG_LEVEL` | Logging level | `INFO` |

### Using OpenAI Embeddings

To use OpenAI embeddings instead of local models:

```bash
DOCVECTOR_EMBEDDING_PROVIDER=openai
DOCVECTOR_EMBEDDING_MODEL=text-embedding-3-small
DOCVECTOR_OPENAI_API_KEY=your-api-key-here
```

### Using PostgreSQL

For production deployments, PostgreSQL is recommended:

```bash
DOCVECTOR_DATABASE_URL=postgresql+asyncpg://user:password@localhost/docvector
```

## Usage

### Ingesting Documentation

Use the API to crawl and index documentation:

```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.example.com",
    "source_name": "Example Docs",
    "max_depth": 3,
    "max_pages": 100
  }'
```

### Searching Documentation

```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to configure authentication?",
    "limit": 10,
    "min_score": 0.7
  }'
```

### Managing Sources

```bash
# List all sources
curl "http://localhost:8000/api/v1/sources"

# Get specific source
curl "http://localhost:8000/api/v1/sources/{source_id}"

# Delete source
curl -X DELETE "http://localhost:8000/api/v1/sources/{source_id}"
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=docvector --cov-report=html

# Run specific test file
pytest tests/test_search.py

# Run in parallel
pytest -n auto
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Architecture

```
src/docvector/
├── api/              # FastAPI application and routes
├── cache/            # Redis caching layer
├── db/               # Database models and repositories
├── embeddings/       # Embedding providers
├── ingestion/        # Web crawling and ingestion
├── processing/       # Content parsing and chunking
├── search/           # Search implementations
├── services/         # Business logic services
├── utils/            # Utility functions
└── vectordb/         # Vector database clients
```

## API Endpoints

### Health & Info

- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - OpenAPI documentation
- `GET /redoc` - ReDoc documentation

### Search

- `POST /api/v1/search` - Search documentation

### Sources

- `GET /api/v1/sources` - List all sources
- `POST /api/v1/sources` - Create source
- `GET /api/v1/sources/{source_id}` - Get source details
- `DELETE /api/v1/sources/{source_id}` - Delete source

### Ingestion

- `POST /api/v1/ingest` - Ingest documentation from URL

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:

```bash
# Reinitialize the database
rm docvector.db
python init_db.py
```

### Redis Connection Issues

Verify Redis is running:

```bash
redis-cli ping
# Should return: PONG
```

### Qdrant Connection Issues

Check Qdrant health:

```bash
curl http://localhost:6333/health
```

### Embedding Model Download

On first run, the sentence-transformers model will be downloaded. This may take a few minutes depending on your internet connection.

## Contributing

Contributions are welcome! Please see the [testing guide](TESTING_GUIDE.md) for information on running tests.

## License

[Add your license here]

## Support

For issues and questions, please create an issue in the repository.

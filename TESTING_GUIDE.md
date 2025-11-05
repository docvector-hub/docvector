# DocVector Testing Guide

This guide explains how to test the web crawling and public/private indexing features.

## Prerequisites

Before testing, ensure you have:

1. **Dependencies installed:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Services running:**
   - PostgreSQL (port 5432)
   - Redis (port 6379)
   - Qdrant (port 6333)

3. **Quick start with Docker Compose:**
   ```bash
   docker-compose up -d postgres redis qdrant
   ```

4. **Database migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Environment variables** (create `.env` file):
   ```env
   DATABASE_URL=postgresql+asyncpg://docvector:docvector@localhost:5432/docvector
   REDIS_URL=redis://localhost:6379/0
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   EMBEDDING_PROVIDER=local
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```

## Running the API Server

Start the FastAPI server:

```bash
# Development mode with auto-reload
python -m uvicorn docvector.api.main:app --reload --host 0.0.0.0 --port 8000

# Or using the Makefile
make dev
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive docs**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

## Testing Web Crawling

### 1. Create a Documentation Source

First, create a source for the documentation you want to crawl:

```bash
curl -X POST http://localhost:8000/api/v1/sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python Docs",
    "type": "web",
    "config": {
      "start_url": "https://docs.python.org/3/tutorial/",
      "max_depth": 2,
      "max_pages": 20,
      "allowed_domains": ["docs.python.org"]
    },
    "sync_frequency": "daily"
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Python Docs",
  "type": "web",
  "status": "active",
  ...
}
```

Save the `id` for the next steps.

### 2. Ingest Entire Source (Background Crawl)

Trigger a full crawl of the source:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/source \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "550e8400-e29b-41d4-a716-446655440000",
    "access_level": "public"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Ingestion started for source: Python Docs"
}
```

The crawling happens in the background. Monitor the logs to see progress.

### 3. Ingest Single URL

To index a specific URL (useful for testing or adding individual pages):

**Public URL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/ingest/url \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "550e8400-e29b-41d4-a716-446655440000",
    "url": "https://docs.python.org/3/tutorial/introduction.html",
    "access_level": "public"
  }'
```

**Private URL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/ingest/url \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "550e8400-e29b-41d4-a716-446655440000",
    "url": "https://internal.company.com/private-docs/api.html",
    "access_level": "private"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "URL ingested successfully: https://docs.python.org/3/tutorial/introduction.html",
  "document_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

## Testing Public/Private Access Control

### Understanding Access Levels

- **Public**: Accessible to anyone (e.g., public documentation)
- **Private**: Restricted access (e.g., internal documentation)

When searching, you can filter by access level to control what results users see.

### Search Examples

**1. Search All Documents (No Filter)**

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how to use Python lists",
    "limit": 5,
    "search_type": "hybrid"
  }'
```

Returns both public and private documents.

**2. Search Only Public Documents**

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how to use Python lists",
    "limit": 5,
    "search_type": "hybrid",
    "access_level": "public"
  }'
```

Returns only documents indexed as "public".

**3. Search Only Private Documents**

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "internal API documentation",
    "limit": 5,
    "search_type": "hybrid",
    "access_level": "private"
  }'
```

Returns only documents indexed as "private".

### Use Cases

**For Public-Facing Applications:**
```json
{
  "query": "user search query",
  "access_level": "public"
}
```

**For Internal Tools (Authenticated Users):**
```json
{
  "query": "user search query",
  "access_level": "private"
}
```

**For Admin/Full Access:**
```json
{
  "query": "user search query"
  // No access_level filter - returns all
}
```

## Integration with Authentication

In a production system, you would integrate the `access_level` filter with your authentication system:

```python
# Pseudo-code example
def search_handler(query: str, user: User):
    if user.is_authenticated:
        # Authenticated users can see private docs
        access_level = None  # or "private"
    else:
        # Anonymous users only see public docs
        access_level = "public"

    return search_service.search(
        query=query,
        filters={"access_level": access_level} if access_level else None
    )
```

## Testing with Python Requests

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Create source
source_response = requests.post(
    f"{BASE_URL}/sources",
    json={
        "name": "Test Docs",
        "type": "web",
        "config": {
            "start_url": "https://example.com/docs",
            "max_depth": 2,
            "max_pages": 10
        }
    }
)
source_id = source_response.json()["id"]

# 2. Ingest a public URL
requests.post(
    f"{BASE_URL}/ingest/url",
    json={
        "source_id": source_id,
        "url": "https://example.com/docs/public-api.html",
        "access_level": "public"
    }
)

# 3. Ingest a private URL
requests.post(
    f"{BASE_URL}/ingest/url",
    json={
        "source_id": source_id,
        "url": "https://example.com/docs/internal-api.html",
        "access_level": "private"
    }
)

# 4. Search public only
public_results = requests.post(
    f"{BASE_URL}/search",
    json={
        "query": "API documentation",
        "access_level": "public",
        "limit": 10
    }
)

print(f"Public results: {len(public_results.json()['results'])}")

# 5. Search private only
private_results = requests.post(
    f"{BASE_URL}/search",
    json={
        "query": "API documentation",
        "access_level": "private",
        "limit": 10
    }
)

print(f"Private results: {len(private_results.json()['results'])}")
```

## Testing with the Interactive Docs

1. Navigate to http://localhost:8000/docs
2. Try out the endpoints interactively:
   - `POST /api/v1/sources` - Create a source
   - `POST /api/v1/ingest/url` - Index a URL
   - `POST /api/v1/search` - Search with access level filters

## Monitoring Ingestion

Check logs for ingestion progress:

```bash
# Watch logs in real-time
tail -f logs/docvector.log

# Or if running in Docker
docker-compose logs -f api
```

You should see logs like:
```
INFO: Starting web crawl start_url=https://docs.python.org/3/tutorial/
INFO: Found sitemap urls=50
INFO: Web crawl completed documents=20
INFO: Document processed document_id=xxx chunks=15
```

## Troubleshooting

### Issue: Crawling is slow

**Solutions:**
- Reduce `max_pages` in source config
- Increase `concurrent_requests` setting
- Check network latency to target site

### Issue: No results when searching

**Checks:**
1. Verify ingestion completed successfully
2. Check access_level filter matches indexed documents
3. Verify Qdrant is running: `curl http://localhost:6333/collections`
4. Check embedding model is loaded: see logs for "Model loaded successfully"

### Issue: Out of memory during embedding

**Solutions:**
- Use smaller embedding model
- Reduce batch size: `EMBEDDING_BATCH_SIZE=16`
- Use OpenAI embeddings instead: `EMBEDDING_PROVIDER=openai`

## Advanced Testing

### Test with Custom Sitemap

```json
{
  "name": "Custom Site",
  "type": "web",
  "config": {
    "start_url": "https://mysite.com",
    "max_depth": 3,
    "max_pages": 100,
    "allowed_domains": ["mysite.com", "docs.mysite.com"]
  }
}
```

### Test Mixed Access Levels

Index the same source with different access levels:

```bash
# Public version
curl -X POST http://localhost:8000/api/v1/ingest/url \
  -d '{"source_id": "...", "url": "https://docs.com/api", "access_level": "public"}'

# Private version (with auth examples)
curl -X POST http://localhost:8000/api/v1/ingest/url \
  -d '{"source_id": "...", "url": "https://docs.com/internal-api", "access_level": "private"}'
```

### Performance Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test search endpoint
ab -n 100 -c 10 -p search_payload.json -T application/json \
  http://localhost:8000/api/v1/search
```

## Next Steps

- **Add Authentication**: Integrate JWT or API keys
- **Rate Limiting**: Add rate limits per access level
- **Monitoring**: Set up Prometheus metrics
- **Testing**: Add automated integration tests
- **Caching**: Enable Redis caching for frequent queries

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review `ARCHITECTURE.md` for system design
- See `docs/` for detailed documentation

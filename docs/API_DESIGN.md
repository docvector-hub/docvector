# API Design Specification

## Overview

DocVector exposes a RESTful API built with FastAPI. All endpoints return JSON and follow standard HTTP conventions.

**Base URL**: `http://localhost:8000/api/v1`

**Authentication**: JWT Bearer tokens (for multi-user setups) or API keys

## API Principles

1. **RESTful**: Standard HTTP methods (GET, POST, PUT, DELETE)
2. **Consistent**: Uniform response format
3. **Versioned**: `/api/v1` prefix for stability
4. **Documented**: OpenAPI/Swagger auto-generated docs
5. **Paginated**: Large result sets use cursor/offset pagination
6. **Filtered**: Consistent filter query params
7. **Async**: All operations are async for performance

## Authentication

### API Key (Recommended for Self-Hosting)

```http
GET /api/v1/search?q=authentication
Authorization: Bearer YOUR_API_KEY
```

### JWT Token (For Multi-User)

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}

Response:
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Response Format

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "request_id": "uuid",
    "timestamp": "2024-01-01T12:00:00Z",
    "duration_ms": 45
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid query parameter",
    "details": {
      "field": "limit",
      "reason": "Must be between 1 and 100"
    }
  },
  "metadata": {
    "request_id": "uuid",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## API Endpoints

## 1. Search API

### Search Documents

**Primary endpoint for AI agents to search documentation.**

```http
POST /api/v1/search
Content-Type: application/json
```

**Request Body**:
```json
{
  "query": "how to authenticate users",
  "search_type": "hybrid",  // "vector", "keyword", "hybrid"
  "limit": 10,
  "offset": 0,

  // Filters
  "filters": {
    "source_ids": ["uuid1", "uuid2"],
    "languages": ["en"],
    "date_from": "2024-01-01T00:00:00Z",
    "date_to": "2024-12-31T23:59:59Z",
    "tags": ["authentication", "security"]
  },

  // Search configuration
  "config": {
    "vector_weight": 0.7,      // For hybrid search
    "keyword_weight": 0.3,
    "min_score": 0.5,          // Minimum relevance score
    "rerank": true,            // Apply reranking
    "include_content": true,   // Include full chunk content
    "context_window": 1        // Include N chunks before/after
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "chunk_id": "uuid",
        "document_id": "uuid",
        "score": 0.92,

        // Content
        "content": "To authenticate users in Supabase...",
        "title": "Authentication Guide",
        "url": "https://supabase.com/docs/guides/auth",

        // Context
        "heading_hierarchy": ["Authentication Guide", "Getting Started"],
        "section": "Getting Started",

        // Metadata
        "source": {
          "id": "uuid",
          "name": "Supabase Docs",
          "type": "web"
        },
        "metadata": {
          "tags": ["auth", "security"],
          "language": "en",
          "published_at": "2024-01-01T00:00:00Z"
        },

        // Context chunks (if requested)
        "context": {
          "before": ["Previous chunk content..."],
          "after": ["Next chunk content..."]
        }
      }
    ],

    "pagination": {
      "total": 150,
      "limit": 10,
      "offset": 0,
      "has_more": true
    },

    "search_metadata": {
      "query_vector_generated": true,
      "search_type": "hybrid",
      "duration_ms": 45,
      "sources_searched": 2
    }
  }
}
```

### Simple Search (GET)

**For quick searches without complex filters.**

```http
GET /api/v1/search?q=authentication&limit=5&source=supabase
```

**Query Parameters**:
- `q` (required): Search query
- `limit` (optional): Results limit (default: 10, max: 100)
- `offset` (optional): Pagination offset (default: 0)
- `source` (optional): Source name filter
- `lang` (optional): Language filter (e.g., "en")
- `type` (optional): Search type ("vector", "keyword", "hybrid")

### Get Similar Chunks

**Find chunks similar to a given chunk.**

```http
GET /api/v1/search/similar/{chunk_id}?limit=5
```

**Response**: Same format as search

## 2. Sources API

### List Sources

```http
GET /api/v1/sources?status=active&type=web&limit=20&offset=0
```

**Response**:
```json
{
  "success": true,
  "data": {
    "sources": [
      {
        "id": "uuid",
        "name": "Supabase Documentation",
        "type": "web",
        "status": "active",
        "config": {
          "url": "https://supabase.com/docs",
          "max_depth": 3
        },
        "stats": {
          "total_documents": 245,
          "total_chunks": 1823,
          "last_synced_at": "2024-01-01T12:00:00Z"
        },
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "total": 5,
      "limit": 20,
      "offset": 0
    }
  }
}
```

### Get Source Details

```http
GET /api/v1/sources/{source_id}
```

**Response**: Single source object with detailed stats

### Create Source

```http
POST /api/v1/sources
Content-Type: application/json
```

**Request Body**:
```json
{
  "name": "Next.js Documentation",
  "type": "web",
  "config": {
    "url": "https://nextjs.org/docs",
    "sitemap_url": "https://nextjs.org/sitemap.xml",
    "max_depth": 3,
    "max_pages": 1000,
    "exclude_patterns": ["/blog/*"],
    "selectors": {
      "content": "article.docs",
      "title": "h1"
    }
  },
  "sync_frequency": "daily"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "source": { ... },
    "ingestion_job": {
      "id": "uuid",
      "status": "pending",
      "message": "Ingestion job queued"
    }
  }
}
```

### Update Source

```http
PUT /api/v1/sources/{source_id}
```

**Request Body**: Same as create (partial updates allowed)

### Delete Source

```http
DELETE /api/v1/sources/{source_id}?delete_documents=true
```

**Query Parameters**:
- `delete_documents` (optional): Also delete all documents (default: false)

### Trigger Source Sync

```http
POST /api/v1/sources/{source_id}/sync
```

**Request Body** (optional):
```json
{
  "full_sync": true,  // Force full re-sync (default: incremental)
  "priority": "high"  // Job priority: "low", "normal", "high"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "status": "queued",
    "estimated_duration": "5 minutes"
  }
}
```

## 3. Documents API

### List Documents

```http
GET /api/v1/documents?source_id=uuid&status=completed&limit=20&offset=0
```

**Query Parameters**:
- `source_id` (optional): Filter by source
- `status` (optional): Filter by status
- `search` (optional): Full-text search in title/content
- `limit`, `offset`: Pagination

**Response**:
```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "id": "uuid",
        "source_id": "uuid",
        "title": "Authentication Guide",
        "url": "https://supabase.com/docs/guides/auth",
        "status": "completed",
        "chunk_count": 12,
        "content_length": 5420,
        "metadata": { ... },
        "processed_at": "2024-01-01T12:00:00Z"
      }
    ],
    "pagination": { ... }
  }
}
```

### Get Document Details

```http
GET /api/v1/documents/{document_id}?include_chunks=true
```

**Query Parameters**:
- `include_chunks` (optional): Include chunk list (default: false)

**Response**: Single document with optional chunks array

### Delete Document

```http
DELETE /api/v1/documents/{document_id}
```

Deletes document and all associated chunks and embeddings.

### Reprocess Document

```http
POST /api/v1/documents/{document_id}/reprocess
```

Re-chunk and re-embed a document (useful after config changes).

## 4. Chunks API

### List Chunks

```http
GET /api/v1/chunks?document_id=uuid&limit=50
```

**Response**:
```json
{
  "success": true,
  "data": {
    "chunks": [
      {
        "id": "uuid",
        "document_id": "uuid",
        "chunk_index": 0,
        "content": "Authentication in Supabase...",
        "content_length": 512,
        "has_embedding": true,
        "metadata": { ... }
      }
    ]
  }
}
```

### Get Chunk Details

```http
GET /api/v1/chunks/{chunk_id}?include_context=true
```

**Query Parameters**:
- `include_context` (optional): Include previous/next chunks

## 5. Ingestion Jobs API

### List Jobs

```http
GET /api/v1/jobs?source_id=uuid&status=running&limit=20
```

**Response**:
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": "uuid",
        "source_id": "uuid",
        "job_type": "full_sync",
        "status": "running",
        "progress": {
          "total_documents": 100,
          "processed_documents": 45,
          "failed_documents": 2,
          "percentage": 45
        },
        "started_at": "2024-01-01T12:00:00Z",
        "estimated_completion": "2024-01-01T12:10:00Z"
      }
    ]
  }
}
```

### Get Job Details

```http
GET /api/v1/jobs/{job_id}
```

**Response**: Detailed job info with logs

### Cancel Job

```http
POST /api/v1/jobs/{job_id}/cancel
```

## 6. System/Management API

### Health Check

```http
GET /api/v1/health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00Z",
  "uptime_seconds": 86400,
  "dependencies": {
    "postgres": {
      "status": "healthy",
      "latency_ms": 2
    },
    "qdrant": {
      "status": "healthy",
      "latency_ms": 5,
      "collections": 1,
      "points_count": 15234
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 1
    }
  }
}
```

### Get System Stats

```http
GET /api/v1/stats
```

**Response**:
```json
{
  "success": true,
  "data": {
    "total_sources": 5,
    "total_documents": 1234,
    "total_chunks": 15234,
    "total_embeddings": 15234,
    "storage": {
      "postgres_size_mb": 245,
      "qdrant_size_mb": 1523
    },
    "performance": {
      "avg_search_latency_ms": 45,
      "avg_ingestion_rate_docs_per_min": 120
    }
  }
}
```

### Get Configuration

```http
GET /api/v1/config
```

**Response**: Current system configuration (non-sensitive)

### Update Configuration

```http
PUT /api/v1/config
Content-Type: application/json
```

**Request Body**:
```json
{
  "search": {
    "default_limit": 10,
    "hybrid_enabled": true,
    "vector_weight": 0.7
  },
  "processing": {
    "chunk_size": 512,
    "chunk_overlap": 50
  }
}
```

## 7. Analytics API (Optional)

### Search Analytics

```http
GET /api/v1/analytics/searches?from=2024-01-01&to=2024-01-31
```

**Response**:
```json
{
  "success": true,
  "data": {
    "total_searches": 1523,
    "avg_latency_ms": 45,
    "popular_queries": [
      { "query": "authentication", "count": 234 },
      { "query": "database setup", "count": 189 }
    ],
    "search_type_distribution": {
      "vector": 45,
      "keyword": 20,
      "hybrid": 35
    }
  }
}
```

## WebSocket API (Future)

### Real-Time Updates

Connect to receive real-time updates about ingestion jobs.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/jobs/{job_id}');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(update);
  // {
  //   "type": "progress",
  //   "job_id": "uuid",
  //   "processed": 50,
  //   "total": 100,
  //   "percentage": 50
  // }
};
```

## Rate Limiting

**Default Limits**:
- Search API: 100 requests/minute
- Ingestion API: 10 requests/minute
- Other APIs: 1000 requests/minute

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

**429 Response**:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "retry_after": 60
  }
}
```

## Pagination

### Offset-based (Simple)

```http
GET /api/v1/documents?limit=20&offset=40
```

### Cursor-based (Efficient for large datasets)

```http
GET /api/v1/documents?limit=20&cursor=eyJpZCI6InV1aWQifQ==
```

**Response includes**:
```json
{
  "pagination": {
    "next_cursor": "eyJpZCI6Im5leHQtdXVpZCJ9",
    "has_more": true
  }
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `AUTHENTICATION_REQUIRED` | 401 | Missing or invalid auth |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate) |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Dependency unavailable |

## Client SDKs (Future)

### Python SDK Example

```python
from docvector import DocVectorClient

client = DocVectorClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Search
results = await client.search(
    query="how to authenticate users",
    search_type="hybrid",
    limit=10
)

# Add source
source = await client.sources.create(
    name="Next.js Docs",
    type="web",
    config={"url": "https://nextjs.org/docs"}
)

# Trigger sync
job = await client.sources.sync(source.id)
```

### JavaScript/TypeScript SDK Example

```typescript
import { DocVectorClient } from '@docvector/sdk';

const client = new DocVectorClient({
  baseURL: 'http://localhost:8000',
  apiKey: 'your-api-key'
});

// Search
const results = await client.search({
  query: 'how to authenticate users',
  searchType: 'hybrid',
  limit: 10
});

// Add source
const source = await client.sources.create({
  name: 'Next.js Docs',
  type: 'web',
  config: { url: 'https://nextjs.org/docs' }
});
```

## OpenAPI/Swagger Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## API Versioning Strategy

- **URL Versioning**: `/api/v1/`, `/api/v2/`
- **Backward Compatibility**: v1 supported for 12 months after v2 release
- **Deprecation Headers**: `Deprecation: true` and `Sunset: 2025-01-01`
- **Changelog**: Document all breaking changes

## Best Practices for API Consumers

1. **Use Pagination**: Don't request all results at once
2. **Cache Results**: Cache search results when appropriate
3. **Handle Errors**: Implement retry logic with exponential backoff
4. **Monitor Rate Limits**: Watch rate limit headers
5. **Use Filters**: Narrow searches with filters for better performance
6. **Batch Operations**: Use batch endpoints when available
7. **WebSocket for Jobs**: Use WebSocket for long-running job updates

## Summary

This API design provides:
1. **Simple**: Easy to understand and use
2. **Powerful**: Rich filtering and search options
3. **Consistent**: Uniform patterns across endpoints
4. **Documented**: Auto-generated OpenAPI docs
5. **Performant**: Async, paginated, cacheable
6. **Extensible**: Easy to add new endpoints

The API is optimized for AI agent consumption while remaining human-friendly for direct use.

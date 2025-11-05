# Database Schema Design

## Overview

DocVector uses two primary databases:
1. **PostgreSQL**: Metadata, configuration, relationships
2. **Qdrant**: Vector embeddings and fast similarity search

This document details the schema design for both.

## PostgreSQL Schema

### Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   sources   │────1:N──│  documents   │────1:N──│   chunks    │
└─────────────┘         └──────────────┘         └─────────────┘
                               │                         │
                               │                         │
                               │                  ┌──────▼──────┐
                               │                  │  embeddings │
                               │                  └─────────────┘
                               │
                        ┌──────▼──────────┐
                        │   ingestion_    │
                        │      jobs       │
                        └─────────────────┘
```

### Table: `sources`

Stores documentation source configurations.

```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'web', 'git', 'file', 'api'
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'paused', 'error'

    -- Source configuration (flexible JSON)
    config JSONB NOT NULL,

    -- Authentication (encrypted)
    auth_config JSONB,

    -- Crawling/fetching settings
    max_depth INTEGER DEFAULT 3,
    max_pages INTEGER DEFAULT 1000,
    respect_robots_txt BOOLEAN DEFAULT true,

    -- Scheduling
    sync_frequency VARCHAR(50), -- 'manual', 'hourly', 'daily', 'weekly'
    last_synced_at TIMESTAMP WITH TIME ZONE,
    next_sync_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),

    -- Indexing
    total_documents INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,

    CONSTRAINT valid_source_type CHECK (type IN ('web', 'git', 'file', 'api'))
);

-- Indexes
CREATE INDEX idx_sources_type ON sources(type);
CREATE INDEX idx_sources_status ON sources(status);
CREATE INDEX idx_sources_next_sync ON sources(next_sync_at) WHERE status = 'active';
CREATE INDEX idx_sources_config ON sources USING gin(config);
```

**Example Data**:
```json
{
    "id": "uuid",
    "name": "Supabase Documentation",
    "type": "web",
    "config": {
        "url": "https://supabase.com/docs",
        "sitemap_url": "https://supabase.com/sitemap.xml",
        "exclude_patterns": ["/blog/*", "/changelog/*"],
        "selectors": {
            "content": "article.documentation",
            "title": "h1"
        }
    },
    "sync_frequency": "daily"
}
```

### Table: `documents`

Stores document-level metadata.

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,

    -- Document identification
    url VARCHAR(2048), -- Original URL
    path VARCHAR(1024), -- File path or relative path
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 of content

    -- Content
    title VARCHAR(512),
    content TEXT, -- Full text content (optional, can be in object storage)
    content_length INTEGER,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    language VARCHAR(10) DEFAULT 'en',
    format VARCHAR(50), -- 'markdown', 'html', 'pdf', etc.

    -- Processing status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    error_message TEXT,

    -- Chunking info
    chunk_count INTEGER DEFAULT 0,
    chunking_strategy VARCHAR(50) DEFAULT 'semantic',

    -- Timestamps
    fetched_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- External metadata
    author VARCHAR(255),
    published_at TIMESTAMP WITH TIME ZONE,
    modified_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

-- Indexes
CREATE INDEX idx_documents_source ON documents(source_id);
CREATE INDEX idx_documents_hash ON documents(content_hash);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_url ON documents(url);
CREATE INDEX idx_documents_metadata ON documents USING gin(metadata);
CREATE INDEX idx_documents_created ON documents(created_at DESC);

-- Unique constraint: one document per URL per source
CREATE UNIQUE INDEX idx_documents_source_url ON documents(source_id, url) WHERE url IS NOT NULL;
```

**Example Data**:
```json
{
    "id": "uuid",
    "source_id": "source-uuid",
    "url": "https://supabase.com/docs/guides/auth",
    "title": "Authentication Guide",
    "content_hash": "abc123...",
    "metadata": {
        "section": "Guides",
        "tags": ["auth", "security"],
        "breadcrumb": ["Docs", "Guides", "Auth"]
    },
    "format": "html",
    "status": "completed"
}
```

### Table: `chunks`

Stores document chunks that will be embedded.

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- Chunk identification
    chunk_index INTEGER NOT NULL, -- Position in document (0-indexed)
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 of chunk content

    -- Content
    content TEXT NOT NULL,
    content_length INTEGER NOT NULL,

    -- Context preservation
    heading_hierarchy JSONB, -- ["h1 text", "h2 text", "h3 text"]
    previous_chunk_id UUID REFERENCES chunks(id),
    next_chunk_id UUID REFERENCES chunks(id),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Position in document
    start_position INTEGER, -- Character offset in original document
    end_position INTEGER,

    -- Embedding info
    has_embedding BOOLEAN DEFAULT false,
    embedding_model VARCHAR(255),
    vector_id VARCHAR(255), -- ID in vector database (Qdrant)

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_doc_chunk UNIQUE (document_id, chunk_index)
);

-- Indexes
CREATE INDEX idx_chunks_document ON chunks(document_id);
CREATE INDEX idx_chunks_hash ON chunks(content_hash);
CREATE INDEX idx_chunks_embedding ON chunks(has_embedding);
CREATE INDEX idx_chunks_vector_id ON chunks(vector_id);
CREATE INDEX idx_chunks_metadata ON chunks USING gin(metadata);
```

**Example Data**:
```json
{
    "id": "uuid",
    "document_id": "doc-uuid",
    "chunk_index": 0,
    "content": "Authentication in Supabase...",
    "heading_hierarchy": ["Authentication Guide", "Getting Started"],
    "metadata": {
        "code_blocks": 2,
        "has_links": true
    },
    "has_embedding": true,
    "vector_id": "qdrant-point-id"
}
```

### Table: `embeddings_cache`

Cache for embeddings to avoid recomputation.

```sql
CREATE TABLE embeddings_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 of content
    model VARCHAR(255) NOT NULL,

    -- Embedding vector (for quick lookup, main vectors in Qdrant)
    embedding_preview VECTOR(384), -- Using pgvector extension

    -- Metadata
    dimension INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 1,

    CONSTRAINT unique_hash_model UNIQUE (content_hash, model)
);

-- Indexes
CREATE INDEX idx_embeddings_hash ON embeddings_cache(content_hash);
CREATE INDEX idx_embeddings_model ON embeddings_cache(model);
CREATE INDEX idx_embeddings_accessed ON embeddings_cache(last_accessed_at);
```

### Table: `ingestion_jobs`

Track ingestion and processing jobs.

```sql
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,

    -- Job details
    job_type VARCHAR(50) NOT NULL, -- 'full_sync', 'incremental', 'manual'
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'

    -- Progress tracking
    total_documents INTEGER DEFAULT 0,
    processed_documents INTEGER DEFAULT 0,
    failed_documents INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,

    -- Error tracking
    error_message TEXT,
    error_details JSONB,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Celery task ID
    task_id VARCHAR(255),

    -- Configuration used for this job
    config JSONB,

    CONSTRAINT valid_job_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Indexes
CREATE INDEX idx_jobs_source ON ingestion_jobs(source_id);
CREATE INDEX idx_jobs_status ON ingestion_jobs(status);
CREATE INDEX idx_jobs_created ON ingestion_jobs(created_at DESC);
CREATE INDEX idx_jobs_task ON ingestion_jobs(task_id);
```

### Table: `search_analytics` (Optional)

Track search queries for analytics and improvement.

```sql
CREATE TABLE search_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Query details
    query TEXT NOT NULL,
    query_hash VARCHAR(64), -- For aggregation

    -- Filters applied
    filters JSONB,

    -- Search parameters
    search_type VARCHAR(50), -- 'vector', 'keyword', 'hybrid'
    limit_requested INTEGER,

    -- Results
    results_count INTEGER,
    top_result_score FLOAT,
    avg_result_score FLOAT,

    -- Performance
    duration_ms INTEGER,

    -- Metadata
    user_agent TEXT,
    ip_address INET,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Feedback (if user provides)
    feedback_rating INTEGER, -- 1-5
    feedback_comment TEXT
);

-- Indexes
CREATE INDEX idx_search_timestamp ON search_analytics(timestamp DESC);
CREATE INDEX idx_search_query_hash ON search_analytics(query_hash);
CREATE INDEX idx_search_type ON search_analytics(search_type);
```

## Qdrant Schema

### Collection: `documents`

Stores vector embeddings for all chunks.

**Collection Configuration**:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=384,  # Dimension of embedding model
        distance=Distance.COSINE  # Cosine similarity
    ),
    # Optional: Quantization for memory efficiency
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            quantile=0.99,
            always_ram=True,
        ),
    ),
)

# Create payload indexes for filtering
client.create_payload_index(
    collection_name="documents",
    field_name="source_id",
    field_schema=PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="documents",
    field_name="document_id",
    field_schema=PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="documents",
    field_name="language",
    field_schema=PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="documents",
    field_name="timestamp",
    field_schema=PayloadSchemaType.INTEGER
)
```

**Point Structure**:
```python
{
    "id": "uuid-or-sequential-id",  # Qdrant point ID
    "vector": [0.123, 0.456, ...],  # 384/768/1536 dimensions
    "payload": {
        # Core identifiers
        "chunk_id": "uuid",
        "document_id": "uuid",
        "source_id": "uuid",

        # Content
        "content": "The actual chunk text...",
        "title": "Document title",

        # Metadata for filtering
        "url": "https://example.com/doc",
        "language": "en",
        "format": "markdown",

        # Hierarchical context
        "heading_hierarchy": ["H1", "H2", "H3"],
        "section": "Getting Started",

        # Custom metadata
        "metadata": {
            "tags": ["auth", "security"],
            "difficulty": "beginner",
            "version": "v2.0"
        },

        # Timestamps (as Unix timestamp for filtering)
        "timestamp": 1699123456,
        "published_at": 1699000000,

        # Chunk context
        "chunk_index": 0,
        "total_chunks": 10,

        # Model info
        "embedding_model": "all-MiniLM-L6-v2"
    }
}
```

**Example Query with Filtering**:
```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    limit=10,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="source_id",
                match=MatchValue(value="source-uuid")
            ),
            FieldCondition(
                key="language",
                match=MatchValue(value="en")
            )
        ]
    ),
    score_threshold=0.7  # Minimum similarity score
)
```

## Data Migration Strategy

### Initial Setup

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Create schema version table
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES (1, 'Initial schema');
```

### Migration Tool: Alembic

Use Alembic for database migrations:

```bash
# Initialize migrations
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Add embeddings cache"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Data Retention and Cleanup

### Cleanup Policies

```sql
-- Delete old failed jobs (older than 30 days)
DELETE FROM ingestion_jobs
WHERE status = 'failed'
  AND created_at < NOW() - INTERVAL '30 days';

-- Delete unused embeddings cache (not accessed in 90 days)
DELETE FROM embeddings_cache
WHERE last_accessed_at < NOW() - INTERVAL '90 days';

-- Archive old search analytics (older than 1 year)
-- Move to separate archive table or export to object storage
```

### Scheduled Maintenance

```sql
-- Vacuum and analyze tables regularly
VACUUM ANALYZE sources;
VACUUM ANALYZE documents;
VACUUM ANALYZE chunks;
VACUUM ANALYZE embeddings_cache;

-- Reindex for optimal performance
REINDEX TABLE documents;
REINDEX TABLE chunks;
```

## Backup Strategy

### PostgreSQL Backup

```bash
# Full backup
pg_dump -Fc docvector > backup_$(date +%Y%m%d).dump

# Restore
pg_restore -d docvector backup_20240101.dump

# Continuous archiving (WAL)
# Configure in postgresql.conf:
# wal_level = replica
# archive_mode = on
# archive_command = 'cp %p /path/to/archive/%f'
```

### Qdrant Backup

```python
# Create snapshot
client.create_snapshot(collection_name="documents")

# List snapshots
snapshots = client.list_snapshots(collection_name="documents")

# Download snapshot
client.download_snapshot(
    collection_name="documents",
    snapshot_name="snapshot_name",
    output_path="/backups/"
)

# Restore from snapshot
# Upload snapshot file to Qdrant snapshots directory
# Restart Qdrant
```

## Performance Optimization

### PostgreSQL

```sql
-- Partitioning large tables (e.g., chunks by date)
CREATE TABLE chunks_partitioned (
    LIKE chunks INCLUDING ALL
) PARTITION BY RANGE (created_at);

CREATE TABLE chunks_2024_01 PARTITION OF chunks_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Materialized views for analytics
CREATE MATERIALIZED VIEW document_stats AS
SELECT
    source_id,
    COUNT(*) as total_docs,
    SUM(chunk_count) as total_chunks,
    AVG(content_length) as avg_length
FROM documents
GROUP BY source_id;

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY document_stats;
```

### Qdrant

```python
# Batch operations for better performance
from qdrant_client.models import Batch

points = []
for chunk in chunks:
    points.append(PointStruct(
        id=chunk.id,
        vector=chunk.embedding,
        payload=chunk.to_dict()
    ))

# Upsert in batches of 100
client.upsert(
    collection_name="documents",
    points=points,
    wait=False  # Async upsert
)
```

## Schema Evolution

### Adding New Fields

```sql
-- Add new column to existing table
ALTER TABLE documents
ADD COLUMN view_count INTEGER DEFAULT 0;

-- Add index
CREATE INDEX idx_documents_views ON documents(view_count);

-- Backfill if needed
UPDATE documents SET view_count = 0 WHERE view_count IS NULL;
```

### Qdrant Schema Changes

Qdrant is schema-less for payloads, so adding new fields is just:

```python
# Add new field to payload
client.set_payload(
    collection_name="documents",
    payload={"new_field": "value"},
    points=[point_id]
)
```

## Monitoring Queries

### Useful Monitoring Queries

```sql
-- Source ingestion status
SELECT
    s.name,
    s.status,
    s.total_documents,
    s.last_synced_at,
    COUNT(DISTINCT d.id) as actual_docs,
    COUNT(DISTINCT c.id) as actual_chunks
FROM sources s
LEFT JOIN documents d ON s.id = d.source_id
LEFT JOIN chunks c ON d.id = c.document_id
GROUP BY s.id;

-- Processing queue depth
SELECT status, COUNT(*)
FROM documents
GROUP BY status;

-- Recent errors
SELECT d.title, d.error_message, d.updated_at
FROM documents d
WHERE status = 'failed'
ORDER BY updated_at DESC
LIMIT 10;

-- Embedding coverage
SELECT
    COUNT(*) as total_chunks,
    COUNT(*) FILTER (WHERE has_embedding = true) as embedded_chunks,
    ROUND(100.0 * COUNT(*) FILTER (WHERE has_embedding = true) / COUNT(*), 2) as coverage_pct
FROM chunks;
```

## Summary

This schema design provides:
1. **Flexibility**: JSONB for extensible metadata
2. **Performance**: Proper indexing, partitioning options
3. **Relationships**: Clear foreign keys and cascades
4. **Auditability**: Timestamps and status tracking
5. **Scalability**: Partition support, cleanup policies
6. **Reliability**: Backup and migration strategies

The dual-database approach (PostgreSQL + Qdrant) leverages the strengths of each:
- **PostgreSQL**: Complex queries, relationships, ACID guarantees
- **Qdrant**: Fast vector similarity search, rich filtering

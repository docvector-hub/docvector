# Context7-Style Features in DocVector

This document describes the Context7-inspired features that have been added to DocVector, making it a powerful, self-hosted alternative to Context7 with advanced documentation search and code snippet extraction.

## Overview

DocVector now includes all major features from Context7:

1. ✅ Multi-Stage Reranking System (5 metrics)
2. ✅ LLM-Based Content Enrichment
3. ✅ Version-Specific Documentation
4. ✅ Library Resolution System
5. ✅ Topic-Focused Retrieval
6. ✅ Token-Limited Responses
7. ✅ Model Context Protocol (MCP) Integration
8. ✅ Code Snippet Extraction & Quality Scoring

---

## 1. Multi-Stage Reranking System

### Overview
DocVector now uses a 5-metric reranking algorithm similar to Context7 to surface the best results first, not just relying on vector similarity.

### The 5 Metrics

1. **Relevance Score (35% weight)**: How well the content matches the query
   - Exact phrase matching
   - Word overlap
   - Term frequency

2. **Code Quality Score (25% weight)**: Quality of code snippets
   - Presence of imports/requires
   - Function definitions
   - Comments and documentation
   - Reasonable length
   - Proper code structure

3. **Formatting Score (15% weight)**: Readability and formatting
   - Consistent indentation
   - Reasonable line lengths
   - Proper spacing

4. **Metadata Score (10% weight)**: Richness of metadata
   - Title presence
   - Language information
   - Topic tags
   - Enrichment/explanation

5. **Initialization Score (15% weight)**: Getting started guidance
   - Keywords like "install", "setup", "getting started"
   - Main/entry point patterns
   - Basic instantiation examples

### Usage

```python
from docvector.search.reranker import MultiStageReranker

reranker = MultiStageReranker(
    relevance_weight=0.35,
    code_quality_weight=0.25,
    formatting_weight=0.15,
    metadata_weight=0.10,
    initialization_weight=0.15,
)

ranked_results = reranker.rerank(
    query="how to connect to MongoDB",
    results=search_results,
    use_stored_scores=True,
)
```

### API Usage

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how to connect to MongoDB",
    "limit": 10,
    "use_reranking": true
  }'
```

---

## 2. LLM-Based Content Enrichment

### Overview
During ingestion, DocVector can use LLMs (OpenAI GPT-4o-mini by default) to:
- Generate brief explanations for code snippets
- Extract relevant topic tags
- Add context to documentation chunks

### Usage

```python
from docvector.processing.enrichment import ContentEnricher

enricher = ContentEnricher(model="gpt-4o-mini")

# Enrich a code snippet
result = await enricher.enrich_code_snippet(
    code="import qdrant_client\nclient = qdrant_client.QdrantClient(...)",
    language="python",
    context="Connecting to Qdrant vector database",
)

# Result:
# {
#   "explanation": "Initializes a connection to Qdrant vector database using the official Python client.",
#   "topics": ["database", "vector-search", "connection", "qdrant"]
# }

# Batch enrichment
snippets = [{"code": "...", "language": "python"}, ...]
enriched = await enricher.batch_enrich_snippets(snippets, batch_size=5)
```

### Database Storage
Enrichment data is stored in the `chunks` table:
- `enrichment`: LLM-generated explanation
- `topics`: Array of topic tags

---

## 3. Version-Specific Documentation

### Overview
DocVector now supports multiple versions of the same library, allowing users to query version-specific documentation.

### Database Schema
- **libraries** table: Stores library metadata
  - `library_id`: Unique identifier (e.g., "mongodb/docs", "vercel/next.js")
  - `name`: Human-readable name
  - `aliases`: Alternative names for matching

- **sources** table: Enhanced with:
  - `library_id`: Foreign key to libraries
  - `version`: Version string (e.g., "3.11", "18.2.0")

### Usage

```python
from docvector.services.library_service import LibraryService

# Create a library
library = await library_service.create_library(
    library_id="mongodb/docs",
    name="MongoDB Documentation",
    description="Official MongoDB documentation",
    aliases=["mongo", "mongodb"],
)

# Create version-specific sources
source_v6 = await source_service.create(
    name="MongoDB Docs v6",
    type="web",
    library_id=library.id,
    version="6.0",
    config={"start_url": "https://docs.mongodb.com/v6.0/"},
)

source_v7 = await source_service.create(
    name="MongoDB Docs v7",
    type="web",
    library_id=library.id,
    version="7.0",
    config={"start_url": "https://docs.mongodb.com/v7.0/"},
)
```

### API Usage

```bash
# Search with version filter
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "aggregation pipeline",
    "library_id": "mongodb/docs",
    "version": "7.0"
  }'
```

---

## 4. Library Resolution System

### Overview
Context7-style library name resolution that maps common library names to standardized library IDs.

### Usage

```python
from docvector.services.library_service import LibraryService

# Resolve library name
library_id = await library_service.resolve_library_id("next.js")
# Returns: "vercel/next.js"

library_id = await library_service.resolve_library_id("mongo")
# Returns: "mongodb/docs"
```

### API Usage

```bash
# Resolve library
curl -X POST http://localhost:8000/api/v1/libraries/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "library_name": "next.js"
  }'

# Response:
# {
#   "library_id": "vercel/next.js",
#   "name": "Next.js",
#   "description": "The React Framework for Production"
# }

# If not found, returns suggestions:
# {
#   "library_id": null,
#   "name": null,
#   "description": null,
#   "suggestions": [
#     {"library_id": "vercel/next.js", "name": "Next.js"},
#     {"library_id": "nextjs/docs", "name": "Next.js Docs"}
#   ]
# }
```

---

## 5. Topic-Focused Retrieval

### Overview
Filter search results by specific topics extracted during enrichment or manually tagged.

### Usage

```python
# Search with topic filter
results = await search_service.search(
    query="database connection",
    filters={"topics": "authentication"},
)
```

### API Usage

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "database connection",
    "topic": "authentication"
  }'
```

### Topics are stored as arrays in chunks
Examples: `["getting-started", "installation", "configuration"]`

---

## 6. Token-Limited Responses

### Overview
Context7-style token limiting ensures responses fit within LLM context windows.

### Usage

```python
from docvector.utils.token_utils import TokenLimiter

limiter = TokenLimiter()

# Truncate text to token limit
truncated = limiter.truncate_to_tokens(
    text=long_text,
    max_tokens=1000,
    preserve_sentences=True,
)

# Limit search results to token budget
limited_results = limiter.limit_results_to_tokens(
    results=search_results,
    max_tokens=5000,
    content_key="content",
)
```

### API Usage

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how to use MongoDB",
    "max_tokens": 5000
  }'
```

### Advanced: Tiktoken Integration

For exact token counts (requires `tiktoken` library):

```python
from docvector.utils.token_utils import TikTokenCounter

counter = TikTokenCounter(encoding_name="cl100k_base")
exact_count = counter.count_tokens(text)
truncated = counter.truncate_to_tokens(text, max_tokens=1000)
```

---

## 7. Model Context Protocol (MCP) Integration

### Overview
DocVector now includes an MCP server for integration with AI code editors like Cursor, Claude Code, Windsurf, VSCode, etc.

### MCP Tools

1. **resolve-library-id**: Map library names to IDs
2. **get-library-docs**: Fetch documentation for a library
3. **search-docs**: Search all documentation

### Running the MCP Server

```bash
# Run over stdio (for MCP clients)
python -m docvector.mcp_server stdio

# Run over HTTP
python -m docvector.mcp_server
# Server runs on http://0.0.0.0:8001/mcp
```

### Client Configuration

**Cursor / Claude Code / VSCode**

Add to your MCP config file:

```json
{
  "mcpServers": {
    "docvector": {
      "command": "python",
      "args": ["-m", "docvector.mcp_server", "stdio"]
    }
  }
}
```

Or use HTTP:

```json
{
  "mcpServers": {
    "docvector": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

### MCP Tool Examples

```json
// resolve-library-id
{
  "name": "resolve-library-id",
  "arguments": {
    "libraryName": "mongodb"
  }
}

// get-library-docs
{
  "name": "get-library-docs",
  "arguments": {
    "libraryId": "mongodb/docs",
    "topic": "aggregation",
    "version": "7.0",
    "tokens": 5000
  }
}

// search-docs
{
  "name": "search-docs",
  "arguments": {
    "query": "how to create indexes",
    "libraryId": "mongodb/docs",
    "tokens": 5000
  }
}
```

---

## 8. Code Snippet Extraction & Quality Scoring

### Overview
Automatically extract code snippets from HTML and Markdown with quality scoring.

### Features
- Detects code blocks in HTML (`<code>`, `<pre>`)
- Extracts fenced code blocks from Markdown
- Detects programming language
- Scores code quality, formatting, and usefulness
- Extracts surrounding context

### Usage

```python
from docvector.processing.code_extractor import CodeExtractor

extractor = CodeExtractor()

# Extract from HTML
snippets = extractor.extract_from_html(html_content)

# Extract from Markdown
snippets = extractor.extract_from_markdown(markdown_content)

# Each snippet has:
# - content: The code
# - language: Detected language
# - quality_score: 0-1 score
# - formatting_score: 0-1 score
# - metadata_score: 0-1 score
# - initialization_score: 0-1 score
# - context: Surrounding text
```

### Quality Scoring Criteria

**Code Quality**:
- Imports/requires present
- Function definitions
- Comments
- Reasonable length (5-50 lines)
- Proper structure (braces, parentheses)

**Formatting**:
- Consistent indentation
- Reasonable line lengths (<100 chars)
- Proper spacing

**Initialization**:
- Contains setup/install keywords
- Has main/entry point
- Basic instantiation examples

### Database Storage

Code snippets are stored in chunks with:
- `is_code_snippet`: Boolean flag
- `code_language`: Detected language
- `code_quality_score`: Quality metric
- `formatting_score`: Formatting metric
- `initialization_score`: Getting started metric

---

## Database Migration

To apply all Context7 features to your database:

```bash
# Run migration
alembic upgrade 002

# Or manually
python -m docvector.db.migrations.versions.002_context7_features
```

### Schema Changes

**New Tables**:
- `libraries`: Library metadata and aliases

**Enhanced Tables**:
- `sources`: Added `library_id`, `version`
- `chunks`: Added 10+ new columns for code snippets, topics, enrichment, and scores

**New Indexes**:
- `idx_libraries_library_id`
- `idx_sources_library_id`
- `idx_sources_version`
- `idx_chunks_is_code_snippet`
- `idx_chunks_code_language`
- `idx_chunks_topics` (GIN index for array search)

---

## Complete API Example

```bash
# 1. Create a library
curl -X POST http://localhost:8000/api/v1/libraries \
  -H "Content-Type: application/json" \
  -d '{
    "library_id": "mongodb/docs",
    "name": "MongoDB",
    "description": "Official MongoDB documentation",
    "aliases": ["mongo", "mongodb"],
    "homepage_url": "https://mongodb.com",
    "repository_url": "https://github.com/mongodb/docs"
  }'

# 2. Create a version-specific source
curl -X POST http://localhost:8000/api/v1/sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MongoDB 7.0 Docs",
    "type": "web",
    "library_id": "<library-uuid>",
    "version": "7.0",
    "config": {
      "start_url": "https://docs.mongodb.com/v7.0/",
      "max_depth": 3,
      "max_pages": 500
    }
  }'

# 3. Ingest the documentation
curl -X POST http://localhost:8000/api/v1/ingest/source \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "<source-uuid>"
  }'

# 4. Search with all Context7 features
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how to create an index",
    "library_id": "mongodb/docs",
    "version": "7.0",
    "topic": "indexes",
    "use_reranking": true,
    "max_tokens": 5000,
    "limit": 10
  }'
```

---

## Comparison: DocVector vs Context7

| Feature | Context7 | DocVector |
|---------|----------|-----------|
| **Multi-Stage Reranking** | ✅ 5-metric algorithm | ✅ 5-metric algorithm |
| **LLM Enrichment** | ✅ LLM-enhanced | ✅ LLM-enhanced (OpenAI) |
| **Version Support** | ✅ Multi-version | ✅ Multi-version |
| **Library Resolution** | ✅ Name → ID mapping | ✅ Name → ID mapping |
| **Topic Filtering** | ✅ Topic-based | ✅ Topic-based |
| **Token Limiting** | ✅ Token-aware | ✅ Token-aware (tiktoken) |
| **MCP Integration** | ✅ MCP server | ✅ MCP server |
| **Code Extraction** | ✅ Code-focused | ✅ Code-focused |
| **Deployment** | SaaS only | ✅ Self-hosted |
| **Custom Sources** | ❌ Pre-indexed only | ✅ Any website |
| **Open Source** | ⚠️ MCP only | ✅ Fully open |
| **Pre-Indexed Libraries** | ✅ 33k+ libraries | ❌ User-configured |

---

## Future Enhancements

Potential improvements to match or exceed Context7:

1. **Automatic Library Discovery**: Crawl and index popular libraries automatically
2. **BM25 Keyword Search**: Full hybrid search with BM25 + vector
3. **Code Execution Validation**: Test code snippets during ingestion
4. **Dependency Graph**: Show relationships between libraries
5. **Change Detection**: Detect documentation updates and re-index
6. **Multilingual Support**: Support non-English documentation
7. **Custom Reranking Weights**: Per-library reranking configuration

---

## Getting Started

1. **Install Dependencies**:
   ```bash
   pip install -e ".[all]"
   ```

2. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Start API Server**:
   ```bash
   python -m docvector.api.main
   ```

4. **Start MCP Server** (optional):
   ```bash
   python -m docvector.mcp_server
   ```

5. **Configure Your AI Editor**: Add DocVector MCP server to your editor config

6. **Start Ingesting**: Create libraries, sources, and ingest documentation

---

## License

DocVector is open-source software. All Context7-inspired features are implemented from scratch and are fully open-source.

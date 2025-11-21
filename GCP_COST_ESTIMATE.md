# GCP Cost Estimate for Context7-Style Documentation Service

## Cost Breakdown for Pre-Indexed Documentation Platform

### Assumptions
- **Libraries**: Start with 1,000 → Scale to 33,000+ (Context7 level)
- **Pages per library**: Average 500 pages
- **Crawl frequency**: Weekly full recrawl + daily change detection
- **Users**: 1,000 → 10,000 active users
- **Queries**: 100K → 1M per month
- **Region**: us-central1

---

## 💰 Monthly Cost Estimates

### Small Scale (1,000 libraries, 100K queries/month)

| Component | Service | Specs | Monthly Cost |
|-----------|---------|-------|--------------|
| **API Servers** | Cloud Run | 2 instances, 2 vCPU, 4GB RAM | $50 |
| **Crawler Workers** | Cloud Run Jobs | 5 workers, 1 vCPU, 2GB RAM, 24/7 | $150 |
| **PostgreSQL** | Cloud SQL | db-custom-4-16384 (4 vCPU, 16GB) | $250 |
| **Vector DB (Qdrant)** | GCE n2-standard-4 | 4 vCPU, 16GB RAM, 500GB SSD | $200 |
| **Redis Cache** | Memorystore | 5GB Standard tier | $40 |
| **Embeddings (OpenAI)** | OpenAI API | 50M tokens/month @ $0.02/1M | $1,000 |
| **LLM Enrichment** | OpenAI GPT-4o-mini | 10M tokens/month @ $0.15/1M input | $150 |
| **Storage** | Cloud Storage | 500GB for backups/archives | $10 |
| **Bandwidth** | Network Egress | 1TB outbound | $120 |
| **Monitoring** | Cloud Logging + Monitoring | Standard tier | $50 |
| **Load Balancer** | Cloud Load Balancing | 100K requests | $20 |
| | | **TOTAL** | **~$2,040/month** |

---

### Medium Scale (10,000 libraries, 500K queries/month)

| Component | Service | Specs | Monthly Cost |
|-----------|---------|-------|--------------|
| **API Servers** | Cloud Run | 5 instances, 4 vCPU, 8GB RAM, autoscale | $200 |
| **Crawler Workers** | Cloud Run Jobs | 20 workers, 2 vCPU, 4GB RAM, 24/7 | $800 |
| **PostgreSQL** | Cloud SQL | db-custom-8-32768 (8 vCPU, 32GB) HA | $600 |
| **Vector DB (Qdrant)** | GKE Cluster | 3 nodes, n2-highmem-4, 2TB SSD | $800 |
| **Redis Cache** | Memorystore | 25GB Standard tier | $180 |
| **Embeddings (OpenAI)** | OpenAI API | 500M tokens/month @ $0.02/1M | $10,000 |
| **LLM Enrichment** | OpenAI GPT-4o-mini | 100M tokens/month @ $0.15/1M | $1,500 |
| **Storage** | Cloud Storage | 2TB for backups/archives | $40 |
| **Bandwidth** | Network Egress | 5TB outbound | $600 |
| **Monitoring** | Cloud Logging + Monitoring | Enhanced | $150 |
| **Load Balancer** | Cloud Load Balancing | 500K requests | $50 |
| **CDN** | Cloud CDN | 2TB egress | $160 |
| | | **TOTAL** | **~$15,080/month** |

---

### Large Scale (33,000+ libraries, 1M+ queries/month - Context7 Level)

| Component | Service | Specs | Monthly Cost |
|-----------|---------|-------|--------------|
| **API Servers** | Cloud Run | 20 instances, 4 vCPU, 8GB RAM, autoscale | $800 |
| **Crawler Workers** | Cloud Run Jobs | 100 workers, 2 vCPU, 4GB RAM, 24/7 | $4,000 |
| **PostgreSQL** | Cloud SQL | db-custom-16-65536 (16 vCPU, 64GB) HA | $1,400 |
| **Vector DB (Qdrant)** | GKE Cluster | 6 nodes, n2-highmem-8, 5TB SSD | $3,200 |
| **Redis Cache** | Memorystore | 100GB High Availability | $800 |
| **Embeddings (OpenAI)** | OpenAI API | 1.65B tokens/month @ $0.02/1M | $33,000 |
| **LLM Enrichment** | OpenAI GPT-4o-mini | 330M tokens/month @ $0.15/1M | $5,000 |
| **Storage** | Cloud Storage | 10TB for backups/archives | $200 |
| **Bandwidth** | Network Egress | 20TB outbound | $2,400 |
| **Monitoring** | Cloud Logging + Monitoring | Premium | $400 |
| **Load Balancer** | Cloud Load Balancing | 1M+ requests | $100 |
| **CDN** | Cloud CDN | 10TB egress | $800 |
| | | **TOTAL** | **~$52,100/month** |

---

## 🔍 Detailed Cost Analysis

### 1. Embedding Generation Costs (Biggest Expense!)

**OpenAI Embeddings** (text-embedding-3-small):
- Cost: $0.02 per 1M tokens
- Average doc page: ~2,000 tokens
- Initial indexing of 33k libraries × 500 pages = 16.5M pages
- **One-time cost**: 16.5M pages × 2K tokens = 33B tokens = **$660,000**
- **Monthly recrawl (10% change)**: 3.3B tokens = **$66,000/month**

**Self-Hosted Embeddings** (Alternative):
- Model: all-MiniLM-L6-v2 or BGE-large
- Hardware: NVIDIA A100 GPU
- GCP: a2-highgpu-1g (1× A100, 12 vCPU, 85GB RAM)
- Cost: ~$3,700/month
- Can process ~50M tokens/hour
- **Saves 90%+ on embedding costs at scale!**

### 2. LLM Enrichment Costs

**GPT-4o-mini** (for code snippet enrichment):
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens
- Average enrichment: 500 input + 100 output tokens per code snippet
- Estimate: 20% of chunks have code = 3.3M code snippets
- **One-time**: (3.3M × 500) / 1M × $0.15 + (3.3M × 100) / 1M × $0.60 = **$2,475**
- **Monthly updates**: ~$250/month

**Alternative: Skip LLM Enrichment**
- Use rule-based topic extraction
- Pre-defined topic taxonomies
- **Saves $250-2,500/month**

### 3. Vector Database (Qdrant)

**Storage Requirements**:
- 16.5M pages × 3 chunks/page = ~50M chunks
- 1536-dim embeddings × 4 bytes = 6KB per vector
- Total: 50M × 6KB = **300GB** vector data
- Plus metadata: ~200GB
- **Total storage**: 500GB → 2TB with growth

**Compute**:
- RAM: Need vectors in memory for speed
- 300GB vectors + OS overhead = 512GB RAM minimum
- GCE: n2-highmem-8 (8 vCPU, 64GB RAM) × 8 nodes = **$2,400/month**

**Alternative: Managed Vector DB**
- Vertex AI Vector Search: $0.80/hour per 1B dimensions
- 50M chunks × 1536 dims = 76.8B dimensions
- Cost: ~$1,840/month + query costs
- **Cheaper than self-hosting at this scale**

### 4. Crawling Infrastructure

**Workers**:
- 33k libraries × 500 pages = 16.5M pages
- Crawl speed: ~10 pages/second per worker
- Weekly full crawl: 16.5M / (7 × 24 × 3600 × 10) = ~27 workers needed
- Cloud Run: 27 workers × $0.15/vCPU-hour × 2 vCPU × 730 hours = **$6,000/month**

**Bandwidth**:
- Average page size: 200KB
- 16.5M pages × 200KB = 3.3TB/week
- Ingress: Free
- Egress for API: ~20TB/month = **$2,400/month**

**Optimization: Use Cloud Functions**
- Triggered crawls instead of 24/7 workers
- Cost: ~$1,000/month for scheduled crawls
- **Saves 80% on worker costs**

### 5. Database (PostgreSQL)

**Data Volume**:
- 50M chunks × 2KB text = 100GB
- Metadata: 50GB
- Indexes: 50GB
- **Total**: 200GB → 500GB with growth

**Cloud SQL**:
- db-custom-16-65536 (16 vCPU, 64GB RAM, 500GB SSD)
- High Availability: 2× cost
- **Cost**: $1,400/month

**Alternative: Self-Managed on GCE**
- n2-highmem-8 + 500GB SSD
- Cost: ~$600/month
- **Saves $800/month but requires management**

---

## 💡 Cost Optimization Strategies

### 1. Use Self-Hosted Embeddings (Saves 90%+)

**Instead of OpenAI**: $33,000/month
**Use GPU VM**: $3,700/month (A100)
**Savings**: **$29,300/month**

```python
# Use local embeddings instead
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cuda
```

### 2. Selective Crawling (Saves 50% on crawling)

**Instead of**: Weekly full crawl
**Use**: Change detection + incremental crawls

- Monitor RSS feeds, sitemaps, GitHub releases
- Only recrawl changed pages
- **Savings**: $3,000/month on workers

### 3. Skip LLM Enrichment Initially (Saves $5,000/month)

**Instead of**: GPT-4o-mini enrichment
**Use**: Rule-based topic extraction

```python
# Extract topics from headings, keywords, file paths
ENABLE_LLM_ENRICHMENT=false
```

### 4. Use Preemptible VMs (Saves 70%)

**For**: Crawler workers, batch processing
**Savings**: 70% on compute costs
**Trade-off**: Can be interrupted

### 5. Use Cloud Storage for Cold Data (Saves on DB costs)

**Strategy**: Move old/rarely-accessed docs to Cloud Storage
**Savings**: $300/month on database costs

### 6. CDN for Static Content (Reduces bandwidth)

**Use**: Cloud CDN for documentation pages
**Savings**: $1,000/month on egress costs

### 7. Batch Processing (Saves on API costs)

**Strategy**:
- Batch embeddings (100 texts at a time)
- Deduplicate before embedding
- Cache embeddings forever

**Savings**: 20% on embedding costs

---

## 📊 Optimized Cost Estimate (Context7 Scale)

| Component | Optimization | Monthly Cost |
|-----------|--------------|--------------|
| **API Servers** | Cloud Run autoscale | $800 |
| **Crawler Workers** | Cloud Functions + change detection | $1,000 |
| **PostgreSQL** | Self-managed on GCE | $600 |
| **Vector DB** | Vertex AI Vector Search | $1,840 |
| **Redis Cache** | Memorystore 100GB HA | $800 |
| **Embeddings** | Self-hosted A100 GPU | $3,700 |
| **LLM Enrichment** | Skip (rule-based) | $0 |
| **Storage** | Cloud Storage 10TB | $200 |
| **Bandwidth** | CDN optimization | $1,200 |
| **Monitoring** | Standard tier | $200 |
| **Load Balancer** | Standard | $100 |
| **CDN** | Cloud CDN 10TB | $800 |
| | **OPTIMIZED TOTAL** | **~$11,240/month** |

**vs Original**: $52,100/month
**Savings**: **78% ($40,860/month)**

---

## 🎯 Recommended Architecture by Budget

### Budget: $500-1,000/month (Startup)

- **Libraries**: 100-500
- **Embeddings**: Local (CPU-based)
- **Hosting**: Cloud Run (serverless)
- **DB**: Cloud SQL db-f1-micro or self-managed
- **Vector DB**: Qdrant on n2-standard-2
- **No LLM enrichment**
- **Simple change detection**

### Budget: $2,000-5,000/month (Growing)

- **Libraries**: 1,000-5,000
- **Embeddings**: Local GPU (T4)
- **Hosting**: Cloud Run + GKE spot instances
- **DB**: Cloud SQL db-custom-4-16384
- **Vector DB**: Qdrant cluster (3 nodes)
- **Selective LLM enrichment**
- **Smart crawling**

### Budget: $10,000-15,000/month (Production)

- **Libraries**: 10,000-20,000
- **Embeddings**: Self-hosted A100
- **Hosting**: GKE with autoscaling
- **DB**: Cloud SQL HA
- **Vector DB**: Vertex AI Vector Search
- **Targeted enrichment**
- **Advanced change detection**

### Budget: $50,000+/month (Context7 Scale)

- **Libraries**: 33,000+
- **Embeddings**: Multi-GPU cluster
- **Hosting**: Multi-region GKE
- **DB**: Cloud Spanner or sharded PostgreSQL
- **Vector DB**: Distributed Vertex AI
- **Full enrichment**
- **Real-time crawling**

---

## ⚡ Quick Start: Minimum Viable Setup

**Total Cost**: **~$500/month**

```yaml
# Cost-optimized config for 100 libraries

Compute:
  - Cloud Run: 1 instance (API)
  - Cloud Functions: Crawlers (on-demand)
  Total: $100/month

Database:
  - Cloud SQL db-f1-micro (shared CPU, 0.6GB RAM)
  Total: $15/month

Vector DB:
  - GCE e2-standard-2 (2 vCPU, 8GB RAM)
  - Qdrant self-hosted
  Total: $50/month

Cache:
  - Memorystore 1GB
  Total: $30/month

Embeddings:
  - Local CPU-based (sentence-transformers)
  - Runs on API server
  Total: $0 (included in compute)

Storage:
  - 100GB Cloud Storage
  Total: $5/month

Bandwidth:
  - 500GB egress
  Total: $60/month

Total: ~$260/month
```

**Add $240/month buffer** = **$500/month**

---

## 📈 Scaling Timeline & Costs

| Libraries | Monthly Cost (Optimized) | One-Time Setup |
|-----------|-------------------------|----------------|
| 100 | $500 | $500 |
| 500 | $1,000 | $2,000 |
| 1,000 | $2,000 | $5,000 |
| 5,000 | $5,000 | $20,000 |
| 10,000 | $8,000 | $40,000 |
| 33,000 | $11,000 | $120,000 |

---

## 🔑 Key Takeaways

1. **Embeddings are 60%+ of costs** at scale
   - Use self-hosted models to save 90%+

2. **Smart crawling saves 50%** on infrastructure
   - Change detection > full recrawls

3. **LLM enrichment is optional**
   - Rule-based extraction works well
   - Save $5,000/month

4. **Optimize for your scale**
   - Start small ($500/month)
   - Scale gradually

5. **One-time indexing is expensive**
   - 33k libraries = $120k setup cost
   - Build incrementally instead

---

## 💰 Revenue Model Needed

To break even at Context7 scale:

**Costs**: $11,000/month (optimized)
**Break-even scenarios**:

1. **Free tier + Pro tier**
   - 1,000 users @ $10/month = $10,000
   - Need 1,100+ paid users

2. **API-based pricing**
   - $0.01 per query
   - Need 1.1M queries/month

3. **Enterprise licenses**
   - 10 companies @ $1,500/month = $15,000
   - Profitable!

**Context7 likely uses**: Freemium + Enterprise model

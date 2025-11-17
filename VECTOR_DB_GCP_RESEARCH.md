# Vector Database Options for GCP - Documentation Search at Scale

**Research Date:** 2025-11-17
**Use Case:** Documentation search with semantic vector embeddings
**Vector Dimensions:** 1536 (OpenAI text-embedding-3-small or equivalent)

---

## Executive Summary

This research compares vector database options for deploying a documentation search system on Google Cloud Platform at three scales:

- **Small Scale:** 500 libraries (~500K-1M vectors)
- **Medium Scale:** 5,000 libraries (~5M-10M vectors)
- **Large Scale:** 33,000 libraries (~50M-100M vectors)

**Key Findings:**
- **Vertex AI Vector Search** is cost-effective for small to medium scale with minimal operational overhead
- **Self-hosted Qdrant on GKE** becomes more economical at large scale but requires DevOps expertise
- **AlloyDB with ScaNN** offers best performance but higher baseline costs
- **Pinecone** provides simplicity but costs scale linearly and can become expensive

---

## 1. Vertex AI Vector Search (Matching Engine)

Google's managed vector database service, optimized for billion-scale similarity search.

### Pricing Model (2025)

#### Index Serving (Primary Cost)
Per-node-hour pricing based on machine type:

| Machine Type | vCPU | RAM | Price/Hour (us-central1) | Monthly Cost (730 hrs) |
|--------------|------|-----|--------------------------|------------------------|
| e2-standard-2 | 2 | 8 GB | $0.094 | $68.62 |
| e2-standard-16 | 16 | 64 GB | $0.75 | $547.50 |

**Shard Size Selection:**
- `SHARD_SIZE_SMALL`: Uses e2-standard-2 instances
- `SHARD_SIZE_MEDIUM`: Uses e2-standard-16 instances

#### Index Building & Updates
- **Initial index build:** $3.00 per GiB processed
- **Streaming updates:** $0.45 per GiB ingested

#### Cost Calculation Formula
```
Total Monthly Cost = (# replicas × # shards × node_hourly_cost × 730) + (data_size_GiB × $3 × updates_per_month)
```

### Performance Characteristics

**Strengths:**
- Built on Google's ScaNN algorithm (12 years of research)
- Handles billions of vectors with low latency
- Automatic scaling and load balancing
- Multi-region deployment support

**Query Performance:**
- Latency: 10-50ms typical (p95)
- QPS per node: 100-500 queries/second (varies by shard size)
- Supports approximate nearest neighbor (ANN) search with configurable accuracy

**Limitations:**
- Minimum of 1-2 hours to build initial index
- No support for hybrid (keyword + vector) search natively
- Limited metadata filtering capabilities compared to specialized DBs
- Requires data in Google Cloud Storage for indexing

### Scaling Capabilities

**Vertical Scaling:**
- Switch between SHARD_SIZE_SMALL and SHARD_SIZE_MEDIUM
- Each shard supports up to 20M vectors efficiently

**Horizontal Scaling:**
- Automatic sharding based on data size
- Can scale to billions of vectors across multiple shards
- Each additional shard adds proportional cost

**Autoscaling:**
- Manual replica adjustment required
- No true autoscaling based on query load

### Integration with GCP Services

**Excellent Integration:**
- Native integration with Vertex AI Platform
- Works seamlessly with Cloud Storage
- Compatible with Vertex AI Workbench notebooks
- Integrated monitoring via Cloud Monitoring

**API Access:**
- REST API and gRPC support
- Python, Java, Node.js client libraries
- Can be called from Cloud Run, GKE, App Engine

### Limitations

1. **Vendor Lock-in:** Tied to Google Cloud ecosystem
2. **Limited Flexibility:** Cannot customize index algorithms
3. **Metadata Filtering:** Less powerful than dedicated vector DBs
4. **Cold Start:** Index deployment takes time
5. **Cost Visibility:** Complex pricing with multiple components
6. **No Hybrid Search:** Requires separate implementation for keyword search

---

## 2. Self-Hosted Qdrant on GKE

Open-source vector database written in Rust, deployable on Kubernetes.

### Instance Types Needed

#### Storage Requirements (1536-dimensional vectors)

| Scale | Vectors | Raw Vector Data | With Metadata (1.5x) | Recommended Storage |
|-------|---------|-----------------|----------------------|---------------------|
| Small | 1M | 6 GB | 9 GB | 100 GB SSD |
| Medium | 10M | 60 GB | 90 GB | 500 GB SSD |
| Large | 100M | 600 GB | 900 GB | 2 TB SSD |

**Formula:** `storage_gb = vectors × 1536 × 4 bytes × 1.5 / (1024^3)`

#### Memory Requirements

**Without Quantization:**
- Formula: `RAM = vectors × 1536 × 4 × 1.5`
- 1M vectors: ~9 GB RAM
- 10M vectors: ~90 GB RAM
- 100M vectors: ~900 GB RAM

**With Binary Quantization (32x reduction):**
- 1M vectors: ~300 MB RAM
- 10M vectors: ~3 GB RAM
- 100M vectors: ~30 GB RAM

**With Scalar Quantization (4x reduction):**
- 1M vectors: ~2.25 GB RAM
- 10M vectors: ~22.5 GB RAM
- 100M vectors: ~225 GB RAM

### Cluster Configuration by Scale

#### Small Scale (500K-1M vectors)
```yaml
Configuration:
  Nodes: 1
  Instance: n2-highmem-2 (2 vCPU, 16 GB RAM)
  Storage: 100 GB SSD persistent disk
  Replication: Single node (no HA)

Costs:
  Compute: ~$95/month
  Storage: ~$17/month (100 GB × $0.17/GB)
  Total: ~$112/month
```

#### Medium Scale (5M-10M vectors)
```yaml
Configuration:
  Nodes: 3 (StatefulSet across 3 zones)
  Instance: n2-highmem-4 (4 vCPU, 32 GB RAM)
  Storage: 500 GB SSD per node
  Replication: 2x (HA enabled)

Costs:
  Compute: ~$382/month per node × 3 = $1,146/month
  Storage: ~$85/month per node × 3 = $255/month
  GKE Control Plane: $73/month
  Total: ~$1,474/month
```

#### Large Scale (50M-100M vectors)
```yaml
Configuration:
  Nodes: 6 (distributed sharding)
  Instance: n2-highmem-8 (8 vCPU, 64 GB RAM)
  Storage: 2 TB SSD per node
  Replication: 2x (HA enabled)
  Quantization: Scalar (enabled)

Costs:
  Compute: ~$382/month per node × 6 = $2,292/month
  Storage: ~$340/month per node × 6 = $2,040/month
  GKE Control Plane: $73/month
  Load Balancer: $18/month
  Total: ~$4,423/month

With 1-year CUD (25% discount):
  Total: ~$3,390/month
```

### Scaling Strategy

**Horizontal Scaling:**
1. Start with single node for development
2. Move to 3-node cluster for HA
3. Add nodes as data grows (6+ nodes for 50M+ vectors)
4. Enable sharding for distributed collections

**Vertical Scaling:**
- Increase RAM for better performance
- Move from n2-standard to n2-highmem for vector workloads
- Use local SSD for maximum I/O performance (costs more)

**Optimization Techniques:**
1. **Quantization:** Reduce memory by 4-32x
2. **Disk-based storage (mmap):** Store vectors on disk, cache in RAM
3. **Filtering optimization:** Create payload indexes for common filters
4. **Batch operations:** Group inserts/updates for efficiency

### Operational Overhead

**Initial Setup (40-60 hours):**
- GKE cluster configuration
- StatefulSet deployment with persistent volumes
- Service mesh and load balancer setup
- Monitoring and alerting (Prometheus/Grafana)
- Backup and disaster recovery procedures

**Ongoing Maintenance (10-20 hours/month):**
- Security patches and updates
- Performance monitoring and optimization
- Capacity planning and scaling
- Backup verification and testing
- Troubleshooting issues

**Skills Required:**
- Kubernetes administration
- GCP networking and IAM
- Database performance tuning
- Infrastructure as code (Terraform/Helm)

### Cost Comparison vs Vertex AI

| Scale | Qdrant on GKE | Vertex AI | Savings | Notes |
|-------|---------------|-----------|---------|-------|
| Small (1M) | $112/mo | $200-300/mo | 40-60% | Without HA |
| Medium (10M) | $1,474/mo | $800-1,200/mo | -23% to +84% | Vertex AI wins |
| Large (100M) | $4,423/mo | $2,500-4,000/mo | -10% to +77% | Comparable |
| Large w/ CUD | $3,390/mo | $2,500-4,000/mo | 15-35% | Qdrant wins |

**Break-even Point:** Around 50M vectors, self-hosted becomes cost-competitive

---

## 3. Other Options

### A. Pinecone (External Service)

**Pricing (2025):**
- **Starter (Free):** 2 GB storage, 2M write units/month, 1M read units/month
- **Standard:** $50/month minimum, then usage-based
  - Storage: $0.33 per GB/month (approx)
  - Write units: $6 per million
  - Read units: $24 per million
- **Enterprise:** $500/month minimum commitment

**Cost Estimates by Scale:**

| Scale | Vectors | Storage (GB) | Monthly Cost | Notes |
|-------|---------|--------------|--------------|-------|
| Small (1M) | 1M | ~10 GB | $50-100 | Includes queries |
| Medium (10M) | 10M | ~100 GB | $300-500 | Based on usage |
| Large (100M) | 100M | ~1 TB | $3,000-5,000 | Enterprise tier |

**Pros:**
- Zero operational overhead
- Excellent documentation and SDKs
- Fast time to market
- Automatic scaling
- Good performance (10-50ms latency)

**Cons:**
- Most expensive option at scale
- No self-hosted option
- Data residency concerns (not in your GCP account)
- Limited customization
- Costs scale linearly with data

**When to Use:**
- Rapid prototyping and MVP
- Small to medium scale (<10M vectors)
- Teams without DevOps resources
- Budget available for convenience

---

### B. Weaviate on GKE

**Deployment Model:** Self-hosted on GKE (similar to Qdrant)

**Instance Requirements:**

| Scale | Instance Type | Storage | Est. Monthly Cost |
|-------|--------------|---------|-------------------|
| Small (1M) | e2-highmem-2 (2 vCPU, 16 GB) | 100 GB | $110-150 |
| Medium (10M) | n2-highmem-4 (4 vCPU, 32 GB) × 3 | 500 GB each | $1,500-2,000 |
| Large (100M) | n2-highmem-8 (8 vCPU, 64 GB) × 6 | 2 TB each | $4,500-5,500 |

**Weaviate Cloud Pricing (Managed):**
- $0.095 per 1M vector dimensions stored
- Example: 100M vectors × 1536 dims = 153.6B dimensions
- Cost: 153,600M × $0.095 = **$14,592/month**
- Additional costs for backups, regional pricing, replication

**Comparison to Qdrant:**

| Feature | Weaviate | Qdrant |
|---------|----------|--------|
| Performance | Good (built on HNSW) | Excellent (Rust-optimized) |
| Memory usage | Higher | Lower (with quantization) |
| Hybrid search | Native support | Limited |
| GraphQL API | Yes | No |
| Filtering | Strong | Very strong |
| Cost (self-hosted) | Similar | Slightly lower |
| Maturity | Mature | Mature |

**When to Use Weaviate:**
- Need GraphQL API
- Require hybrid search (vector + keyword)
- Multi-modal search (text + images)
- Prefer Weaviate's schema-based approach

---

### C. pgvector on Cloud SQL / AlloyDB

**pgvector Extension:** PostgreSQL extension for vector similarity search

#### Cloud SQL for PostgreSQL

**Pricing (Enterprise Edition, us-central1):**
- vCPU: ~$0.0821 per vCPU/hour
- RAM: ~$0.0138 per GB/hour
- Storage (SSD): $0.17 per GB/month

**Instance Recommendations:**

| Scale | Instance | vCPU | RAM | Storage | Monthly Cost |
|-------|----------|------|-----|---------|--------------|
| Small (1M) | db-custom-4-16384 | 4 | 16 GB | 100 GB | $280-350 |
| Medium (10M) | db-custom-8-32768 | 8 | 32 GB | 500 GB | $600-750 |
| Large (100M) | db-custom-16-65536 | 16 | 64 GB | 2 TB | $1,400-1,800 |

**Performance Characteristics:**
- **Throughput:** Moderate (100-500 QPS depending on instance)
- **Latency:** 20-100ms typical
- **Index:** HNSW (Hierarchical Navigable Small World)
- **Limitations:** Single-node scalability ceiling at ~100M vectors

#### AlloyDB for PostgreSQL

**Pricing (us-central1):**
- vCPU: $0.06608 per vCPU/hour ($48.24/month per vCPU)
- RAM: $0.00886 per GB/hour ($6.47/month per GB)
- Storage: $0.10 per GB/month (cheaper than Cloud SQL)

**ScaNN Extension (October 2024):**
- 10x better latency than pgvector HNSW on large datasets
- 4x smaller memory footprint
- Outperforms on datasets that don't fit in memory
- Free with AlloyDB (no additional cost)

**Instance Recommendations:**

| Scale | vCPU | RAM | Storage | Monthly Cost | With CUD (52%) |
|-------|------|-----|---------|--------------|----------------|
| Small (1M) | 4 | 32 GB | 100 GB | $410 | $197 |
| Medium (10M) | 8 | 64 GB | 500 GB | $870 | $417 |
| Large (100M) | 16 | 128 GB | 2 TB | $1,972 | $946 |

**Performance Benchmarks (ScaNN vs pgvector HNSW):**
- **Large dataset (1B vectors):** 431ms latency (ScaNN) vs >4000ms (pgvector)
- **Instance efficiency:** ScaNN runs on 16 vCPU / 128 GB vs requiring "extra-large" for pgvector
- **Memory efficiency:** 4x smaller footprint
- **Small datasets:** 4x better latency even for small workloads

**When to Use Cloud SQL:**
- Already using PostgreSQL
- Need transactional data + vectors in same DB
- Moderate scale (<10M vectors)
- Want simplicity over performance

**When to Use AlloyDB:**
- Need best-in-class performance
- Large datasets (10M+ vectors)
- Willing to pay premium for managed service
- Want ScaNN's superior performance
- High availability requirements

**Comparison:**

| Feature | Cloud SQL + pgvector | AlloyDB + ScaNN |
|---------|---------------------|-----------------|
| Performance | Good | Excellent (10x better) |
| Cost (list price) | Lower baseline | 40-50% higher |
| Cost (with CUD) | N/A | Competitive |
| Memory efficiency | Standard | 4x better |
| Large dataset handling | Struggles >50M | Excels at 1B+ |
| HA setup cost | 2x | 2x |

---

## 4. Recommendations by Scale

### Small Scale: 500 Libraries (500K-1M vectors)

**Estimated Vector Count:** 500 libraries × 500 pages × 2 chunks = **500,000 vectors**
**Storage Required:** ~8 GB (vectors + metadata)
**Memory Required:** ~8-10 GB

#### Option 1: Qdrant on GKE (Recommended for Cost)
```yaml
Configuration:
  Instance: n2-standard-2 (2 vCPU, 8 GB RAM)
  Storage: 100 GB SSD
  Nodes: 1 (no HA initially)
  Quantization: Scalar

Monthly Cost: $110-150
Setup Time: 20-30 hours
Operational: 5-10 hours/month

Pros:
  - Lowest monthly cost
  - Good performance
  - Full control
  - Can scale up easily

Cons:
  - Requires Kubernetes expertise
  - No HA in this configuration
  - Initial setup time
```

#### Option 2: Vertex AI Vector Search (Recommended for Simplicity)
```yaml
Configuration:
  Shard size: SMALL (e2-standard-2)
  Shards: 1
  Replicas: 2 (for HA)

Monthly Cost: $200-300
Setup Time: 4-8 hours
Operational: 1-2 hours/month

Pros:
  - Minimal ops overhead
  - Automatic HA
  - Google-managed
  - Good integration

Cons:
  - Higher cost
  - Vendor lock-in
  - Less flexibility
```

#### Option 3: AlloyDB with ScaNN (Recommended for All-in-One)
```yaml
Configuration:
  Instance: 4 vCPU, 32 GB RAM
  Storage: 100 GB
  HA: No (single instance)

Monthly Cost: $410 (list) / $197 (with 3-year CUD)
Setup Time: 8-12 hours
Operational: 2-4 hours/month

Pros:
  - Best performance
  - Combines transactional + vector data
  - ScaNN algorithm superiority
  - Easy to manage

Cons:
  - Highest base cost
  - Overkill for vector-only workloads
```

#### Option 4: Pinecone (Recommended for Speed to Market)
```yaml
Configuration:
  Plan: Standard
  Storage: ~8 GB

Monthly Cost: $50-100
Setup Time: 2-4 hours
Operational: 0 hours/month

Pros:
  - Fastest to deploy
  - Zero ops
  - Great DX
  - Elastic scaling

Cons:
  - Moderate cost
  - External service
  - Less control
```

**Winner by Priority:**
- **Cost:** Qdrant on GKE ($110-150/mo)
- **Simplicity:** Pinecone ($50-100/mo)
- **Performance:** AlloyDB w/ ScaNN ($197-410/mo)
- **Balance:** Vertex AI ($200-300/mo)

---

### Medium Scale: 5,000 Libraries (5M-10M vectors)

**Estimated Vector Count:** 5,000 libraries × 500 pages × 2 chunks = **5,000,000 vectors**
**Storage Required:** ~80 GB (vectors + metadata)
**Memory Required:** ~80-90 GB

#### Option 1: Vertex AI Vector Search (Recommended)
```yaml
Configuration:
  Shard size: MEDIUM (e2-standard-16)
  Shards: 1-2
  Replicas: 2

Monthly Cost: $1,200-1,600
  - Serving: 2 shards × 2 replicas × $547/mo = $2,188/mo
  - Optimized: 1 shard × 2 replicas = $1,095/mo

Setup Time: 6-10 hours
Operational: 2-4 hours/month

Pros:
  - Excellent performance at this scale
  - Managed service
  - Automatic scaling
  - Integrated monitoring

Cons:
  - Higher cost than self-hosted
  - Vendor lock-in

Why it wins:
  - Sweet spot for Vertex AI
  - Cost-competitive with self-hosted + ops time
  - Much less operational burden
```

#### Option 2: Qdrant on GKE (Cost-Conscious Alternative)
```yaml
Configuration:
  Nodes: 3 (StatefulSet, HA)
  Instance: n2-highmem-4 (4 vCPU, 32 GB RAM)
  Storage: 500 GB SSD per node
  Quantization: Scalar
  Replication: 2x

Monthly Cost: $1,474
  - Compute: $1,146
  - Storage: $255
  - GKE: $73

With 1-year CUD: $1,199

Setup Time: 40-50 hours
Operational: 10-15 hours/month

Pros:
  - More control
  - Can optimize further
  - Open source

Cons:
  - Significant ops burden
  - Team needs K8s expertise
```

#### Option 3: AlloyDB with ScaNN (Best Performance)
```yaml
Configuration:
  Instance: 8 vCPU, 64 GB RAM
  Storage: 500 GB
  HA: Yes (2x cost)

Monthly Cost: $1,740 (with HA)
With 3-year CUD: $835

Setup Time: 10-15 hours
Operational: 3-5 hours/month

Pros:
  - Superior query performance
  - ScaNN algorithm advantage
  - Managed service
  - Can combine with transactional data

Cons:
  - Higher cost at list price
  - Requires CUD for competitiveness
```

#### Option 4: Pinecone (Not Recommended at This Scale)
```yaml
Monthly Cost: $500-800
Reason to avoid: Costs increasing without benefit

Better alternatives exist at this scale for both cost and control
```

**Winner by Priority:**
- **Simplicity + Performance:** Vertex AI ($1,200-1,600/mo)
- **Best Performance:** AlloyDB + CUD ($835/mo)
- **Cost + Control:** Qdrant + CUD ($1,199/mo)

**Recommended:** **Vertex AI Vector Search** - Best balance of performance, cost, and operational simplicity at this scale.

---

### Large Scale: 33,000 Libraries (50M-100M vectors)

**Estimated Vector Count:** 33,000 libraries × 500 pages × 2 chunks = **33,000,000 vectors**
But with chunking variability, plan for **50-100M vectors**

**Storage Required:** ~600-1,000 GB (vectors + metadata)
**Memory Required:** ~600-900 GB (or ~150-225 GB with quantization)

#### Option 1: Qdrant on GKE with Quantization (Recommended for Cost)
```yaml
Configuration:
  Nodes: 6-8 (distributed sharding)
  Instance: n2-highmem-8 (8 vCPU, 64 GB RAM)
  Storage: 2 TB SSD per node
  Quantization: Scalar (4x reduction)
  Replication: 2x
  Sharding: Enabled across nodes

Monthly Cost: $4,423
  - Compute: $2,292
  - Storage: $2,040
  - GKE: $73
  - LB: $18

With 1-year CUD (25%): $3,390/mo
With 3-year CUD (52%): $2,283/mo

Setup Time: 60-80 hours
Operational: 15-25 hours/month

Pros:
  - Most cost-effective at scale
  - Maximum control and flexibility
  - Excellent performance with tuning
  - No vendor lock-in

Cons:
  - Highest operational complexity
  - Requires expert Kubernetes team
  - Significant initial investment
```

#### Option 2: Vertex AI Vector Search (Recommended for Managed Service)
```yaml
Configuration:
  Shard size: MEDIUM (e2-standard-16)
  Shards: 4-5 (based on data size)
  Replicas: 2 per shard

Monthly Cost: $3,500-5,000
  - Serving: 5 shards × 2 replicas × $547 = $5,470/mo
  - Optimized: 4 shards × 2 replicas × $547 = $4,376/mo

Setup Time: 10-15 hours
Operational: 3-6 hours/month

Pros:
  - Fully managed
  - Proven at billion+ scale
  - Automatic scaling
  - Google SLA backing

Cons:
  - Higher cost than self-hosted
  - Less control
  - Vendor lock-in

Why consider:
  - If ops team is small
  - If reliability > cost
  - If integrated GCP ecosystem
```

#### Option 3: AlloyDB with ScaNN (Best Performance)
```yaml
Configuration:
  Instance: 16 vCPU, 128 GB RAM
  Storage: 2 TB
  HA: Yes
  Read replicas: 2 (for query scaling)

Monthly Cost: $3,944 (with HA + 2 read replicas)
With 3-year CUD: $1,892/mo

Setup Time: 15-20 hours
Operational: 5-8 hours/month

Pros:
  - Best query performance (10x vs pgvector)
  - Superior memory efficiency
  - Handles 1B+ vectors
  - Managed service

Cons:
  - Higher baseline cost
  - PostgreSQL scalability limits
  - Need to manage sharding manually >100M vectors
```

#### Option 4: Hybrid Approach (Recommended for Large Enterprises)
```yaml
Configuration:
  Primary: Vertex AI Vector Search
    - Production queries
    - 50M most-accessed vectors
    - Cost: ~$4,000/mo

  Archive: Qdrant on GKE
    - Older/less-accessed documentation
    - 50M archived vectors
    - Cost: ~$2,000/mo

  Total: ~$6,000/mo

Pros:
  - Best of both worlds
  - Cost optimization
  - Flexibility
  - Tiered performance

Cons:
  - Complexity of managing two systems
  - Data synchronization overhead
```

**Winner by Priority:**
- **Lowest Cost:** Qdrant + 3yr CUD ($2,283/mo)
- **Best Performance:** AlloyDB + 3yr CUD ($1,892/mo)
- **Least Ops:** Vertex AI ($3,500-5,000/mo)
- **Best Overall:** Qdrant + 1yr CUD ($3,390/mo)

**Recommended:** **Qdrant on GKE with 1-year CUD** - Offers the best balance of cost ($3,390/mo), performance, and flexibility. Worth the operational investment at this scale.

**Alternative:** If team lacks Kubernetes expertise or reliability is paramount, choose **Vertex AI Vector Search** despite 20-50% higher cost.

---

## 5. Cost Comparison Summary

### Total Cost of Ownership (TCO) - 3 Year Analysis

Assuming DevOps engineer costs $150K/year ($75/hour), operational hours valued accordingly:

| Solution | Small (1M) | Medium (10M) | Large (100M) |
|----------|-----------|--------------|--------------|
| **Vertex AI Vector Search** |
| Monthly Cost | $250 | $1,400 | $4,000 |
| Ops Hours/mo | 2 | 3 | 5 |
| Ops Cost/mo | $150 | $225 | $375 |
| **Total/mo** | **$400** | **$1,625** | **$4,375** |
| 3-year TCO | $14,400 | $58,500 | $157,500 |
| | | | |
| **Qdrant on GKE** |
| Monthly Cost | $112 | $1,199 (CUD) | $2,283 (CUD) |
| Ops Hours/mo | 8 | 15 | 25 |
| Ops Cost/mo | $600 | $1,125 | $1,875 |
| **Total/mo** | **$712** | **$2,324** | **$4,158** |
| 3-year TCO | $25,632 | $83,664 | $149,688 |
| | | | |
| **AlloyDB + ScaNN** |
| Monthly Cost | $197 (CUD) | $835 (CUD) | $1,892 (CUD) |
| Ops Hours/mo | 3 | 4 | 6 |
| Ops Cost/mo | $225 | $300 | $450 |
| **Total/mo** | **$422** | **$1,135** | **$2,342** |
| 3-year TCO | $15,192 | $40,860 | $84,312 |
| | | | |
| **Pinecone** |
| Monthly Cost | $75 | $500 | $4,000 |
| Ops Hours/mo | 0 | 0 | 0 |
| Ops Cost/mo | $0 | $0 | $0 |
| **Total/mo** | **$75** | **$500** | **$4,000** |
| 3-year TCO | $2,700 | $18,000 | $144,000 |

### Winner by Scale (3-Year TCO):

- **Small (1M vectors):** Pinecone ($2,700) - Zero ops wins
- **Medium (10M vectors):** AlloyDB ($40,860) - Best performance + reasonable cost
- **Large (100M vectors):** AlloyDB ($84,312) - ScaNN algorithm + managed service advantage

**Key Insight:** When factoring in operational costs, managed services (AlloyDB, Vertex AI) become more attractive, especially for teams with limited DevOps resources.

---

## 6. Decision Matrix

### Choose Vertex AI Vector Search if:
- Team size < 5 engineers
- Limited Kubernetes/DevOps expertise
- Need rapid deployment (days not weeks)
- Reliability and SLA critical
- Willing to pay for convenience
- Medium scale (5M-50M vectors)

### Choose Qdrant on GKE if:
- Have strong DevOps/Kubernetes team
- Cost optimization critical
- Need maximum flexibility
- Large scale (50M+ vectors) with cost constraints
- Want open-source solution
- Can commit to 1-3 year CUD

### Choose AlloyDB with ScaNN if:
- Performance is top priority
- Already using PostgreSQL
- Need transactional + vector data together
- Medium to large scale (10M-100M vectors)
- Willing to commit to 3-year CUD
- Want managed service with best performance

### Choose Pinecone if:
- Small scale (<5M vectors)
- Startup/MVP stage
- Zero ops tolerance
- Fast time to market critical
- Budget for premium service
- Don't need data in GCP

### Choose Cloud SQL + pgvector if:
- Already heavily using Cloud SQL
- Small to medium scale (<10M vectors)
- Simple use case
- Budget constraints (no CUD)
- Don't need maximum performance

---

## 7. Migration Path Recommendation

### Phase 1: MVP (0-500 libraries)
**Start with:** Pinecone or Vertex AI
**Duration:** 3-6 months
**Cost:** $75-250/month
**Why:** Speed to market, validate product-market fit

### Phase 2: Growth (500-2,000 libraries)
**Migrate to:** Vertex AI Vector Search
**Duration:** 6-12 months
**Cost:** $400-800/month
**Why:** Staying in GCP, managed service, scales easily

### Phase 3: Scale (2,000-10,000 libraries)
**Decision Point:** Evaluate TCO
**Options:**
- **Option A:** Stay on Vertex AI (~$1,600/mo)
- **Option B:** Migrate to AlloyDB + ScaNN (~$1,135/mo with CUD)

**Recommendation:** AlloyDB if have PostgreSQL expertise, else Vertex AI

### Phase 4: Enterprise (10,000+ libraries)
**Migrate to:** Qdrant on GKE with 3-year CUD
**Cost:** $2,283-4,158/month
**Why:** Cost optimization at scale, maximum control
**Investment:** 80-100 hours setup + hire DevOps engineer

**Alternative:** Stay on AlloyDB if performance > cost ($2,342/mo with ops)

---

## 8. Storage & Networking Costs (Often Forgotten)

### Persistent Disk (all solutions except Pinecone)
- **SSD:** $0.17 per GB/month (us-central1)
- **Balanced SSD:** $0.10 per GB/month (good compromise)
- **Snapshots:** $0.026 per GB/month

### Network Egress
- **Within GCP region:** Free
- **Cross-region (US):** $0.01 per GB
- **To internet:** $0.12 per GB (first 1 TB)

**Example:** 100M vectors, 1000 queries/second, 10KB response each:
- Daily egress: 1000 QPS × 10KB × 86,400 sec = 864 GB/day
- Monthly: ~26 TB × $0.12 = **$3,120/month** (if external)
- **Solution:** Keep clients in GCP region (free egress)

### Backup Costs
- **Qdrant on GKE:** Snapshot 2TB × $0.026 = $52/month
- **Vertex AI:** Included in service
- **AlloyDB:** 7 days free, then $0.10/GB/month
- **Cloud SQL:** $0.08/GB/month

---

## 9. Additional Considerations

### Disaster Recovery
- **Vertex AI:** Multi-region replication available
- **Qdrant on GKE:** Must implement (use Velero)
- **AlloyDB:** Built-in continuous backup, cross-region replicas
- **Pinecone:** Automatic, included

### Compliance & Security
- **Data Residency:**
  - Pinecone: Data in their cloud (may be issue)
  - Others: Your GCP account
- **Encryption at rest:** All support
- **Encryption in transit:** All support
- **VPC peering:** Vertex AI, Qdrant, AlloyDB (not Pinecone)

### Team Expertise Required

| Solution | Kubernetes | PostgreSQL | Vector DB | GCP |
|----------|-----------|------------|-----------|-----|
| Vertex AI | ★☆☆ | ☆☆☆ | ★★☆ | ★★★ |
| Qdrant on GKE | ★★★ | ☆☆☆ | ★★☆ | ★★☆ |
| AlloyDB | ☆☆☆ | ★★★ | ★☆☆ | ★★☆ |
| Pinecone | ☆☆☆ | ☆☆☆ | ★☆☆ | ☆☆☆ |

---

## 10. Final Recommendations

### For Most Teams (Balanced Approach):

1. **Start:** Pinecone or Vertex AI (0-5M vectors)
2. **Grow:** Vertex AI or AlloyDB (5M-30M vectors)
3. **Scale:** AlloyDB with 3-year CUD (30M-100M vectors)
4. **Massive:** Qdrant on GKE or Vertex AI (100M+ vectors)

### For Cost-Conscious Startups:

1. **MVP:** Pinecone Free tier or Vertex AI
2. **Growth:** Qdrant on single GCE instance (not GKE)
3. **Scale:** Qdrant on GKE with spot instances + CUD

### For Enterprise (Performance Priority):

1. **All Scales:** AlloyDB with ScaNN + 3-year CUD
2. **Why:** Best performance, managed service, predictable costs, proven at scale

### For Maximum Control & Cost Optimization:

1. **All Scales:** Qdrant on GKE with CUD
2. **Requirement:** Strong DevOps team
3. **Benefit:** 40-60% cost savings at scale

---

## Conclusion

**No single "best" solution** - it depends on:
- Scale (vector count)
- Team expertise
- Budget
- Operational tolerance
- Performance requirements

**General Rule of Thumb:**
- **<1M vectors:** Pinecone (simplicity) or Vertex AI (GCP-native)
- **1M-10M vectors:** Vertex AI or AlloyDB
- **10M-50M vectors:** AlloyDB with CUD (best TCO)
- **50M+ vectors:** Qdrant on GKE with CUD (best cost) or AlloyDB (best performance)

**The Winner for Documentation Search at Scale:** **AlloyDB with ScaNN + 3-year CUD** offers the best combination of performance, manageability, and cost-effectiveness across all scales when you factor in operational overhead.

**Runner-up:** Vertex AI Vector Search for teams that prioritize simplicity and are willing to pay 20-30% more for a fully managed solution.

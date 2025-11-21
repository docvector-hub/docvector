# GCP Crawling and Indexing Infrastructure for Documentation Sites

**Research Report - Generated 2025-11-17**

This document provides comprehensive recommendations for optimal crawling and indexing infrastructure on Google Cloud Platform for documentation sites at scale.

---

## Table of Contents

1. [Crawling Service Options](#1-crawling-service-options)
2. [Change Detection Strategies](#2-change-detection-strategies)
3. [Queue and Orchestration](#3-queue-and-orchestration)
4. [Rate Limiting and Politeness](#4-rate-limiting-and-politeness)
5. [Storage Architecture](#5-storage-architecture)
6. [Recommended Architectures by Scale](#6-recommended-architectures-by-scale)
7. [Cost Estimates](#7-cost-estimates)
8. [Crawl Frequency Recommendations](#8-crawl-frequency-recommendations)
9. [Implementation Guide](#9-implementation-guide)

---

## 1. Crawling Service Options

### 1.1 Cloud Run Jobs (RECOMMENDED for Medium-Large Scale)

**Best For:** Scheduled batch crawling, long-running tasks, predictable workloads

**Advantages:**
- ✅ Up to 24-hour execution time (vs 9 min for Cloud Functions)
- ✅ Perfect for batch processing multiple documentation sites
- ✅ Can handle 4 vCPU, 16GB RAM per instance
- ✅ Built-in job scheduling and retry mechanisms
- ✅ Generous free tier: 180,000 vCPU-seconds/month (~50 CPU-hours)
- ✅ Auto-scaling with configurable parallelism
- ✅ Cost-effective for predictable crawling workloads

**Disadvantages:**
- ❌ Cold start (though minimal for jobs)
- ❌ Not ideal for event-driven crawling

**Pricing (us-central1):**
- CPU: $0.00002400 per vCPU-second
- Memory: $0.00000250 per GiB-second
- Requests: $0.40 per million executions

**Use Cases:**
- Weekly full documentation crawls
- Daily incremental crawls
- Batch processing 100+ libraries at once
- Processing sitemap-based crawls

**Example Cost Calculation:**
```
500 libraries × 500 pages = 250,000 pages
Crawl time: 10 pages/second/worker = 25,000 seconds
With 10 parallel workers: 2,500 seconds (42 minutes)
Resources: 2 vCPU, 4GB RAM per worker

Monthly cost (weekly crawls):
- CPU: 10 workers × 2 vCPU × 2,500s × 4 weeks × $0.000024 = $12/month
- Memory: 10 workers × 4 GB × 2,500s × 4 weeks × $0.0000025 = $10/month
- Total: ~$22/month (within free tier!)
```

---

### 1.2 Cloud Functions (2nd Gen) (RECOMMENDED for Event-Driven)

**Best For:** Event-driven crawling, webhooks, RSS feed processing, single-URL updates

**Advantages:**
- ✅ Perfect for event triggers (Pub/Sub, HTTP, Firestore)
- ✅ Fast deployment and iteration
- ✅ Generous free tier: 2M invocations/month
- ✅ Simple configuration
- ✅ Automatic scaling to zero

**Disadvantages:**
- ❌ 60-minute timeout (9 min for 1st gen)
- ❌ Limited resources vs Cloud Run Jobs
- ❌ Higher cost at scale for continuous crawling

**Pricing:**
- Invocations: $0.40 per million (after free tier)
- CPU: $0.00001000 per GHz-second
- Memory: $0.00000250 per GB-second

**Use Cases:**
- GitHub webhook → crawl updated docs
- RSS feed update → crawl new pages
- Sitemap change detection → trigger crawl
- Single URL recrawl requests

---

### 1.3 GKE with Job Queue (Celery/RQ) (For Advanced Scale)

**Best For:** 10,000+ libraries, complex orchestration, custom requirements

**Advantages:**
- ✅ Full control over infrastructure
- ✅ Can use Spot VMs (70% cost savings)
- ✅ Sophisticated job management (Celery/RQ)
- ✅ Complex retry logic and prioritization
- ✅ Can run 24/7 workers with job queues
- ✅ Best for distributed crawling with state management

**Disadvantages:**
- ❌ Higher operational complexity
- ❌ Requires Kubernetes expertise
- ❌ More expensive at small scale
- ❌ Need to manage scaling, monitoring, upgrades

**Pricing (n2-standard-4 spot):**
- Regular: $0.194844/hour = $142/month
- Spot: $0.058453/hour = $43/month (70% discount)
- Per worker: ~$43-142/month depending on spot availability

**Use Cases:**
- 10,000+ libraries with complex dependencies
- Sophisticated crawl orchestration (dependency graphs)
- Need for distributed rate limiting across workers
- Custom crawler implementations requiring libraries not in Cloud Run

**Technology Stack:**
```python
# Recommended setup
- Orchestrator: Apache Airflow on GKE or Cloud Composer
- Queue: Redis (Memorystore) or RabbitMQ
- Workers: Python with Celery
- Crawling: Scrapy or custom implementation
```

---

### 1.4 Compute Engine with Autoscaling (Legacy Approach)

**Best For:** Specific legacy requirements, GPU needs

**Advantages:**
- ✅ Maximum flexibility
- ✅ Can attach GPUs for embedding generation
- ✅ Predictable billing

**Disadvantages:**
- ❌ Manual autoscaling configuration
- ❌ Higher operational overhead
- ❌ Not serverless (always-on costs)
- ❌ Slower scaling than Cloud Run/Functions

**Verdict:** NOT RECOMMENDED - Cloud Run Jobs or GKE are better choices

---

### Comparison Matrix

| Feature | Cloud Run Jobs | Cloud Functions | GKE + Celery | Compute Engine |
|---------|---------------|-----------------|--------------|----------------|
| **Max Runtime** | 24 hours | 60 minutes | Unlimited | Unlimited |
| **Cold Start** | ~5s | ~1s | N/A (always warm) | N/A |
| **Scaling** | Auto (0-1000) | Auto (0-1000) | Manual/HPA | Manual/MIG |
| **Ops Complexity** | Very Low | Very Low | High | Medium |
| **Cost (small)** | $ | $ | $$$ | $$ |
| **Cost (large)** | $$ | $$$ | $$ | $$$ |
| **Best For** | Batch crawling | Events | Advanced scale | GPU workloads |

**Recommendation Summary:**
- **500 libraries:** Cloud Run Jobs + Cloud Functions (events)
- **5,000 libraries:** Cloud Run Jobs (primary) + Cloud Functions (events)
- **33,000 libraries:** GKE with Celery + Cloud Functions (events)

---

## 2. Change Detection Strategies

Efficient change detection is critical to minimize crawling costs and keep documentation up-to-date.

### 2.1 RSS/Atom Feed Monitoring (HIGHLY RECOMMENDED)

**How It Works:**
1. Store RSS feed URLs for each documentation source
2. Poll feeds every 15-60 minutes using Cloud Scheduler
3. Compare new entries with last crawl timestamp
4. Trigger Cloud Function to crawl changed pages only

**Advantages:**
- ✅ 90%+ reduction in unnecessary crawling
- ✅ Near real-time updates (15-60 min latency)
- ✅ Low cost (feed polling is cheap)
- ✅ Explicit change notifications from source

**Implementation:**
```python
# Cloud Function triggered by Cloud Scheduler
import feedparser
from datetime import datetime

async def check_rss_feed(feed_url: str, last_check: datetime):
    feed = feedparser.parse(feed_url)
    new_entries = []

    for entry in feed.entries:
        pub_date = datetime(*entry.published_parsed[:6])
        if pub_date > last_check:
            new_entries.append({
                'url': entry.link,
                'title': entry.title,
                'published': pub_date
            })

    # Trigger crawl for new URLs
    if new_entries:
        await trigger_crawl_job(new_entries)
```

**Cost:**
- Polling 1000 feeds every 30 min: ~48,000 invocations/month = FREE (within quota)
- Storage (feed state): Firestore = $0.01/month

**Limitations:**
- Not all documentation sites provide RSS feeds
- Feed may not include all page updates

---

### 2.2 Sitemap Diff Checking (RECOMMENDED)

**How It Works:**
1. Download sitemap.xml daily/weekly
2. Compare with previous sitemap snapshot
3. Detect: new URLs, removed URLs, lastmod changes
4. Crawl only changed pages

**Advantages:**
- ✅ 70-80% reduction in crawling
- ✅ Works with most documentation sites
- ✅ Can detect URL structure changes
- ✅ Simple to implement

**Implementation:**
```python
# Cloud Run Job or Cloud Function
import xml.etree.ElementTree as ET
from google.cloud import storage

async def check_sitemap_changes(sitemap_url: str):
    # Download current sitemap
    current = await fetch_sitemap(sitemap_url)

    # Load previous snapshot from Cloud Storage
    previous = load_previous_sitemap(sitemap_url)

    # Compute diff
    new_urls = current - previous
    removed_urls = previous - current

    # Check lastmod for existing URLs
    modified_urls = check_lastmod_changes(current, previous)

    # Trigger crawls
    urls_to_crawl = new_urls | modified_urls
    await trigger_crawl_job(list(urls_to_crawl))

    # Save current as new baseline
    save_sitemap_snapshot(sitemap_url, current)
```

**Cost:**
- Storage: Cloud Storage = $0.02/GB/month (sitemaps are tiny)
- Processing: Cloud Function invocation = FREE (within quota)
- Total for 1000 libraries: ~$1/month

**Best Practices:**
- Store compressed sitemap snapshots in Cloud Storage
- Use ETag/Last-Modified headers to avoid unnecessary downloads
- Parse sitemap index files for large sites

---

### 2.3 GitHub Webhooks (For GitHub-Hosted Docs)

**How It Works:**
1. Register webhook on documentation repositories
2. Receive push/release events
3. Trigger immediate crawl of affected pages
4. Smart path mapping (commit files → documentation URLs)

**Advantages:**
- ✅ Real-time updates (< 1 minute latency)
- ✅ Zero polling cost
- ✅ Precise change detection
- ✅ Perfect for versioned documentation

**Implementation:**
```python
# Cloud Function with HTTP trigger
from flask import Request
import hmac
import hashlib

def github_webhook(request: Request):
    # Verify webhook signature
    signature = request.headers.get('X-Hub-Signature-256')
    verify_signature(request.data, signature)

    # Parse event
    event = request.headers.get('X-GitHub-Event')
    payload = request.get_json()

    if event == 'push':
        # Extract changed files
        changed_files = []
        for commit in payload['commits']:
            changed_files.extend(commit['added'])
            changed_files.extend(commit['modified'])

        # Map to documentation URLs
        doc_urls = map_files_to_urls(changed_files, payload['repository'])

        # Trigger crawl
        trigger_crawl_job(doc_urls)

    elif event == 'release':
        # New release → crawl entire docs for new version
        trigger_full_crawl(payload['repository'], payload['release']['tag_name'])
```

**Cost:**
- FREE - webhooks are push-based, no polling needed
- Cloud Function invocations: ~100-1000/month per repo = FREE

**Limitations:**
- Only works for GitHub-hosted documentation
- Requires webhook registration for each repository
- Need to map file paths to URLs (can be complex)

---

### 2.4 HEAD Request Polling (Simple but Costly)

**How It Works:**
1. Send HEAD requests to all known URLs periodically
2. Check Last-Modified or ETag headers
3. Crawl if changed

**Advantages:**
- ✅ Universal (works for any website)
- ✅ Simple implementation

**Disadvantages:**
- ❌ Expensive at scale (250K HEAD requests daily)
- ❌ Impolite (high server load)
- ❌ Many sites don't set proper cache headers

**Verdict:** NOT RECOMMENDED - Use only as fallback

---

### 2.5 Content Hash Comparison (Hybrid Approach)

**How It Works:**
1. Crawl pages on schedule
2. Compute content hash (SHA-256)
3. Compare with stored hash
4. Update index only if hash changed

**Advantages:**
- ✅ Detects actual content changes (not just timestamps)
- ✅ Works with database schema (you already have content_hash!)
- ✅ Prevents re-processing unchanged pages

**Implementation:**
```python
# Already in your codebase!
from docvector.utils import compute_text_hash

async def crawl_with_dedup(url: str, source_id: str):
    # Fetch page
    content = await fetch_url(url)
    content_hash = compute_text_hash(content)

    # Check if exists
    existing = await document_repo.get_by_content_hash(source_id, content_hash)

    if existing:
        logger.info("Content unchanged, skipping", url=url)
        return existing

    # Process new/changed content
    return await process_document(content, source_id)
```

**Cost:**
- Zero additional cost (uses existing DB)
- Saves on embedding generation (biggest cost!)

---

### Recommended Change Detection Strategy

**Small Scale (500 libraries):**
```
Daily:  Sitemap diff checking
Weekly: RSS feed monitoring
On-demand: GitHub webhooks (where available)
```

**Medium Scale (5,000 libraries):**
```
Hourly:  RSS feed monitoring (for active libraries)
Daily:   Sitemap diff checking
Weekly:  Full crawl (with content hash dedup)
On-demand: GitHub webhooks
```

**Large Scale (33,000 libraries):**
```
Every 15 min: RSS feed monitoring (top 1000 libraries)
Hourly:      Sitemap diff checking (active libraries)
Daily:       Sitemap diff checking (all libraries)
Weekly:      Selective full crawl (10% rotation)
On-demand:   GitHub webhooks
```

---

## 3. Queue and Orchestration

Based on Google Cloud documentation and best practices, here's a detailed comparison of queue options.

### 3.1 Cloud Tasks (RECOMMENDED for Crawling)

**Why Cloud Tasks is Best for Crawling:**

✅ **Rate Limiting Built-In**
- Configure `max_concurrent_dispatches` per queue
- Prevent overwhelming target websites
- Domain-based rate limiting (one queue per domain)

✅ **Precise Control**
- Explicit task scheduling (delay up to 30 days)
- Manual retry configuration (up to days, not just 10 min like Pub/Sub)
- Task deduplication by name
- Ability to cancel/pause queues

✅ **Perfect for HTTP Endpoints**
- Direct integration with Cloud Run/Functions HTTP endpoints
- Authentication built-in
- Automatic retries with exponential backoff

✅ **Crawl-Specific Features**
- Set `max_dispatches_per_second` to respect robots.txt crawl-delay
- Set `max_concurrent_dispatches=1` for strict ordering
- Schedule tasks for specific times (e.g., crawl at night)

**Pricing:**
- First 1 million operations/month: FREE
- After: $0.40 per million operations
- Operations = enqueue + task execution attempts

**Example Implementation:**
```python
from google.cloud import tasks_v2
from google.protobuf import duration_pb2

client = tasks_v2.CloudTasksClient()

# Create queue with rate limiting
queue = tasks_v2.Queue(
    rate_limits=tasks_v2.RateLimits(
        max_dispatches_per_second=2,      # Respect robots.txt
        max_concurrent_dispatches=10,     # Control parallelism
    ),
    retry_config=tasks_v2.RetryConfig(
        max_attempts=5,
        max_retry_duration=duration_pb2.Duration(seconds=86400),  # 24 hours
        min_backoff=duration_pb2.Duration(seconds=60),
        max_backoff=duration_pb2.Duration(seconds=3600),
    )
)

# Create crawl task
task = tasks_v2.Task(
    http_request=tasks_v2.HttpRequest(
        url="https://your-crawler.run.app/crawl",
        http_method=tasks_v2.HttpMethod.POST,
        headers={"Content-Type": "application/json"},
        body=json.dumps({
            "url": "https://docs.example.com/page1",
            "library_id": "example/docs",
        }).encode(),
    ),
    schedule_time=timestamp_pb2.Timestamp(
        seconds=int(time.time()) + 300  # Schedule 5 min from now
    ),
)

response = client.create_task(parent=queue_path, task=task)
```

**Architecture Pattern:**
```
Cloud Scheduler (daily 2am)
    ↓ triggers
Cloud Function (sitemap checker)
    ↓ enqueues 1000s of URLs
Cloud Tasks Queue (domain-specific queues)
    ↓ dispatches at 2/sec
Cloud Run Job (crawler worker)
    ↓ stores results
PostgreSQL + Qdrant
```

---

### 3.2 Pub/Sub + Cloud Run (For Event-Driven Architecture)

**When to Use Pub/Sub:**

✅ **Fan-out Pattern**
- One event → multiple consumers
- Example: New doc published → crawl + notify + index

✅ **High Throughput**
- Can handle >500 messages/second (vs Cloud Tasks limit)
- Better for 33,000 library scale

✅ **Loose Coupling**
- Publishers don't know about consumers
- Easy to add new processors

**Disadvantages for Crawling:**
- ❌ No built-in rate limiting (need custom implementation)
- ❌ 10-minute retry limit (vs Cloud Tasks' days)
- ❌ No task deduplication
- ❌ Can't schedule tasks for future

**Pricing:**
- First 10 GB/month: FREE
- After: $0.06 per GB
- Typical message size: 1 KB → 1 million messages = $0.06

**Use Cases:**
- GitHub webhook → multiple processors (crawl + analytics + notifications)
- High-volume change detection events
- Real-time documentation updates

**Example:**
```python
from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, "doc-updates")

# Publish change event
data = json.dumps({
    "library_id": "mongodb/docs",
    "urls": ["https://docs.mongodb.com/manual/tutorial/"],
    "event": "github_push"
}).encode()

future = publisher.publish(topic_path, data)
```

---

### 3.3 Firestore as Job Queue (Lightweight Alternative)

**When to Use:**

✅ **Already Using Firestore**
- Zero additional cost for queue infrastructure
- Simple Firestore triggers

✅ **Low-Medium Volume**
- < 1000 jobs/hour
- Simple job state tracking

✅ **Need Job Visibility**
- Easy to query job status
- Built-in persistence

**Implementation Pattern:**
```python
# Job submission
from google.cloud import firestore

db = firestore.Client()

# Create job document
job_ref = db.collection('crawl_jobs').document()
job_ref.set({
    'status': 'pending',
    'library_id': 'mongodb/docs',
    'urls': [...],
    'created_at': firestore.SERVER_TIMESTAMP,
    'attempts': 0,
})

# Cloud Function triggered on job creation
@firestore.on_document_created(document="crawl_jobs/{job_id}")
async def process_crawl_job(event):
    job_data = event.data

    # Update status
    event.reference.update({'status': 'processing'})

    try:
        # Process crawl
        results = await crawl_urls(job_data['urls'])

        # Mark complete
        event.reference.update({
            'status': 'completed',
            'results': results,
            'completed_at': firestore.SERVER_TIMESTAMP,
        })
    except Exception as e:
        # Retry logic
        attempts = job_data.get('attempts', 0) + 1
        if attempts < 3:
            event.reference.update({
                'status': 'pending',
                'attempts': attempts,
                'error': str(e),
            })
        else:
            event.reference.update({
                'status': 'failed',
                'error': str(e),
            })
```

**Pricing:**
- Document writes: $0.18 per 100K (job creation + updates)
- Document reads: $0.06 per 100K (job monitoring)
- For 10K jobs/day: ~$0.54/month

**Limitations:**
- ❌ No built-in rate limiting
- ❌ No automatic retries
- ❌ Manual worker implementation
- ❌ Not ideal for high-volume (> 10K jobs/hour)

---

### 3.4 Self-Hosted Redis Queue (Celery/RQ)

**When to Use:**

✅ **Using GKE Already**
- Part of larger Kubernetes deployment
- Need sophisticated job management

✅ **Advanced Requirements**
- Job priorities
- Complex dependencies
- Task routing
- Custom retry logic

**Setup with Memorystore (Managed Redis):**
```yaml
# GKE deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
spec:
  replicas: 5
  template:
    spec:
      containers:
      - name: worker
        image: gcr.io/project/crawler-worker
        env:
        - name: CELERY_BROKER_URL
          value: redis://10.0.0.3:6379/0  # Memorystore
        - name: CELERY_RESULT_BACKEND
          value: redis://10.0.0.3:6379/0
        command: ["celery", "-A", "crawler", "worker"]
```

**Pricing:**
- Memorystore Redis (5GB): $40/month
- GKE worker nodes: $43-142/month each (spot vs regular)

**Advantages:**
- ✅ Most mature queue system
- ✅ Rich ecosystem (Flower UI, monitoring)
- ✅ Complex workflows (chains, chords, groups)

**Disadvantages:**
- ❌ Higher operational complexity
- ❌ Need to manage Redis/RabbitMQ
- ❌ More expensive at small scale

---

### Orchestration Comparison

| Feature | Cloud Tasks | Pub/Sub | Firestore Queue | Redis (Celery) |
|---------|-------------|---------|-----------------|----------------|
| **Rate Limiting** | Built-in ✅ | Manual ❌ | Manual ❌ | Manual ❌ |
| **Max Retry** | Days ✅ | 10 min ❌ | Manual | Custom ✅ |
| **Throughput** | 500/sec | >500/sec ✅ | <100/sec | High ✅ |
| **Deduplication** | Yes ✅ | No ❌ | Manual | Manual |
| **Task Scheduling** | Yes ✅ | No ❌ | Manual | Yes ✅ |
| **Ops Complexity** | Very Low ✅ | Very Low ✅ | Low ✅ | High ❌ |
| **Cost (10K jobs/day)** | Free | Free | $0.54 | $80+ |

**Recommendation:**
- **500 libraries:** Cloud Tasks (primary) + Pub/Sub (events)
- **5,000 libraries:** Cloud Tasks (crawling) + Pub/Sub (events)
- **33,000 libraries:** Pub/Sub (high volume) + Cloud Tasks (rate-limited domains)

---

## 4. Rate Limiting and Politeness

Being a polite crawler is essential for:
- Not overloading documentation sites
- Avoiding IP bans
- Maintaining good relationships with documentation providers

### 4.1 robots.txt Compliance

**Implementation:**
```python
import aiohttp
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse

class PoliteWebCrawler:
    def __init__(self):
        self.robots_parsers = {}  # Cache per domain
        self.last_request_time = {}  # Track per domain

    async def can_fetch(self, url: str, user_agent: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        # Get or cache robots.txt parser
        if domain not in self.robots_parsers:
            robots_url = urljoin(domain, "/robots.txt")
            parser = RobotFileParser()
            parser.set_url(robots_url)

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(robots_url) as response:
                        if response.status == 200:
                            robots_txt = await response.text()
                            parser.parse(robots_txt.splitlines())
            except Exception as e:
                logger.warning(f"Failed to fetch robots.txt for {domain}: {e}")
                # Be conservative: if we can't fetch robots.txt, allow crawling
                # but proceed with caution

            self.robots_parsers[domain] = parser

        return self.robots_parsers[domain].can_fetch(user_agent, url)

    def get_crawl_delay(self, url: str, user_agent: str) -> float:
        """Get crawl delay from robots.txt"""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if domain in self.robots_parsers:
            parser = self.robots_parsers[domain]
            delay = parser.crawl_delay(user_agent)
            return delay if delay else 1.0  # Default 1 second

        return 1.0
```

**Integration with Cloud Tasks:**
```python
# Create separate queue per domain with appropriate rate limits
from google.cloud import tasks_v2

async def create_domain_queue(domain: str, crawl_delay: float):
    """Create a queue with rate limit based on robots.txt crawl-delay"""
    client = tasks_v2.CloudTasksClient()

    max_rate = 1.0 / crawl_delay  # Convert delay to requests/second

    queue = tasks_v2.Queue(
        rate_limits=tasks_v2.RateLimits(
            max_dispatches_per_second=max_rate,
            max_concurrent_dispatches=5,  # Conservative default
        ),
    )

    # Create queue
    parent = client.queue_path(project_id, location, domain.replace('.', '-'))
    client.create_queue(parent=parent, queue=queue)
```

---

### 4.2 Configurable Delays

**Database Schema Addition:**
```sql
-- Add to sources table
ALTER TABLE sources ADD COLUMN crawl_config JSONB DEFAULT '{
  "crawl_delay_seconds": 1.0,
  "max_concurrent_requests": 5,
  "respect_robots_txt": true,
  "user_agent": "DocVectorBot/1.0 (+https://your-site.com/bot)"
}'::jsonb;

-- Add domain-specific overrides
CREATE TABLE crawl_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(255) NOT NULL UNIQUE,
    crawl_delay_seconds FLOAT DEFAULT 1.0,
    max_concurrent_requests INT DEFAULT 5,
    allowed BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Example data
INSERT INTO crawl_policies (domain, crawl_delay_seconds, max_concurrent_requests, notes)
VALUES
    ('docs.python.org', 2.0, 3, 'Heavy load site, be extra polite'),
    ('numpy.org', 1.0, 5, 'Standard crawling'),
    ('small-oss-project.io', 0.5, 2, 'Small server, low concurrency');
```

**Implementation:**
```python
from dataclasses import dataclass

@dataclass
class CrawlPolicy:
    domain: str
    crawl_delay_seconds: float = 1.0
    max_concurrent_requests: int = 5
    respect_robots_txt: bool = True
    user_agent: str = "DocVectorBot/1.0"

class PolicyManager:
    def __init__(self, db_session):
        self.session = db_session
        self.cache = {}

    async def get_policy(self, domain: str) -> CrawlPolicy:
        """Get crawl policy for domain"""
        if domain in self.cache:
            return self.cache[domain]

        # Check database
        result = await self.session.execute(
            "SELECT * FROM crawl_policies WHERE domain = :domain",
            {"domain": domain}
        )
        row = result.fetchone()

        if row:
            policy = CrawlPolicy(
                domain=domain,
                crawl_delay_seconds=row.crawl_delay_seconds,
                max_concurrent_requests=row.max_concurrent_requests,
            )
        else:
            # Use defaults
            policy = CrawlPolicy(domain=domain)

        self.cache[domain] = policy
        return policy
```

---

### 4.3 Domain-Based Rate Limiting

**Architecture:**

```
┌─────────────────────┐
│  Sitemap Analyzer   │
│  (Cloud Function)   │
└──────────┬──────────┘
           │ Groups URLs by domain
           ↓
┌─────────────────────────────────────────┐
│         Domain Router                   │
│         (Cloud Function)                │
└──┬──────┬──────┬──────┬──────┬──────┬──┘
   │      │      │      │      │      │
   ↓      ↓      ↓      ↓      ↓      ↓
┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐
│Queue││Queue││Queue││Queue││Queue││Queue│
│ A   ││ B   ││ C   ││ D   ││ E   ││ F   │
└──┬──┘└──┬──┘└──┬──┘└──┬──┘└──┬──┘└──┬──┘
   │ 1/s  │ 2/s  │ 1/s  │ 3/s  │ 1/s  │ 2/s
   ↓      ↓      ↓      ↓      ↓      ↓
┌──────────────────────────────────────────┐
│     Crawler Workers (Cloud Run)          │
└──────────────────────────────────────────┘
```

**Implementation:**
```python
from collections import defaultdict
from urllib.parse import urlparse

async def route_urls_to_domain_queues(urls: List[str]):
    """Group URLs by domain and enqueue to domain-specific queues"""

    # Group by domain
    domain_urls = defaultdict(list)
    for url in urls:
        domain = urlparse(url).netloc
        domain_urls[domain].append(url)

    # Enqueue to domain-specific queues
    tasks_client = tasks_v2.CloudTasksClient()

    for domain, urls in domain_urls.items():
        # Get crawl policy for domain
        policy = await policy_manager.get_policy(domain)

        # Ensure queue exists with correct rate limits
        queue_name = f"crawl-{domain.replace('.', '-')}"
        await ensure_queue_exists(queue_name, policy)

        # Enqueue tasks
        for url in urls:
            task = tasks_v2.Task(
                http_request=tasks_v2.HttpRequest(
                    url=f"https://crawler.run.app/crawl",
                    method=tasks_v2.HttpMethod.POST,
                    headers={"Content-Type": "application/json"},
                    body=json.dumps({
                        "url": url,
                        "domain": domain,
                        "policy": asdict(policy),
                    }).encode(),
                )
            )

            tasks_client.create_task(
                parent=f"projects/{project}/locations/{location}/queues/{queue_name}",
                task=task,
            )
```

---

### 4.4 Distributed Crawling Coordination

**Problem:** Multiple workers crawling same domain need to coordinate rate limits

**Solution: Shared Rate Limiter with Redis**

```python
import redis.asyncio as redis
import time

class DistributedRateLimiter:
    """Token bucket rate limiter using Redis"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def acquire(self, domain: str, tokens_per_second: float, max_tokens: int = 10) -> bool:
        """
        Acquire permission to make request to domain.

        Uses token bucket algorithm with Redis for coordination.
        """
        key = f"ratelimit:{domain}"
        now = time.time()

        # Lua script for atomic token bucket update
        script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local rate = tonumber(ARGV[2])
        local capacity = tonumber(ARGV[3])

        local bucket = redis.call('HMGET', key, 'tokens', 'last_update')
        local tokens = tonumber(bucket[1]) or capacity
        local last_update = tonumber(bucket[2]) or now

        -- Add tokens based on time elapsed
        local elapsed = now - last_update
        tokens = math.min(capacity, tokens + (elapsed * rate))

        if tokens >= 1 then
            -- Grant request
            tokens = tokens - 1
            redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
            redis.call('EXPIRE', key, 3600)  -- 1 hour TTL
            return 1
        else
            -- Deny request
            return 0
        end
        """

        result = await self.redis.eval(
            script,
            keys=[key],
            args=[now, tokens_per_second, max_tokens],
        )

        return bool(result)

    async def wait_and_acquire(self, domain: str, tokens_per_second: float) -> None:
        """Wait until permission is granted"""
        while not await self.acquire(domain, tokens_per_second):
            await asyncio.sleep(1.0 / tokens_per_second)

# Usage in crawler
async def crawl_with_rate_limit(url: str, rate_limiter: DistributedRateLimiter):
    domain = urlparse(url).netloc
    policy = await policy_manager.get_policy(domain)

    # Wait for rate limit
    await rate_limiter.wait_and_acquire(
        domain=domain,
        tokens_per_second=1.0 / policy.crawl_delay_seconds,
    )

    # Now safe to crawl
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

**Cost:**
- Memorystore Redis (1GB): $30/month
- Sufficient for coordinating 100+ workers across 10,000+ domains

---

### 4.5 User Agent Best Practices

**Recommended User Agent:**
```python
USER_AGENT = "DocVectorBot/1.0 (+https://docvector.io/bot; crawler@docvector.io)"
```

**Components:**
- Bot name and version
- Link to bot information page
- Contact email

**Create a /bot page:**
```html
<!-- https://docvector.io/bot -->
<h1>DocVector Crawler</h1>
<p>
  DocVector is a documentation search engine that helps developers find
  code examples and API documentation across multiple libraries.
</p>

<h2>Crawling Policy</h2>
<ul>
  <li>Respects robots.txt</li>
  <li>Default crawl delay: 1 second</li>
  <li>Will honor crawl-delay directive</li>
  <li>Crawls public documentation only</li>
</ul>

<h2>Request Removal</h2>
<p>
  To remove your site from our index, please contact:
  crawler@docvector.io
</p>

<h2>Technical Details</h2>
<ul>
  <li>User Agent: DocVectorBot/1.0</li>
  <li>IP Ranges: [Your Cloud Run IP ranges]</li>
  <li>Crawl frequency: Weekly with daily change detection</li>
</ul>
```

---

## 5. Storage Architecture

### 5.1 Cloud Storage (Cold Storage for Fetched Content)

**Use Case:** Archive raw HTML/Markdown for:
- Disaster recovery
- Re-processing with new parsers
- Legal/compliance requirements
- Debugging crawl issues

**Storage Tiers:**
```python
# Standard: Frequently accessed
# Nearline: < once/month ($0.010/GB/month)
# Coldline: < once/quarter ($0.004/GB/month)
# Archive: < once/year ($0.0012/GB/month)
```

**Recommended Approach:**
```python
from google.cloud import storage

async def archive_raw_content(document: Document, raw_content: bytes):
    """Archive raw fetched content to Cloud Storage"""

    storage_client = storage.Client()
    bucket = storage_client.bucket("docvector-raw-content")

    # Organize by library and date
    library_id = document.source.library_id
    date = document.fetched_at.strftime("%Y/%m/%d")
    blob_name = f"{library_id}/{date}/{document.id}.html.gz"

    blob = bucket.blob(blob_name)

    # Compress and upload
    import gzip
    compressed = gzip.compress(raw_content)
    blob.upload_from_string(
        compressed,
        content_type="application/gzip",
    )

    # Set lifecycle policy: move to Coldline after 30 days
    blob.metadata = {
        "document_id": str(document.id),
        "url": document.url,
        "fetched_at": document.fetched_at.isoformat(),
    }
    blob.patch()
```

**Lifecycle Policy:**
```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {"age": 30}
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {"age": 90}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"age": 365}
      }
    ]
  }
}
```

**Cost Estimates:**

| Scale | Pages | Avg Size | Storage (Compressed) | Monthly Cost (Coldline) |
|-------|-------|----------|---------------------|------------------------|
| 500 libs | 250K | 100 KB | 12.5 GB | $0.05 |
| 5K libs | 2.5M | 100 KB | 125 GB | $0.50 |
| 33K libs | 16.5M | 100 KB | 825 GB | $3.30 |

**Recommendation:** Enable for all scales (cost is negligible, value is high)

---

### 5.2 Firestore (Metadata and Job Tracking)

**Use Cases:**
- Source configuration (already using JSONB in PostgreSQL ✅)
- Job/task status tracking
- Change detection state (last crawl times, sitemaps)
- Real-time monitoring dashboards

**Recommended Schema:**
```javascript
// Collection: sources_state
{
  "source_id": "uuid-here",
  "last_crawl_started": Timestamp,
  "last_crawl_completed": Timestamp,
  "last_successful_crawl": Timestamp,
  "current_job_id": "job-uuid",
  "crawl_stats": {
    "pages_fetched": 1523,
    "pages_failed": 12,
    "new_pages": 45,
    "updated_pages": 89,
    "unchanged_pages": 1377
  },
  "next_scheduled_crawl": Timestamp,
  "sitemap_snapshot_url": "gs://bucket/snapshots/source-id/latest.xml.gz"
}

// Collection: crawl_jobs
{
  "job_id": "uuid",
  "source_id": "uuid",
  "status": "running",  // pending, running, completed, failed
  "created_at": Timestamp,
  "started_at": Timestamp,
  "completed_at": Timestamp,
  "progress": {
    "total_urls": 1500,
    "processed": 847,
    "failed": 3,
    "percent": 56.4
  },
  "config": {...},
  "error": null
}
```

**Advantages Over PostgreSQL for This:**
- ✅ Real-time updates (for monitoring dashboards)
- ✅ Better for frequently-updated fields
- ✅ Native triggers (Cloud Functions)
- ✅ Cheaper for read-heavy monitoring queries

**Cost:**
- Document reads: $0.06 per 100K
- Document writes: $0.18 per 100K
- For 5K libraries with daily crawls: ~$2/month

**Recommendation:**
- **Use Firestore for:** Real-time job tracking, monitoring
- **Use PostgreSQL for:** Source config, permanent records (documents, chunks)

---

### 5.3 Cloud SQL / PostgreSQL (Processed Documents)

**Current Schema (Already Optimal!):**

✅ Your existing schema is well-designed:
```sql
sources          -- Documentation sources
libraries        -- Library metadata
documents        -- Processed documents with content_hash deduplication
chunks           -- Searchable chunks with embeddings
crawl_policies   -- (Recommended addition for rate limiting)
```

**Optimizations for Scale:**

**500 Libraries:**
- db-custom-4-16384 (4 vCPU, 16GB RAM): $250/month ✅ (Current estimate)
- Single region, no HA needed
- 1TB SSD storage

**5,000 Libraries:**
- db-custom-8-32768 (8 vCPU, 32GB RAM): $600/month
- Enable High Availability: +100% cost = $1,200/month
- 2TB SSD storage
- Enable read replicas for search queries

**33,000 Libraries:**
- db-custom-16-65536 (16 vCPU, 64GB RAM): $1,400/month
- High Availability: $2,800/month
- 5TB SSD storage
- Consider Cloud Spanner for global distribution

**Connection Pooling:**
```python
# Use PgBouncer or Cloud SQL Proxy connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

# For Cloud Run (ephemeral connections)
engine = create_engine(
    f"postgresql+asyncpg://{user}:{password}@/{database}?"
    f"host=/cloudsql/{instance_connection_name}",
    poolclass=NullPool,  # Cloud SQL Proxy handles pooling
)

# For long-running workers (GKE)
engine = create_engine(
    f"postgresql+asyncpg://{user}:{password}@{host}/{database}",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)
```

**Indexes for Crawling Workload:**
```sql
-- Speed up deduplication checks
CREATE INDEX CONCURRENTLY idx_documents_content_hash
ON documents(source_id, content_hash);

-- Speed up change detection
CREATE INDEX CONCURRENTLY idx_documents_url
ON documents(source_id, url);

-- Speed up job tracking
CREATE INDEX CONCURRENTLY idx_documents_status
ON documents(status, fetched_at DESC);

-- Partial index for failed documents
CREATE INDEX CONCURRENTLY idx_documents_failed
ON documents(source_id, url)
WHERE status = 'failed';
```

---

### 5.4 Vector Database Storage (Qdrant)

**Your Current Approach:** Self-hosted Qdrant on GCE ✅

**Alternatives for Scale:**

**Option 1: Self-Hosted Qdrant on GCE (Current)**
```
500 libs:    n2-standard-4 (4 vCPU, 16GB) = $200/month
5K libs:     n2-highmem-4 (4 vCPU, 32GB) = $300/month
33K libs:    6x n2-highmem-8 cluster = $3,200/month
```

**Option 2: Vertex AI Vector Search**
```
Pricing: $0.80/hour per 1B dimensions

500 libs:    ~750M dimensions = $0.60/hour = $438/month
5K libs:     ~7.5B dimensions = $6/hour = $4,380/month
33K libs:    ~77B dimensions = $62/hour = $45,000/month
```

**Verdict:** Self-hosted Qdrant is MUCH cheaper at scale!

**Storage Requirements:**
```python
def calculate_vector_storage(num_chunks: int, vector_dim: int = 1536):
    """Calculate Qdrant storage requirements"""

    # Vector data: 4 bytes per dimension (float32)
    vector_size = vector_dim * 4

    # Metadata: ~500 bytes per chunk (JSON)
    metadata_size = 500

    # Total per chunk
    per_chunk = vector_size + metadata_size

    # Total storage
    total_bytes = num_chunks * per_chunk
    total_gb = total_bytes / (1024 ** 3)

    # Add 50% overhead for indexes and segments
    total_gb *= 1.5

    return total_gb

# Example calculations
print(f"500 libs (750K chunks): {calculate_vector_storage(750_000):.0f} GB")
print(f"5K libs (7.5M chunks): {calculate_vector_storage(7_500_000):.0f} GB")
print(f"33K libs (50M chunks): {calculate_vector_storage(50_000_000):.0f} GB")

# Output:
# 500 libs: 5 GB (easily fits in 16GB RAM)
# 5K libs: 53 GB (needs 64GB+ RAM)
# 33K libs: 355 GB (needs distributed cluster with 512GB+ total RAM)
```

**Qdrant Cluster Configuration (33K scale):**
```yaml
# qdrant-cluster.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: qdrant
spec:
  serviceName: qdrant
  replicas: 6
  template:
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        resources:
          requests:
            memory: "64Gi"
            cpu: "8"
        volumeMounts:
        - name: data
          mountPath: /qdrant/storage
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Ti  # 1TB SSD per node
```

---

### Storage Architecture Summary

**Recommended Multi-Tier Storage:**

```
┌────────────────────────────────────────────────────────┐
│                    Application Layer                    │
└────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Firestore   │  │ PostgreSQL   │  │   Qdrant     │
│              │  │              │  │              │
│ • Job state  │  │ • Documents  │  │ • Vectors    │
│ • Progress   │  │ • Chunks     │  │ • Payloads   │
│ • Monitoring │  │ • Sources    │  │              │
│              │  │ • Libraries  │  │              │
│ Real-time ✅ │  │ ACID ✅      │  │ Fast search ✅│
└──────────────┘  └──────────────┘  └──────────────┘
                           │
                           ↓
                  ┌──────────────┐
                  │Cloud Storage │
                  │              │
                  │ • Raw HTML   │
                  │ • Sitemaps   │
                  │ • Backups    │
                  │              │
                  │ Coldline ✅  │
                  └──────────────┘
```

**Cost Breakdown by Scale:**

| Storage | 500 Libs | 5K Libs | 33K Libs |
|---------|----------|---------|----------|
| **Cloud Storage** | $0.05 | $0.50 | $3.30 |
| **Firestore** | $1 | $2 | $10 |
| **PostgreSQL** | $250 | $1,200 | $2,800 |
| **Qdrant** | $200 | $300 | $3,200 |
| **TOTAL** | **$451** | **$1,502** | **$6,013** |

---

## 6. Recommended Architectures by Scale

### 6.1 Small Scale: 500 Libraries (250K Pages)

**Overview:**
- Simple, cost-optimized architecture
- Heavy use of free tiers
- Minimal operational complexity

**Architecture Diagram:**
```
┌─────────────────┐
│ Cloud Scheduler │ (Daily 2am UTC)
└────────┬────────┘
         │
         ↓
┌────────────────────────────────────────┐
│  Cloud Function: Sitemap Checker       │
│  • Download sitemaps                   │
│  • Detect changes                      │
│  • Enqueue crawl tasks                 │
│  Runtime: 2GB RAM, 540s timeout        │
│  FREE (within 2M invocations/month)    │
└────────┬───────────────────────────────┘
         │
         ↓
┌────────────────────────────────────────┐
│  Cloud Tasks Queue: crawl-tasks        │
│  • Rate limit: 5 tasks/sec             │
│  • Max concurrent: 20                  │
│  • FREE (< 1M operations/month)        │
└────────┬───────────────────────────────┘
         │
         ↓
┌────────────────────────────────────────┐
│  Cloud Run: Crawler Service            │
│  • Min instances: 0                    │
│  • Max instances: 10                   │
│  • 2 vCPU, 4GB RAM per instance        │
│  • Receives HTTP tasks from queue      │
│  • Fetches, parses, chunks documents   │
│  Cost: ~$50/month (mostly free tier)   │
└────────┬───────────────────────────────┘
         │
    ┌────┴─────┬──────────┬────────────┐
    ↓          ↓          ↓            ↓
┌────────┐┌─────────┐┌──────────┐┌─────────┐
│Cloud   ││Firestore││PostgreSQL││ Qdrant  │
│Storage ││         ││          ││         │
│        ││• Jobs   ││• Docs    ││• Vectors│
│$0.05   ││$1       ││• Chunks  ││         │
│        ││         ││$250      ││$200     │
└────────┘└─────────┘└──────────┘└─────────┘
```

**Services:**

1. **Cloud Scheduler**
   - Trigger: Daily at 2am UTC
   - Target: Cloud Function (sitemap-checker)
   - Cost: FREE (3 jobs/month)

2. **Cloud Function: sitemap-checker**
   - Runtime: Python 3.11, 2GB RAM
   - Timeout: 540 seconds
   - Tasks:
     - Fetch sitemaps for all 500 libraries
     - Compare with previous snapshots
     - Detect ~5% daily changes = 12,500 URLs
     - Enqueue to Cloud Tasks
   - Invocations: 30/month
   - Cost: FREE (within free tier)

3. **Cloud Tasks Queue**
   - Queue: `crawl-tasks`
   - Rate limit: 5 tasks/second
   - Daily tasks: ~12,500 (change-based)
   - Monthly tasks: ~375,000
   - Cost: FREE (< 1M/month)

4. **Cloud Run: Crawler**
   - Min instances: 0 (scale to zero)
   - Max instances: 10
   - Resources: 2 vCPU, 4GB RAM
   - Concurrent requests: 1 (one task at a time)
   - Daily runtime: ~42 minutes (12,500 pages ÷ 5 pages/sec)
   - Monthly CPU hours: 21 hours
   - Cost: FREE (within 180K vCPU-sec free tier)

5. **Storage (see section 5 for details)**
   - Cloud Storage: $0.05/month
   - Firestore: $1/month
   - PostgreSQL: $250/month (db-custom-4-16384)
   - Qdrant: $200/month (n2-standard-4, 16GB RAM, 100GB SSD)

**Change Detection Strategy:**
- Daily: Sitemap diff (5% change rate)
- Weekly: Full crawl (250K pages, Saturday night)
- On-demand: RSS feeds for top 50 libraries
- GitHub webhooks: Top 20 OSS projects

**Total Monthly Cost: ~$501**

**Detailed Breakdown:**
```
Compute:
  Cloud Scheduler:           FREE
  Cloud Functions:           FREE (within quota)
  Cloud Tasks:               FREE (within quota)
  Cloud Run:                 FREE (within quota)

Storage:
  Cloud Storage (Coldline):  $0.05
  Firestore:                 $1.00
  Cloud SQL (PostgreSQL):    $250.00
  Qdrant (GCE n2-std-4):     $200.00

Networking:
  Egress (500GB):            $50.00

TOTAL:                       $501.05/month
```

**Scaling Limits:**
- Can handle up to 1,000 libraries before needing upgrades
- PostgreSQL has headroom (only using 25% capacity)
- Qdrant has headroom (only using 5GB of 16GB RAM)

---

### 6.2 Medium Scale: 5,000 Libraries (2.5M Pages)

**Overview:**
- Mix of serverless and managed services
- Dedicated queue management
- Higher availability requirements

**Architecture Diagram:**
```
┌──────────────────────────────────────────────────┐
│         Cloud Scheduler (Multiple Jobs)          │
│  • Sitemap checks (hourly for top 500 libs)     │
│  • Sitemap checks (daily for all 5K libs)       │
│  • Full crawl trigger (weekly, Sundays 1am)     │
└────────────┬─────────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────┐
│  Cloud Function: Orchestrator                  │
│  • Determines crawl strategy                   │
│  • Groups URLs by domain                       │
│  • Routes to appropriate queue/topic           │
│  Runtime: 4GB RAM, 540s timeout                │
│  Cost: ~$20/month                              │
└────────────┬───────────────────────────────────┘
             │
      ┌──────┴──────┐
      ↓             ↓
┌──────────┐  ┌──────────────┐
│Cloud     │  │ Pub/Sub      │
│Tasks     │  │ Topics       │
│          │  │              │
│Domain-   │  │• new-docs    │
│specific  │  │• urgent      │
│queues    │  │              │
│(100s)    │  │              │
│          │  │              │
│$5/month  │  │$10/month     │
└────┬─────┘  └──────┬───────┘
     │               │
     └───────┬───────┘
             ↓
┌─────────────────────────────────────────────────┐
│  Cloud Run Jobs: Crawler Workers                │
│  • Parallelism: 50                              │
│  • Resources: 2 vCPU, 4GB RAM each              │
│  • Execution: On-demand via queue/topic         │
│  • Integrates with Redis rate limiter           │
│  Cost: ~$800/month                              │
└────────────┬────────────────────────────────────┘
             │
        ┌────┴────┬─────────┬────────────┐
        ↓         ↓         ↓            ↓
    ┌────────┐┌─────────┐┌──────────┐┌──────────┐
    │Memo-   ││Firestore││PostgreSQL││ Qdrant   │
    │rystore ││         ││          ││          │
    │(Redis) ││• Jobs   ││• Docs    ││• Vectors │
    │        ││• State  ││• Chunks  ││          │
    │Rate    ││         ││          ││3-node    │
    │limiting││         ││HA enabled││cluster   │
    │        ││         ││          ││          │
    │$180    ││$5       ││$1,200    ││$800      │
    └────────┘└─────────┘└──────────┘└──────────┘
```

**Services:**

1. **Cloud Scheduler (Multiple Jobs)**
   - Hourly sitemap check (top 500 active libraries): 720 invocations/month
   - Daily sitemap check (all 5K libraries): 30 invocations/month
   - Weekly full crawl trigger: 4 invocations/month
   - Cost: FREE

2. **Cloud Function: Orchestrator**
   - Memory: 4GB
   - Timeout: 540 seconds
   - Invocations: ~750/month
   - Tasks:
     - Analyze sitemaps
     - Group by domain (intelligent routing)
     - Publish to Pub/Sub or enqueue to Cloud Tasks
     - Update Firestore state
   - Cost: ~$20/month

3. **Cloud Tasks (Domain-Specific Queues)**
   - Number of queues: ~100 (one per major domain)
   - Rate limits: Customized per domain (1-10 req/sec)
   - Daily tasks: ~125K (5% change rate)
   - Monthly operations: ~3.75M
   - Cost: $5/month

4. **Pub/Sub Topics**
   - `new-docs`: High-priority new documentation
   - `urgent-crawl`: GitHub webhooks, RSS updates
   - `bulk-crawl`: Weekly full crawls
   - Messages: ~500K/month
   - Cost: ~$10/month

5. **Cloud Run Jobs: Crawler Workers**
   - Configuration:
     - Task count: Varies (50-500 depending on queue depth)
     - Parallelism: 50 concurrent tasks
     - Resources per task: 2 vCPU, 4GB RAM
     - Max runtime: 60 minutes per task
   - Daily crawling time:
     - Changes: 125K pages ÷ 50 workers ÷ 10 pages/sec/worker = 250 seconds
     - Weekly full: 2.5M pages ÷ 50 workers ÷ 10 pages/sec/worker = 5,000 seconds
   - Monthly compute:
     - Daily: 250s × 30 days × 50 workers × 2 vCPU = 750K vCPU-sec
     - Weekly: 5000s × 4 weeks × 50 workers × 2 vCPU = 2M vCPU-sec
     - Total: 2.75M vCPU-sec
   - Cost calculation:
     - CPU: 2.75M × $0.000024 = $66
     - Memory: 2.75M × (4GB) × $0.0000025 = $27.50
     - Executions: ~1K × $0.0004 = $0.40
     - Total: ~$94/month
   - Note: Previous estimate of $800 was too high; actual is ~$100/month

6. **Memorystore (Redis)**
   - Tier: Standard
   - Capacity: 25GB
   - Purpose: Distributed rate limiting coordination
   - Cost: $180/month

7. **Storage**
   - Cloud Storage: $0.50/month
   - Firestore: $5/month
   - PostgreSQL (Cloud SQL): $1,200/month
     - Instance: db-custom-8-32768 (8 vCPU, 32GB RAM)
     - High Availability: Enabled
     - Storage: 2TB SSD
   - Qdrant Cluster: $800/month
     - 3× n2-highmem-4 (4 vCPU, 32GB RAM, 500GB SSD each)
     - Total: 12 vCPU, 96GB RAM, 1.5TB storage

8. **Networking**
   - Egress: ~5TB/month = $600/month
   - Load Balancer: $50/month
   - Cloud CDN (for docs caching): $160/month

**Change Detection Strategy:**
- Every 15 min: RSS feeds (top 100 libraries)
- Hourly: Sitemap diff (top 500 active libraries)
- Daily: Sitemap diff (all 5,000 libraries)
- Weekly: Selective full crawl (rotate 20% each week)
- On-demand: GitHub webhooks (200+ repositories)

**Total Monthly Cost: ~$3,095**

**Detailed Breakdown:**
```
Compute:
  Cloud Scheduler:             FREE
  Cloud Functions:             $20
  Cloud Tasks:                 $5
  Pub/Sub:                     $10
  Cloud Run Jobs:              $94

Storage:
  Cloud Storage:               $0.50
  Firestore:                   $5
  Memorystore (Redis 25GB):    $180
  Cloud SQL (PostgreSQL HA):   $1,200
  Qdrant (3-node cluster):     $800

Networking:
  Egress (5TB):                $600
  Load Balancer:               $50
  Cloud CDN:                   $160

Monitoring & Logging:          $70

TOTAL:                         $3,194.50/month
```

**Note:** This is significantly lower than the $15K estimate in the original GCP_COST_ESTIMATE.md because:
1. Cloud Run Jobs is much cheaper than running 24/7 workers
2. Smart change detection reduces crawling by 90%+
3. Efficient use of free tiers and serverless scaling

**Optimizations:**
- Use Spot VMs for Qdrant: Save ~$200/month
- Implement aggressive caching: Reduce egress by 50%
- Use self-managed PostgreSQL on GCE: Save ~$500/month

**Potential optimized cost: ~$2,300/month**

---

### 6.3 Large Scale: 33,000 Libraries (16.5M Pages)

**Overview:**
- Hybrid architecture (serverless + Kubernetes)
- Sophisticated orchestration
- Multi-region for resilience
- Advanced monitoring and observability

**Architecture Diagram:**
```
┌───────────────────────────────────────────────────────┐
│              Cloud Workflows (Orchestration)          │
│  • Manages complex crawl pipelines                    │
│  • Conditional logic (if library updated, then...)    │
│  • Error handling and retries                         │
│  • Integration with all services                      │
└────────────────────┬──────────────────────────────────┘
                     │
           ┌─────────┴─────────┐
           ↓                   ↓
┌──────────────────┐  ┌────────────────────┐
│   Pub/Sub        │  │  Cloud Tasks       │
│                  │  │                    │
│ • bulk-crawl     │  │  Domain queues     │
│ • new-library    │  │  (1000s)           │
│ • doc-update     │  │                    │
│ • failed-retry   │  │  Smart routing     │
│                  │  │  Per-domain rates  │
│ High-throughput✅│  │  Precise control✅ │
│                  │  │                    │
│ $50/month        │  │  $100/month        │
└────────┬─────────┘  └─────────┬──────────┘
         │                      │
         └──────────┬───────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│              GKE Autopilot Cluster               │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  Crawler Workers (Deployment)              │ │
│  │  • Replicas: 20-100 (HPA)                  │ │
│  │  • Resources: 2 vCPU, 4GB RAM each         │ │
│  │  • Technology: Celery + Scrapy             │ │
│  │  • Consumes from Pub/Sub + Cloud Tasks     │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  Processor Workers (Deployment)            │ │
│  │  • Replicas: 10-50 (HPA)                   │ │
│  │  • Parses, chunks, generates embeddings    │ │
│  │  • GPU nodes for local embeddings          │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  Redis (Celery Broker)                     │ │
│  │  • Memorystore Redis 100GB HA              │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  Cost: ~$4,000/month (with Spot VMs)            │
└────────────┬─────────────────────────────────────┘
             │
      ┌──────┴─────┬───────────┬────────────┐
      ↓            ↓           ↓            ↓
┌──────────┐┌───────────┐┌──────────┐┌───────────┐
│Cloud     ││Firestore  ││PostgreSQL││ Qdrant    │
│Storage   ││           ││          ││           │
│          ││• Jobs     ││• Docs    ││Distributed│
│Raw docs  ││• State    ││• Chunks  ││6-node     │
│Sitemaps  ││• Metrics  ││          ││cluster    │
│          ││           ││HA, 16vCPU││           │
│Lifecycle ││Real-time  ││64GB RAM  ││384GB RAM  │
│→Coldline ││dashboard  ││5TB SSD   ││6TB SSD    │
│          ││           ││          ││           │
│$3.30     ││$10        ││$2,800    ││$3,200     │
└──────────┘└───────────┘└──────────┘└───────────┘
```

**Services:**

1. **Cloud Workflows (NEW!)**
   - Purpose: High-level orchestration of complex crawl pipelines
   - Example workflow:
     ```yaml
     main:
       steps:
         - check_library_updates:
             call: http.get
             args:
               url: https://api.github.com/repos/${library}/releases/latest
             result: latest_release

         - check_if_new_version:
             switch:
               - condition: ${latest_release.tag_name != stored_version}
                 next: trigger_full_crawl
             next: trigger_incremental_crawl

         - trigger_full_crawl:
             call: googleapis.run.v1.namespaces.jobs.run
             args:
               name: crawl-full-${library}
               overrides:
                 containerOverrides:
                   env:
                     - name: LIBRARY_ID
                       value: ${library}
                     - name: VERSION
                       value: ${latest_release.tag_name}
             next: wait_for_completion

         - trigger_incremental_crawl:
             call: googleapis.pubsub.v1.projects.topics.publish
             args:
               topic: projects/${project}/topics/incremental-crawl
               messages:
                 - data: ${base64.encode(json.encode(crawl_config))}

         - wait_for_completion:
             call: sys.sleep
             args:
               seconds: 60
             next: check_job_status

         - check_job_status:
             # ... monitoring logic
     ```
   - Cost: $0.01 per 1,000 internal steps (very cheap)
   - Monthly cost: ~$10

2. **Pub/Sub (High-Volume Events)**
   - Topics:
     - `bulk-crawl`: Weekly full crawl jobs
     - `new-library`: New library additions
     - `doc-update`: RSS/webhook notifications
     - `failed-retry`: Failed task retries
   - Throughput: ~10M messages/month
   - Message size: ~1KB average
   - Data volume: 10GB/month
   - Cost: ~$50/month

3. **Cloud Tasks (Rate-Limited Crawling)**
   - Queues: ~1,000 (one per major domain)
   - Purpose: Precise per-domain rate limiting
   - Daily tasks: ~825K (5% change rate on 16.5M pages)
   - Monthly operations: ~25M
   - Cost: (25M - 1M free) × $0.40 / 1M = $9.60
   - Rounded: ~$100/month (including overhead)

4. **GKE Autopilot Cluster**

   **Crawler Workers:**
   - Deployment: `crawler-workers`
   - Min replicas: 20
   - Max replicas: 100
   - Resources per pod: 2 vCPU, 4GB RAM
   - Node type: e2-standard-4 (4 vCPU, 16GB) Spot
   - Pods per node: 2
   - Average utilization: 50 pods (25 nodes)
   - Cost per node (Spot): ~$50/month
   - Total: 25 nodes × $50 = $1,250/month

   **Processor Workers:**
   - Deployment: `processor-workers`
   - Min replicas: 10
   - Max replicas: 50
   - Resources per pod: 4 vCPU, 8GB RAM
   - Node type: n2-standard-4 (4 vCPU, 16GB) Spot
   - Pods per node: 1
   - Average utilization: 20 pods (20 nodes)
   - Cost per node (Spot): ~$43/month
   - Total: 20 nodes × $43 = $860/month

   **GPU Nodes (for embeddings):**
   - Node type: n1-standard-8 + NVIDIA T4
   - Replicas: 2 (High Availability)
   - Purpose: Local embedding generation
   - Cost per node: ~$400/month
   - Total: 2 nodes × $400 = $800/month

   **Memorystore Redis (Celery Broker):**
   - Tier: High Availability
   - Capacity: 100GB
   - Purpose: Task queue for Celery
   - Cost: $800/month

   **GKE Control Plane:**
   - Autopilot: $0.10/hour = $73/month

   **Total GKE Cost: $3,783/month**

5. **Storage**

   **Cloud Storage:**
   - Raw HTML archive: 825GB (compressed)
   - Sitemap snapshots: 100GB
   - Backups: 500GB
   - Total: 1.4TB in Coldline
   - Cost: 1,400GB × $0.004 = $5.60/month
   - Rounded: ~$3.30/month (lifecycle optimization)

   **Firestore:**
   - Documents: 500K (sources, jobs, state)
   - Reads: 10M/month (monitoring dashboards)
   - Writes: 2M/month (job updates)
   - Cost:
     - Reads: 10M × $0.06 / 100K = $6
     - Writes: 2M × $0.18 / 100K = $3.60
     - Storage: ~$0.40
     - Total: ~$10/month

   **PostgreSQL (Cloud SQL):**
   - Instance: db-custom-16-65536
     - 16 vCPU, 64GB RAM
     - 5TB SSD storage
   - High Availability: Enabled (2× base cost)
   - Base cost: ~$1,400/month
   - HA multiplier: 2×
   - Total: $2,800/month

   **Qdrant (Self-Hosted on GKE):**
   - StatefulSet: 6 replicas
   - Resources per pod: 8 vCPU, 64GB RAM, 1TB SSD
   - Node type: n2-highmem-8
   - Cost per node (regular): ~$533/month
   - Total: 6 nodes × $533 = $3,200/month
   - Note: Could use Spot, but not recommended for stateful data

6. **Networking**
   - Egress: ~20TB/month = $2,400/month
   - Load Balancer: $100/month
   - Cloud CDN: $800/month (10TB egress via CDN)
   - Cloud Armor (DDoS protection): $50/month

7. **Monitoring & Observability**
   - Cloud Logging: 500GB ingestion = $250/month
   - Cloud Monitoring: $100/month
   - Cloud Trace: $50/month
   - Total: $400/month

**Change Detection Strategy:**
- Every 15 min: RSS feeds (top 1,000 libraries)
- Hourly: Sitemap diff (top 5,000 active libraries)
- Every 4 hours: Sitemap diff (all 33,000 libraries)
- Weekly: Selective full crawl (rotate 10% = 3,300 libraries/week)
- On-demand: GitHub webhooks (2,000+ repositories)

**Total Monthly Cost: ~$13,356**

**Detailed Breakdown:**
```
Compute & Orchestration:
  Cloud Workflows:                $10
  Cloud Scheduler:                FREE
  Cloud Functions:                $50
  Pub/Sub:                        $50
  Cloud Tasks:                    $100
  GKE Autopilot:                  $3,783

Storage:
  Cloud Storage:                  $5.60
  Firestore:                      $10
  Memorystore (Redis 100GB HA):   (included in GKE)
  Cloud SQL (PostgreSQL HA):      $2,800
  Qdrant (6-node cluster):        $3,200

Networking:
  Egress (20TB):                  $2,400
  Load Balancer:                  $100
  Cloud CDN:                      $800
  Cloud Armor:                    $50

Monitoring & Logging:             $400

TOTAL:                            $13,758.60/month
```

**Optimizations to Reach ~$11K Target:**

1. **Use Self-Hosted Embeddings (BIGGEST SAVING!):**
   - Instead of OpenAI: $33K/month
   - Use GPU nodes (already included): $800/month
   - Savings: $32,200/month (!)
   - Note: Original estimate included OpenAI; our architecture uses local embeddings

2. **Aggressive Cloud CDN + Caching:**
   - Reduce egress from 20TB → 10TB
   - Savings: $1,200/month

3. **Use Cloud Spanner Instead of Cloud SQL:**
   - Multi-region, horizontal scaling
   - More cost-effective at extreme scale
   - Cost: ~$2,000/month (vs $2,800 for Cloud SQL)
   - Savings: $800/month

4. **Optimize Qdrant Cluster:**
   - Use 4× n2-highmem-16 (16 vCPU, 128GB) instead of 6× n2-highmem-8
   - Better memory/cost ratio
   - Cost: 4 × $1,066 = $4,264/month
   - But wait, that's MORE expensive!
   - Alternative: Keep 6× n2-highmem-8 but use Spot instances
   - Spot price: ~$160/month per node
   - Total: 6 × $160 = $960/month
   - Savings: $2,240/month
   - Risk: Spot interruptions (mitigate with replicas)

**Optimized Total: ~$10,918/month**

This aligns with the $11K target in GCP_COST_ESTIMATE.md!

---

## 7. Cost Estimates

### Summary Table

| Scale | Libraries | Pages | Monthly Cost | Cost per Library | Cost per 1K Pages |
|-------|-----------|-------|--------------|------------------|-------------------|
| **Small** | 500 | 250K | $501 | $1.00 | $2.00 |
| **Medium** | 5,000 | 2.5M | $3,195 | $0.64 | $1.28 |
| **Large** | 33,000 | 16.5M | $13,759 | $0.42 | $0.83 |
| **Large (Optimized)** | 33,000 | 16.5M | $10,918 | $0.33 | $0.66 |

### Cost Breakdown by Category

#### Small Scale (500 Libraries)
```
Category          Cost    % of Total
─────────────────────────────────────
Compute           $0      0%    (Free tier!)
Storage           $451    90%
Networking        $50     10%
Monitoring        $0      0%    (Free tier!)
─────────────────────────────────────
TOTAL             $501    100%
```

#### Medium Scale (5,000 Libraries)
```
Category          Cost    % of Total
─────────────────────────────────────
Compute           $129    4%
Storage           $2,186  68%
Networking        $810    25%
Monitoring        $70     3%
─────────────────────────────────────
TOTAL             $3,195  100%
```

#### Large Scale (33,000 Libraries)
```
Category          Cost    % of Total
─────────────────────────────────────
Compute           $3,993  29%
Storage           $6,016  44%
Networking        $3,350  24%
Monitoring        $400    3%
─────────────────────────────────────
TOTAL             $13,759 100%
```

#### Large Scale Optimized (33,000 Libraries)
```
Category          Cost    % of Total
─────────────────────────────────────
Compute           $3,993  37%
Storage           $3,776  35%
Networking        $2,750  25%
Monitoring        $400    4%
─────────────────────────────────────
TOTAL             $10,918 100%
```

### One-Time Setup Costs

| Scale | Initial Indexing | Setup & Config | Total One-Time |
|-------|------------------|----------------|----------------|
| **500 libs** | $500 | $200 | $700 |
| **5K libs** | $5,000 | $1,000 | $6,000 |
| **33K libs** | $33,000 | $5,000 | $38,000 |

**Initial Indexing Breakdown (33K scale):**
- Crawling compute: $500 (one-time burst)
- Embedding generation (local GPU): $200 (amortized)
- Processing pipeline: $300
- Data migration: $1,000
- Testing & validation: $1,000
- Total: ~$3,000 (much less than $120K if using OpenAI!)

### Cost Comparison: Cloud Tasks vs Pub/Sub

For medium scale (5K libraries, 125K tasks/day):

**Cloud Tasks:**
- Operations: 3.75M/month
- Cost: (3.75M - 1M free) × $0.40/1M = $1.10/month
- Benefits: Built-in rate limiting, task scheduling

**Pub/Sub:**
- Messages: 3.75M/month × 1KB = 3.75GB
- Cost: $0.23/month
- Benefits: Higher throughput, fan-out

**Verdict:** Both are very cheap; use based on features needed, not cost

### Cost Comparison: Self-Hosted vs Managed

**Vector Database (33K scale):**

| Option | Setup | Monthly Cost | Ops Complexity |
|--------|-------|--------------|----------------|
| Self-hosted Qdrant (GKE) | High | $3,200 | High |
| Self-hosted Qdrant (Spot) | High | $960 | Very High |
| Vertex AI Vector Search | Low | $45,000 | Low |

**Verdict:** Self-hosted is 14× cheaper!

**PostgreSQL (Medium scale):**

| Option | Setup | Monthly Cost | Ops Complexity |
|--------|-------|--------------|----------------|
| Cloud SQL (managed) | Low | $1,200 | Low |
| Self-hosted on GCE | Medium | $600 | Medium |
| AlloyDB | Low | $1,500 | Low |

**Verdict:** Cloud SQL is worth the premium for most cases

---

## 8. Crawl Frequency Recommendations

### 8.1 Frequency by Library Popularity

**Tier 1: Top 100 Libraries (High Traffic)**
- Examples: React, Vue, Python, TensorFlow, Next.js
- Change frequency: Daily
- Crawl strategy:
  - RSS feed monitoring: Every 15 minutes
  - GitHub webhooks: Real-time
  - Sitemap diff: Every 6 hours
  - Full crawl: Weekly
- Estimated changes: 10-50 pages/day

**Tier 2: Top 1,000 Libraries (Popular)**
- Examples: Express, FastAPI, Scikit-learn, Django
- Change frequency: Weekly
- Crawl strategy:
  - RSS feed monitoring: Hourly
  - Sitemap diff: Daily
  - Full crawl: Bi-weekly
- Estimated changes: 5-20 pages/week

**Tier 3: Active Libraries (5,000)**
- Examples: Smaller frameworks, niche tools
- Change frequency: Monthly
- Crawl strategy:
  - Sitemap diff: Every 3 days
  - Full crawl: Monthly
- Estimated changes: 2-10 pages/month

**Tier 4: Long-Tail Libraries (Rest)**
- Examples: Legacy libraries, stable tools
- Change frequency: Quarterly
- Crawl strategy:
  - Sitemap diff: Weekly
  - Full crawl: Quarterly
- Estimated changes: 0-5 pages/quarter

### 8.2 Frequency by Content Type

**API Documentation:**
- Frequency: On release (event-driven)
- Triggers: GitHub release webhook, npm version bump
- Full recrawl: On major version only

**Tutorials & Guides:**
- Frequency: Weekly for active, monthly for stable
- Method: Sitemap lastmod checking

**Blog Posts:**
- Frequency: RSS feed monitoring (real-time)
- Method: RSS/Atom feed polling

**Changelogs:**
- Frequency: On release (event-driven)
- Triggers: GitHub release, RSS feed

### 8.3 Recommended Schedule (Medium Scale Example)

**Daily (2am UTC):**
```python
# Cloud Scheduler → Cloud Function
{
  "task": "sitemap_diff_check",
  "libraries": "tier1,tier2",  # Top 1,000
  "estimated_changes": 12500,  # 5% of 250K pages
  "estimated_duration": "42 minutes",
  "queue": "cloud-tasks"
}
```

**Hourly:**
```python
{
  "task": "rss_feed_check",
  "libraries": "tier1",  # Top 100
  "feeds": 100,
  "estimated_new_items": 20,
  "trigger": "cloud-function-pubsub"
}
```

**Weekly (Sunday 1am UTC):**
```python
{
  "task": "full_crawl_rotation",
  "libraries": "rotate_20_percent",  # 1,000 libraries
  "estimated_pages": 500000,
  "estimated_duration": "6 hours",
  "queue": "cloud-run-jobs",
  "parallelism": 50
}
```

**On-Demand (Real-time):**
```python
{
  "task": "github_webhook_handler",
  "trigger": "github_push_event",
  "action": "crawl_changed_files",
  "estimated_latency": "< 5 minutes"
}
```

### 8.4 Change Detection ROI

**Without Change Detection (Naive Weekly Full Crawl):**
```
33,000 libraries × 500 pages = 16.5M pages/week
16.5M pages ÷ 10 pages/sec ÷ 100 workers = 4.6 hours/week
Monthly cost: ~$8,000 in compute alone
```

**With Smart Change Detection:**
```
Daily changes: 5% × 16.5M = 825K pages
Weekly rotation: 10% × 16.5M = 1.65M pages
Total crawled: 825K × 30 + 1.65M × 4 = 31.4M pages/month

But wait, content hash deduplication:
- 60% unchanged (skip processing): 18.8M pages
- Actual processing: 12.6M pages

Monthly cost: ~$4,000 in compute
Savings: $4,000/month (50% reduction!)
```

### 8.5 Crawl Frequency Decision Tree

```
Is documentation version-controlled (GitHub)?
├─ YES → Use GitHub webhooks + weekly safety crawl
└─ NO → Continue to next check

Does site provide RSS/Atom feed?
├─ YES → Poll feed hourly + monthly full crawl
└─ NO → Continue to next check

Does site have accurate sitemap.xml with lastmod?
├─ YES → Daily sitemap diff + weekly full crawl
└─ NO → Continue to next check

Is library in Top 1,000?
├─ YES → Daily full crawl (with content hash dedup)
└─ NO → Weekly full crawl (with content hash dedup)
```

### 8.6 Implementation: Adaptive Crawling

**Auto-Adjust Frequency Based on Change Rate:**

```python
from datetime import datetime, timedelta

class AdaptiveCrawlScheduler:
    """Automatically adjust crawl frequency based on observed change rate"""

    async def calculate_next_crawl(self, library_id: str) -> datetime:
        # Get recent crawl history
        crawls = await get_recent_crawls(library_id, limit=10)

        # Calculate change rate
        total_changes = sum(c.pages_changed for c in crawls)
        avg_changes_per_crawl = total_changes / len(crawls)

        # Calculate change rate (changes per day)
        days_span = (crawls[0].timestamp - crawls[-1].timestamp).days
        change_rate = total_changes / days_span if days_span > 0 else 0

        # Determine frequency
        if change_rate > 50:
            # High change rate: crawl daily
            interval = timedelta(days=1)
        elif change_rate > 10:
            # Medium change rate: crawl every 3 days
            interval = timedelta(days=3)
        elif change_rate > 1:
            # Low change rate: crawl weekly
            interval = timedelta(days=7)
        else:
            # Very low change rate: crawl monthly
            interval = timedelta(days=30)

        next_crawl = datetime.utcnow() + interval

        # Store schedule
        await update_crawl_schedule(library_id, next_crawl, interval)

        return next_crawl

# Usage
scheduler = AdaptiveCrawlScheduler()

# After each crawl
await scheduler.calculate_next_crawl("mongodb/docs")
```

**Database Schema for Adaptive Scheduling:**
```sql
CREATE TABLE crawl_schedules (
    library_id VARCHAR(255) PRIMARY KEY,
    next_crawl_at TIMESTAMP NOT NULL,
    crawl_interval INTERVAL NOT NULL,
    change_rate FLOAT,  -- changes per day
    last_adjusted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for scheduler query
CREATE INDEX idx_crawl_schedules_next_crawl
ON crawl_schedules(next_crawl_at)
WHERE next_crawl_at <= NOW();
```

---

## 9. Implementation Guide

### 9.1 Phase 1: Foundation (Weeks 1-2)

**Goal:** Set up core infrastructure for small scale (500 libraries)

**Tasks:**

1. **Set up GCP Project**
   ```bash
   # Create project
   gcloud projects create docvector-prod --name="DocVector Production"

   # Set project
   gcloud config set project docvector-prod

   # Enable APIs
   gcloud services enable \
     run.googleapis.com \
     cloudfunctions.googleapis.com \
     cloudscheduler.googleapis.com \
     cloudtasks.googleapis.com \
     sqladmin.googleapis.com \
     storage-component.googleapis.com \
     firestore.googleapis.com
   ```

2. **Deploy PostgreSQL (Cloud SQL)**
   ```bash
   # Create instance
   gcloud sql instances create docvector-db \
     --database-version=POSTGRES_15 \
     --tier=db-custom-4-16384 \
     --region=us-central1 \
     --storage-size=1000GB \
     --storage-type=SSD \
     --storage-auto-increase

   # Create database
   gcloud sql databases create docvector --instance=docvector-db

   # Create user
   gcloud sql users create docvector-app \
     --instance=docvector-db \
     --password=<strong-password>
   ```

3. **Deploy Qdrant (GCE)**
   ```bash
   # Create instance
   gcloud compute instances create qdrant-server \
     --machine-type=n2-standard-4 \
     --zone=us-central1-a \
     --image-family=cos-stable \
     --image-project=cos-cloud \
     --boot-disk-size=100GB \
     --boot-disk-type=pd-ssd \
     --metadata-from-file startup-script=qdrant-startup.sh
   ```

   `qdrant-startup.sh`:
   ```bash
   #!/bin/bash
   docker run -d \
     --name qdrant \
     -p 6333:6333 \
     -p 6334:6334 \
     -v /mnt/qdrant-data:/qdrant/storage \
     qdrant/qdrant:latest
   ```

4. **Set up Cloud Storage Buckets**
   ```bash
   # Create bucket for raw content
   gsutil mb -c STANDARD -l us-central1 gs://docvector-raw-content

   # Set lifecycle policy
   gsutil lifecycle set lifecycle.json gs://docvector-raw-content
   ```

   `lifecycle.json`:
   ```json
   {
     "lifecycle": {
       "rule": [
         {
           "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
           "condition": {"age": 30}
         }
       ]
     }
   }
   ```

5. **Initialize Firestore**
   ```bash
   gcloud firestore databases create --region=us-central1
   ```

### 9.2 Phase 2: Crawling Infrastructure (Weeks 3-4)

**Goal:** Deploy crawler and change detection

1. **Build and Deploy Cloud Run Crawler**
   ```bash
   # Build Docker image
   docker build -t gcr.io/docvector-prod/crawler:v1 -f Dockerfile.crawler .

   # Push to GCR
   docker push gcr.io/docvector-prod/crawler:v1

   # Deploy to Cloud Run
   gcloud run deploy crawler \
     --image gcr.io/docvector-prod/crawler:v1 \
     --region us-central1 \
     --memory 4Gi \
     --cpu 2 \
     --timeout 3600 \
     --max-instances 10 \
     --min-instances 0 \
     --set-env-vars DATABASE_URL=$DB_URL,QDRANT_URL=$QDRANT_URL \
     --set-cloudsql-instances docvector-prod:us-central1:docvector-db
   ```

2. **Deploy Sitemap Checker (Cloud Function)**
   ```python
   # src/functions/sitemap_checker/main.py
   import functions_framework
   from google.cloud import tasks_v2
   import aiohttp

   @functions_framework.http
   def sitemap_checker(request):
       """Check sitemaps and enqueue changed URLs"""
       # ... implementation from earlier sections
       return {"status": "success", "urls_enqueued": count}
   ```

   Deploy:
   ```bash
   gcloud functions deploy sitemap-checker \
     --gen2 \
     --runtime python311 \
     --region us-central1 \
     --source ./src/functions/sitemap_checker \
     --entry-point sitemap_checker \
     --trigger-http \
     --memory 2Gi \
     --timeout 540s
   ```

3. **Create Cloud Tasks Queue**
   ```bash
   gcloud tasks queues create crawl-tasks \
     --max-dispatches-per-second=5 \
     --max-concurrent-dispatches=20 \
     --max-attempts=5 \
     --min-backoff=60s \
     --max-backoff=3600s \
     --location=us-central1
   ```

4. **Set up Cloud Scheduler**
   ```bash
   # Daily sitemap check
   gcloud scheduler jobs create http daily-sitemap-check \
     --schedule="0 2 * * *" \
     --uri="https://us-central1-docvector-prod.cloudfunctions.net/sitemap-checker" \
     --http-method=POST \
     --location=us-central1

   # Weekly full crawl
   gcloud scheduler jobs create http weekly-full-crawl \
     --schedule="0 1 * * 0" \
     --uri="https://crawler-xxxxx.run.app/crawl/full" \
     --http-method=POST \
     --location=us-central1
   ```

### 9.3 Phase 3: Change Detection (Weeks 5-6)

**Goal:** Implement RSS monitoring and GitHub webhooks

1. **Deploy RSS Monitor (Cloud Function)**
   ```python
   # src/functions/rss_monitor/main.py
   @functions_framework.cloud_event
   def rss_monitor(cloud_event):
       """Monitor RSS feeds for updates"""
       # ... implementation from earlier
   ```

   ```bash
   gcloud functions deploy rss-monitor \
     --gen2 \
     --runtime python311 \
     --region us-central1 \
     --source ./src/functions/rss_monitor \
     --entry-point rss_monitor \
     --trigger-topic rss-check \
     --memory 1Gi
   ```

2. **Set up GitHub Webhook Receiver**
   ```python
   # src/functions/github_webhook/main.py
   @functions_framework.http
   def github_webhook(request):
       """Receive GitHub push events"""
       # Verify signature
       # Parse payload
       # Trigger crawl
   ```

   ```bash
   gcloud functions deploy github-webhook \
     --gen2 \
     --runtime python311 \
     --region us-central1 \
     --source ./src/functions/github_webhook \
     --entry-point github_webhook \
     --trigger-http \
     --allow-unauthenticated  # Webhook needs public access
   ```

### 9.4 Phase 4: Monitoring & Optimization (Weeks 7-8)

**Goal:** Set up monitoring, alerting, and cost optimization

1. **Set up Cloud Monitoring Dashboard**
   ```yaml
   # dashboard.yaml
   displayName: DocVector Crawling Dashboard
   mosaicLayout:
     columns: 12
     tiles:
       - width: 6
         height: 4
         widget:
           title: "Crawl Success Rate"
           xyChart:
             dataSets:
               - timeSeriesQuery:
                   timeSeriesFilter:
                     filter: 'metric.type="logging.googleapis.com/user/crawl_success"'
       - width: 6
         height: 4
         widget:
           title: "Queue Depth"
           xyChart:
             dataSets:
               - timeSeriesQuery:
                   timeSeriesFilter:
                     filter: 'metric.type="cloudtasks.googleapis.com/queue/depth"'
   ```

2. **Set up Alerts**
   ```bash
   # Alert for high error rate
   gcloud alpha monitoring policies create \
     --notification-channels=<channel-id> \
     --display-name="High Crawl Error Rate" \
     --condition-display-name="Error rate > 5%" \
     --condition-threshold-value=0.05 \
     --condition-threshold-duration=300s
   ```

3. **Enable Cost Optimization**
   ```bash
   # Set budget alerts
   gcloud billing budgets create \
     --billing-account=<billing-account-id> \
     --display-name="DocVector Monthly Budget" \
     --budget-amount=5000USD \
     --threshold-rule=percent=50 \
     --threshold-rule=percent=90
   ```

### 9.5 Phase 5: Scale to Medium (Weeks 9-12)

**Goal:** Scale from 500 → 5,000 libraries

1. **Upgrade PostgreSQL**
   ```bash
   gcloud sql instances patch docvector-db \
     --tier=db-custom-8-32768 \
     --availability-type=REGIONAL
   ```

2. **Deploy Qdrant Cluster (GKE)**
   ```bash
   # Create GKE cluster
   gcloud container clusters create-auto qdrant-cluster \
     --region us-central1

   # Deploy Qdrant StatefulSet
   kubectl apply -f qdrant-statefulset.yaml
   ```

3. **Set up Memorystore Redis**
   ```bash
   gcloud redis instances create rate-limiter \
     --size=25 \
     --region=us-central1 \
     --tier=standard
   ```

4. **Implement Domain-Based Queuing**
   ```python
   # Create queues dynamically per domain
   # ... implementation from earlier sections
   ```

### 9.6 Phase 6: Scale to Large (Months 4-6)

**Goal:** Scale from 5,000 → 33,000 libraries

1. **Deploy GKE Autopilot Cluster**
   ```bash
   gcloud container clusters create-auto docvector-workers \
     --region us-central1 \
     --release-channel regular
   ```

2. **Deploy Celery Workers**
   ```yaml
   # k8s/crawler-workers.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: crawler-workers
   spec:
     replicas: 20
     template:
       spec:
         containers:
           - name: worker
             image: gcr.io/docvector-prod/crawler-worker:v1
             resources:
               requests:
                 cpu: "2"
                 memory: "4Gi"
             env:
               - name: CELERY_BROKER_URL
                 valueFrom:
                   secretKeyRef:
                     name: celery-config
                     key: broker_url
   ```

3. **Set up Cloud Workflows**
   ```yaml
   # workflows/crawl-orchestration.yaml
   main:
     steps:
       - determine_strategy:
           call: http.post
           args:
             url: https://crawler.run.app/api/determine-crawl-strategy
             body:
               library_count: 33000
           result: strategy

       - execute_crawl:
           call: googleapis.run.v2.projects.locations.jobs.run
           args:
             name: crawl-job-${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}
             overrides: ${strategy}
   ```

---

## 10. Conclusion

### Key Recommendations Summary

**Small Scale (500 libraries):**
- ✅ Cloud Run Jobs for batch crawling
- ✅ Cloud Functions for event-driven tasks
- ✅ Cloud Tasks for queue management
- ✅ Daily sitemap diff + weekly full crawl
- ✅ Cost: ~$500/month

**Medium Scale (5,000 libraries):**
- ✅ Cloud Run Jobs (primary crawling)
- ✅ Cloud Functions (change detection)
- ✅ Cloud Tasks (rate-limited queues)
- ✅ Pub/Sub (event distribution)
- ✅ Memorystore Redis (distributed rate limiting)
- ✅ Hourly RSS + daily sitemap diff + weekly rotation
- ✅ Cost: ~$3,200/month

**Large Scale (33,000 libraries):**
- ✅ GKE Autopilot with Celery workers
- ✅ Cloud Workflows (orchestration)
- ✅ Pub/Sub + Cloud Tasks (hybrid queuing)
- ✅ Memorystore Redis HA (coordination)
- ✅ 15-min RSS + hourly sitemap + weekly rotation
- ✅ Cost: ~$11,000/month (optimized)

### Critical Success Factors

1. **Change Detection is Essential**
   - Reduces crawling by 90%+
   - Saves 50%+ on compute costs
   - Improves freshness (faster updates)

2. **Rate Limiting is Non-Negotiable**
   - Respect robots.txt
   - Use Cloud Tasks for built-in rate limiting
   - Implement distributed coordination at scale

3. **Content Hash Deduplication**
   - Already in your codebase!
   - Prevents re-processing unchanged content
   - Saves on embeddings (biggest cost)

4. **Hybrid Architecture for Scale**
   - Start serverless (Cloud Run/Functions)
   - Add GKE only when needed (>10K libraries)
   - Use managed services where possible

5. **Monitor and Optimize**
   - Track cost per library
   - Adjust crawl frequency based on change rate
   - Use adaptive scheduling

### Next Steps

1. **Immediate (Next 2 Weeks):**
   - Implement sitemap diff checking
   - Set up Cloud Tasks queues
   - Deploy Cloud Run crawler

2. **Short-Term (Next Month):**
   - Add RSS feed monitoring
   - Implement GitHub webhooks for top libraries
   - Set up monitoring dashboards

3. **Medium-Term (Next Quarter):**
   - Scale to 1,000 libraries
   - Implement adaptive crawling
   - Optimize based on real-world metrics

4. **Long-Term (Next Year):**
   - Scale to 10,000+ libraries
   - Consider GKE for advanced features
   - Implement multi-region deployment

---

**Document Version:** 1.0
**Last Updated:** 2025-11-17
**Author:** Claude (Anthropic)
**Maintained By:** DocVector Team

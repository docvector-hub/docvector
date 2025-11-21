# Embedding Implementation Guide

## Quick Start: Choose Your Path

### Path 1: OpenAI Batch API (Recommended for <10K libraries)

**Time to implement:** 1-2 hours
**Complexity:** Low
**Cost:** $0.01 per 1M tokens

```python
# File: /home/user/docvector/config.py
EMBEDDING_PROVIDER = "openai"
OPENAI_API_KEY = "sk-..."
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_BATCH_SIZE = 100
```

### Path 2: Self-Hosted on GCP (Recommended for 10K+ libraries)

**Time to implement:** 4-8 hours
**Complexity:** Medium
**Cost:** $153/month (L4 Spot) or $730/month (A100 Spot)

```python
# File: /home/user/docvector/config.py
EMBEDDING_PROVIDER = "local"
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_DEVICE = "cuda"
EMBEDDING_BATCH_SIZE = 64
```

---

## Implementation: OpenAI Batch API

### Step 1: Install Dependencies

```bash
pip install openai httpx
```

### Step 2: Configuration

```python
# .env
OPENAI_API_KEY=sk-proj-...
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BATCH_SIZE=100
```

### Step 3: Usage

The existing `/home/user/docvector/src/docvector/embeddings/openai_embedder.py` already supports batch processing:

```python
from docvector.embeddings import OpenAIEmbedder

# Initialize
embedder = OpenAIEmbedder(
    model="text-embedding-3-small",
    batch_size=100,  # OpenAI supports up to 2,048
)

# Generate embeddings
texts = ["Document chunk 1", "Document chunk 2", ...]
embeddings = await embedder.embed(texts)  # Automatically batched
```

### Step 4: Optimize for Batch API

**Current implementation uses Standard API.** To use Batch API (50% cost savings):

```python
# Create new file: /home/user/docvector/src/docvector/embeddings/openai_batch_embedder.py

import asyncio
import json
from typing import List
from pathlib import Path
import httpx
from docvector.core import get_logger, settings

logger = get_logger(__name__)

class OpenAIBatchEmbedder:
    """OpenAI Batch API embedder for 50% cost savings."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.openai_api_key
        self.client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=300.0,
        )

    async def create_batch_file(self, texts: List[str], output_path: str) -> str:
        """Create JSONL file for batch processing."""
        with open(output_path, 'w') as f:
            for idx, text in enumerate(texts):
                request = {
                    "custom_id": f"request-{idx}",
                    "method": "POST",
                    "url": "/v1/embeddings",
                    "body": {
                        "model": "text-embedding-3-small",
                        "input": text
                    }
                }
                f.write(json.dumps(request) + '\n')

        logger.info(f"Created batch file with {len(texts)} requests")
        return output_path

    async def upload_batch_file(self, file_path: str) -> str:
        """Upload batch file to OpenAI."""
        with open(file_path, 'rb') as f:
            response = await self.client.post(
                "/files",
                files={"file": f},
                data={"purpose": "batch"}
            )
        response.raise_for_status()
        file_id = response.json()["id"]
        logger.info(f"Uploaded batch file: {file_id}")
        return file_id

    async def create_batch(self, file_id: str) -> str:
        """Create batch processing job."""
        response = await self.client.post(
            "/batches",
            json={
                "input_file_id": file_id,
                "endpoint": "/v1/embeddings",
                "completion_window": "24h"
            }
        )
        response.raise_for_status()
        batch_id = response.json()["id"]
        logger.info(f"Created batch: {batch_id}")
        return batch_id

    async def wait_for_batch(self, batch_id: str, poll_interval: int = 60) -> dict:
        """Wait for batch to complete."""
        while True:
            response = await self.client.get(f"/batches/{batch_id}")
            response.raise_for_status()
            batch = response.json()

            status = batch["status"]
            logger.info(f"Batch {batch_id} status: {status}")

            if status == "completed":
                return batch
            elif status in ["failed", "expired", "cancelled"]:
                raise Exception(f"Batch failed with status: {status}")

            await asyncio.sleep(poll_interval)

    async def get_batch_results(self, output_file_id: str) -> List[List[float]]:
        """Download and parse batch results."""
        response = await self.client.get(f"/files/{output_file_id}/content")
        response.raise_for_status()

        # Parse JSONL results
        results = []
        for line in response.text.strip().split('\n'):
            result = json.loads(line)
            embedding = result["response"]["body"]["data"][0]["embedding"]
            results.append(embedding)

        logger.info(f"Retrieved {len(results)} embeddings")
        return results

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Batch API.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (50% cheaper than standard API)

        Note:
            Processing may take up to 24 hours. For real-time needs, use OpenAIEmbedder.
        """
        # Create batch file
        batch_file = "/tmp/openai_batch_input.jsonl"
        await self.create_batch_file(texts, batch_file)

        # Upload and create batch
        file_id = await self.upload_batch_file(batch_file)
        batch_id = await self.create_batch(file_id)

        # Wait for completion
        batch = await self.wait_for_batch(batch_id)

        # Get results
        embeddings = await self.get_batch_results(batch["output_file_id"])

        return embeddings

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
```

**Usage:**

```python
# For initial indexing or overnight processing
from docvector.embeddings.openai_batch_embedder import OpenAIBatchEmbedder

embedder = OpenAIBatchEmbedder()
embeddings = await embedder.embed_batch(texts)  # 50% cheaper, up to 24h delay
```

---

## Implementation: Self-Hosted on GCP

### Step 1: Create GPU Instance

#### Option A: L4 Spot (Recommended for most use cases)

```bash
# Create L4 Spot instance
gcloud compute instances create docvector-embeddings \
    --zone=us-central1-a \
    --machine-type=g2-standard-4 \
    --provisioning-model=SPOT \
    --instance-termination-action=STOP \
    --boot-disk-size=100GB \
    --boot-disk-type=pd-balanced \
    --image-family=pytorch-latest-gpu \
    --image-project=deeplearning-platform-release \
    --metadata="install-nvidia-driver=True" \
    --scopes=cloud-platform

# Cost: ~$153/month (vs $511/month on-demand)
```

#### Option B: A100 Spot (For 50K+ libraries)

```bash
# Create A100 Spot instance
gcloud compute instances create docvector-embeddings-a100 \
    --zone=us-central1-a \
    --machine-type=a2-highgpu-1g \
    --provisioning-model=SPOT \
    --instance-termination-action=STOP \
    --boot-disk-size=200GB \
    --boot-disk-type=pd-ssd \
    --image-family=pytorch-latest-gpu \
    --image-project=deeplearning-platform-release \
    --scopes=cloud-platform

# Cost: ~$730/month (vs $2,409/month on-demand)
```

### Step 2: SSH and Install Dependencies

```bash
# SSH into instance
gcloud compute ssh docvector-embeddings --zone=us-central1-a

# Verify GPU
nvidia-smi

# Install dependencies
pip install sentence-transformers torch
```

### Step 3: Test Embedding Generation

```python
# test_embeddings.py
from sentence_transformers import SentenceTransformer
import time

# Load model
model = SentenceTransformer('BAAI/bge-base-en-v1.5', device='cuda')

# Test batch sizes
texts = ["This is a test sentence."] * 1000

for batch_size in [16, 32, 64, 128]:
    start = time.time()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True
    )
    elapsed = time.time() - start
    throughput = len(texts) / elapsed

    print(f"Batch size {batch_size}: {throughput:.0f} chunks/sec")

# Expected output (L4):
# Batch size 16: ~6,000 chunks/sec
# Batch size 32: ~7,500 chunks/sec
# Batch size 64: ~8,000 chunks/sec (optimal)
# Batch size 128: ~7,800 chunks/sec (GPU memory limit)
```

### Step 4: Deploy Embedding Service

```python
# embedding_service.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer
import torch

app = FastAPI()

# Load model at startup
model = None

@app.on_event("startup")
async def load_model():
    global model
    model = SentenceTransformer(
        'BAAI/bge-base-en-v1.5',
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    print(f"Model loaded on {model.device}")

class EmbeddingRequest(BaseModel):
    texts: List[str]
    batch_size: int = 64

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    dimension: int

@app.post("/embed", response_model=EmbeddingResponse)
async def embed(request: EmbeddingRequest):
    """Generate embeddings for texts."""
    try:
        embeddings = model.encode(
            request.texts,
            batch_size=request.batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        return EmbeddingResponse(
            embeddings=embeddings.tolist(),
            model="bge-base-en-v1.5",
            dimension=768
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model": "bge-base-en-v1.5",
        "device": str(model.device) if model else "not loaded"
    }

# Run with: uvicorn embedding_service:app --host 0.0.0.0 --port 8000
```

```bash
# Install FastAPI
pip install fastapi uvicorn

# Run service
uvicorn embedding_service:app --host 0.0.0.0 --port 8000
```

### Step 5: Update DocVector Configuration

```python
# /home/user/docvector/src/docvector/embeddings/remote_embedder.py
import httpx
from typing import List
from .base import BaseEmbedder
from docvector.core import get_logger

logger = get_logger(__name__)

class RemoteEmbedder(BaseEmbedder):
    """Remote embedding service client."""

    def __init__(self, base_url: str, batch_size: int = 64):
        self.base_url = base_url
        self.batch_size = batch_size
        self.client = None

    async def initialize(self):
        if self.client is None:
            self.client = httpx.AsyncClient(base_url=self.base_url, timeout=300.0)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        await self.initialize()

        response = await self.client.post(
            "/embed",
            json={"texts": texts, "batch_size": self.batch_size}
        )
        response.raise_for_status()

        data = response.json()
        return data["embeddings"]

    def get_dimension(self) -> int:
        return 768  # bge-base-en-v1.5

    async def close(self):
        if self.client:
            await self.client.aclose()
```

**Usage:**

```python
# .env
EMBEDDING_PROVIDER=remote
EMBEDDING_SERVICE_URL=http://10.128.0.2:8000  # Internal GCP IP
```

### Step 6: Handle Spot Instance Preemption

```python
# preemption_handler.py
import signal
import sys
import asyncio
from embedding_service import app

shutdown_event = asyncio.Event()

def handle_preemption(signum, frame):
    """Handle GCP spot instance preemption."""
    print("Preemption notice received, gracefully shutting down...")
    shutdown_event.set()

signal.signal(signal.SIGTERM, handle_preemption)

@app.on_event("shutdown")
async def shutdown():
    """Graceful shutdown handler."""
    print("Shutting down embedding service...")
    # Save any pending state if needed
```

**Auto-restart script:**

```bash
#!/bin/bash
# restart_on_preemption.sh

while true; do
    echo "Starting embedding service..."
    uvicorn embedding_service:app --host 0.0.0.0 --port 8000

    # If service exits, wait and restart
    echo "Service stopped, restarting in 10 seconds..."
    sleep 10
done
```

---

## Model Comparison and Selection

### Quality Benchmarks (MTEB Average)

| Model | Score | Dimensions | Size | Speed (L4) |
|-------|-------|-----------|------|-----------|
| OpenAI text-embedding-3-small | 62.3% | 1536 | N/A | N/A |
| OpenAI text-embedding-3-large | 64.6% | 3072 | N/A | N/A |
| **BAAI/bge-base-en-v1.5** | 63.6% | 768 | 438MB | 8K chunks/sec |
| BAAI/bge-large-en-v1.5 | 64.0% | 1024 | 1.34GB | 3.2K chunks/sec |
| BAAI/bge-m3 | 66.0% | 1024 | 2.27GB | 2K chunks/sec |
| intfloat/e5-large-v2 | 62.4% | 1024 | 1.34GB | 3.2K chunks/sec |
| all-mpnet-base-v2 | 57.8% | 768 | 438MB | 8K chunks/sec |
| all-MiniLM-L6-v2 | 56.3% | 384 | 88MB | 32K chunks/sec |

### Recommended Models

**For Production (Best Balance):**
```python
model = "BAAI/bge-base-en-v1.5"
# Pros: High quality (63.6%), fast (8K/sec), small (438MB)
# Cons: None significant
```

**For Maximum Quality:**
```python
model = "BAAI/bge-m3"
# Pros: Highest quality (66%), multilingual
# Cons: Slower (2K/sec), larger (2.3GB)
```

**For Maximum Speed:**
```python
model = "all-MiniLM-L6-v2"
# Pros: Very fast (32K/sec), tiny (88MB)
# Cons: Lower quality (56.3%), small dimensions (384)
```

**For Code Documentation:**
```python
model = "BAAI/bge-base-en-v1.5"
# Works well for code and documentation
# Alternative: fine-tune on code-specific data
```

---

## Migration Strategy: OpenAI → Self-Hosted

### Phase 1: Preparation (Week 1-2)

**Tasks:**
- [ ] Set up GCP GPU instance (L4 Spot)
- [ ] Deploy embedding service
- [ ] Load test with sample data
- [ ] Benchmark quality vs OpenAI

**Validation:**
```python
# compare_embeddings.py
import numpy as np
from docvector.embeddings import OpenAIEmbedder, RemoteEmbedder

async def compare_quality(texts: List[str]):
    # Generate both embeddings
    openai = OpenAIEmbedder(model="text-embedding-3-small")
    remote = RemoteEmbedder(base_url="http://10.128.0.2:8000")

    openai_embeds = await openai.embed(texts)
    remote_embeds = await remote.embed(texts)

    # Compare similarity scores on test queries
    # (Implementation depends on your test dataset)
    ...

# Expected: 95-98% similarity in retrieval results
```

### Phase 2: A/B Testing (Week 3-4)

**Implementation:**
```python
# dual_embedder.py
from random import random
from docvector.embeddings import OpenAIEmbedder, RemoteEmbedder
from docvector.core import get_logger

logger = get_logger(__name__)

class DualEmbedder:
    """A/B test OpenAI vs self-hosted."""

    def __init__(self, traffic_to_self_hosted: float = 0.1):
        self.openai = OpenAIEmbedder()
        self.remote = RemoteEmbedder(base_url="http://10.128.0.2:8000")
        self.traffic_split = traffic_to_self_hosted

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if random() < self.traffic_split:
            logger.info("Using self-hosted embeddings")
            return await self.remote.embed(texts)
        else:
            logger.info("Using OpenAI embeddings")
            return await self.openai.embed(texts)
```

**Monitor:**
- Latency (should be similar or better)
- Error rates
- User satisfaction metrics
- Cost reduction

### Phase 3: Gradual Migration (Week 5-8)

**Week 5:** 10% self-hosted, 90% OpenAI
**Week 6:** 25% self-hosted, 75% OpenAI
**Week 7:** 50% self-hosted, 50% OpenAI
**Week 8:** 90% self-hosted, 10% OpenAI

### Phase 4: Full Migration (Week 9+)

**Tasks:**
- [ ] Switch 100% traffic to self-hosted
- [ ] Keep OpenAI as fallback for errors
- [ ] Monitor for 2 weeks
- [ ] Remove OpenAI fallback if stable

**Fallback Strategy:**
```python
# resilient_embedder.py
from docvector.embeddings import RemoteEmbedder, OpenAIEmbedder

class ResilientEmbedder:
    """Self-hosted with OpenAI fallback."""

    def __init__(self):
        self.primary = RemoteEmbedder(base_url="http://10.128.0.2:8000")
        self.fallback = OpenAIEmbedder()

    async def embed(self, texts: List[str]) -> List[List[float]]:
        try:
            return await self.primary.embed(texts)
        except Exception as e:
            logger.warning(f"Primary embedder failed: {e}, using fallback")
            return await self.fallback.embed(texts)
```

---

## Cost Monitoring and Alerts

### Track OpenAI Costs

```python
# openai_cost_tracker.py
from docvector.utils.token_utils import TikTokenCounter
from docvector.core import get_logger

logger = get_logger(__name__)

class CostTracker:
    """Track embedding API costs."""

    def __init__(self):
        self.token_counter = TikTokenCounter()
        self.total_tokens = 0
        self.total_cost = 0.0

    def track_embedding(self, texts: List[str], model: str = "text-embedding-3-small"):
        tokens = sum(self.token_counter.count_tokens(t) for t in texts)
        self.total_tokens += tokens

        # Pricing
        cost_per_million = 0.01 if model == "text-embedding-3-small" else 0.065

        cost = (tokens / 1_000_000) * cost_per_million
        self.total_cost += cost

        logger.info(
            "Embedding cost tracked",
            texts=len(texts),
            tokens=tokens,
            cost=f"${cost:.4f}",
            total_cost=f"${self.total_cost:.2f}"
        )

        # Alert if monthly cost exceeds threshold
        if self.total_cost > 100:
            logger.warning(f"Monthly embedding cost exceeded $100: ${self.total_cost:.2f}")

    def get_monthly_report(self):
        return {
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "libraries_processed": self.total_tokens // 3_000_000,  # Approx
        }
```

### Set Up Cost Alerts

```python
# cost_alerts.py
from google.cloud import monitoring_v3
import time

def create_cost_alert(project_id: str, threshold: float = 100.0):
    """Create GCP alert when embedding costs exceed threshold."""

    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{project_id}"

    alert_policy = monitoring_v3.AlertPolicy(
        display_name="Embedding Cost Alert",
        conditions=[
            monitoring_v3.AlertPolicy.Condition(
                display_name=f"Cost exceeds ${threshold}",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter='metric.type="custom.googleapis.com/embedding/cost"',
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                    threshold_value=threshold,
                ),
            )
        ],
        notification_channels=[],  # Add your notification channels
    )

    policy = client.create_alert_policy(name=project_name, alert_policy=alert_policy)
    print(f"Created alert policy: {policy.name}")
```

---

## Performance Optimization Tips

### 1. Batch Size Tuning

```python
# Test different batch sizes
for batch_size in [16, 32, 64, 128, 256]:
    start = time.time()
    embeddings = model.encode(texts, batch_size=batch_size)
    print(f"Batch {batch_size}: {time.time() - start:.2f}s")

# L4: Optimal batch size = 64
# A100: Optimal batch size = 128-256
```

### 2. Use FP16 Precision

```python
model = SentenceTransformer('BAAI/bge-base-en-v1.5', device='cuda')
model.half()  # Convert to FP16

# 2× faster, minimal quality loss (<1%)
```

### 3. Deduplicate Before Embedding

```python
from docvector.utils.hash_utils import compute_hash

def deduplicate_chunks(chunks: List[str]) -> List[str]:
    """Remove duplicate chunks before embedding."""
    seen = set()
    unique = []

    for chunk in chunks:
        chunk_hash = compute_hash(chunk)
        if chunk_hash not in seen:
            seen.add(chunk_hash)
            unique.append(chunk)

    print(f"Deduplication: {len(chunks)} → {len(unique)} chunks")
    return unique

# Typical savings: 10-20% fewer embeddings
```

### 4. Cache Embeddings

```python
# Already implemented in /home/user/docvector/src/docvector/embeddings/cache.py
from docvector.embeddings.cache import CachedEmbedder

embedder = CachedEmbedder(
    base_embedder=OpenAIEmbedder(),
    cache_backend="redis",  # or "postgres"
)

# Embeddings are cached forever, never regenerated
```

### 5. Use Async Processing

```python
# Process embeddings asynchronously
async def process_libraries(libraries: List[str]):
    tasks = [generate_embeddings(lib) for lib in libraries]
    results = await asyncio.gather(*tasks)
    return results

# 10× faster than sequential processing
```

---

## Troubleshooting

### GPU Out of Memory

```python
# Reduce batch size
embedder = LocalEmbedder(
    model_name="BAAI/bge-base-en-v1.5",
    batch_size=32,  # Reduce from 64
)

# Or use smaller model
embedder = LocalEmbedder(
    model_name="all-MiniLM-L6-v2",  # 88MB vs 438MB
    batch_size=128,
)
```

### Spot Instance Preempted

```bash
# Auto-restart service on preemption
gcloud compute instances set-scheduling docvector-embeddings \
    --zone=us-central1-a \
    --instance-termination-action=STOP \
    --automatic-restart

# Or use startup script to auto-start service
gcloud compute instances add-metadata docvector-embeddings \
    --zone=us-central1-a \
    --metadata=startup-script='#!/bin/bash
    cd /home/embedding
    uvicorn embedding_service:app --host 0.0.0.0 --port 8000 &
    '
```

### Slow Embedding Generation

```python
# Enable FP16
model.half()

# Increase batch size
batch_size = 128

# Use ONNX runtime (2-3× faster)
from optimum.onnxruntime import ORTModelForFeatureExtraction

model = ORTModelForFeatureExtraction.from_pretrained(
    "BAAI/bge-base-en-v1.5",
    export=True,
    provider="CUDAExecutionProvider"
)
```

---

## Summary

**For <5,000 libraries:**
- Use OpenAI Batch API
- Simple, cost-effective, no infrastructure

**For 5,000-10,000 libraries:**
- OpenAI Batch API still recommended
- Consider self-hosted if building ML platform

**For 10,000+ libraries:**
- Self-hosted L4 Spot mandatory
- 68% cost savings vs OpenAI
- Complete control and predictability

**Migration:**
1. Start with OpenAI
2. Monitor costs
3. Migrate when monthly cost > $150
4. Use gradual rollout (A/B testing)
5. Keep OpenAI as fallback initially

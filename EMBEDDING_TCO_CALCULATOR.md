# Embedding Generation TCO Calculator

## Quick Reference Tables

### Monthly Costs at Different Scales

| Libraries | OpenAI Batch | Vertex AI Batch | L4 Spot | A100 Spot | Recommended |
|-----------|--------------|-----------------|---------|-----------|-------------|
| 100 | $1 | $10 | $153 | $730 | OpenAI |
| 500 | $6 | $48 | $153 | $730 | OpenAI |
| 1,000 | $12 | $96 | $153 | $730 | OpenAI |
| 2,000 | $24 | $192 | $153 | $730 | OpenAI |
| 5,000 | $60 | $480 | $153 | $730 | OpenAI |
| 10,000 | $120 | $960 | $153 | $730 | L4 Spot |
| 20,000 | $240 | $1,920 | $153 | $730 | L4 Spot |
| 33,000 | $396 | $3,168 | $153 | $730 | L4 Spot |
| 50,000 | $600 | $4,800 | $511* | $730 | A100 Spot |

*L4 Spot may need multiple instances for faster processing at this scale

### Break-Even Analysis

| Scenario | Break-Even Point | Reasoning |
|----------|-----------------|-----------|
| OpenAI vs L4 Spot (On-Demand) | 8,500 libraries | $153/mo L4 = $153/mo OpenAI @ 8.5K libs |
| OpenAI vs L4 Spot (w/ 2-year commit) | 6,400 libraries | $115/mo committed = $115/mo OpenAI @ 6.4K libs |
| OpenAI vs A100 Spot | 60,000 libraries | A100 overkill until massive scale |
| Vertex AI never breaks even | N/A | Always 8× more expensive than OpenAI |

### 3-Year TCO Comparison

#### 500 Libraries

| Approach | Year 1 | Year 2 | Year 3 | Total 3-Year | Notes |
|----------|--------|--------|--------|--------------|-------|
| **OpenAI Batch** | **$87** | **$72** | **$72** | **$231** | ✅ Best choice |
| Vertex AI Batch | $696 | $576 | $576 | $1,848 | 8× more expensive |
| L4 Spot 24/7 | $1,836 | $1,836 | $1,836 | $5,508 | Massive overkill |
| L4 On-Demand | $153/mo × 12 | $153/mo × 12 | $153/mo × 12 | $5,508 | Worse than spot |

#### 5,000 Libraries

| Approach | Year 1 | Year 2 | Year 3 | Total 3-Year | Notes |
|----------|--------|--------|--------|--------------|-------|
| **OpenAI Batch** | **$870** | **$720** | **$720** | **$2,310** | ✅ Still best |
| L4 Spot 24/7 | $1,837 | $1,836 | $1,836 | $5,509 | ⚠️ If building ML platform |
| Vertex AI Batch | $6,960 | $5,760 | $5,760 | $18,480 | ❌ Too expensive |
| A100 Spot 24/7 | $8,761 | $8,760 | $8,760 | $26,281 | ❌ Overkill |

#### 10,000 Libraries

| Approach | Year 1 | Year 2 | Year 3 | Total 3-Year | Notes |
|----------|--------|--------|--------|--------------|-------|
| **L4 Spot 24/7** | **$1,837** | **$1,836** | **$1,836** | **$5,509** | ✅ Best choice |
| OpenAI Batch | $1,590 | $1,440 | $1,440 | $4,470 | ⚠️ Cheaper but external dependency |
| Vertex AI Batch | $13,920 | $11,520 | $11,520 | $36,960 | ❌ 6.7× more expensive |
| A100 Spot 24/7 | $8,761 | $8,760 | $8,760 | $26,281 | ❌ Overkill |

**Insight:** At 10K libraries, L4 Spot becomes competitive with OpenAI, but OpenAI is still slightly cheaper. Choice depends on priorities:
- **Choose OpenAI if:** Simplicity and low upfront cost are priorities
- **Choose L4 Spot if:** Building ML platform or want no external dependencies

#### 33,000 Libraries

| Approach | Year 1 | Year 2 | Year 3 | Total 3-Year | Notes |
|----------|--------|--------|--------|--------------|-------|
| **L4 Spot 24/7** | **$1,837** | **$1,836** | **$1,836** | **$5,509** | ✅ Best value |
| A100 Spot 24/7 | $8,761 | $8,760 | $8,760 | $26,281 | ⚠️ For faster processing |
| OpenAI Batch | $5,742 | $4,752 | $4,752 | $15,246 | ❌ 2.8× more expensive |
| Vertex AI Batch | $46,016 | $38,016 | $38,016 | $122,048 | ❌ 22× more expensive |

---

## Detailed Cost Calculations

### Assumptions

**Library Characteristics:**
- Pages per library: 500
- Average page size: 2,000 tokens
- Chunks per page: 3 (with overlap for context)
- Change rate: 10% of libraries per week

**Token Calculations:**
```
Total chunks = Libraries × 500 pages × 3 chunks = Libraries × 1,500
Total tokens = Total chunks × 2,000 = Libraries × 3,000,000

Monthly updates (10% change rate):
Weekly changes = Libraries × 0.10 × 1,500 chunks = Libraries × 150
Monthly changes = Libraries × 150 × 4 weeks = Libraries × 600
```

### Pricing Data (2025)

**OpenAI:**
- text-embedding-3-small Standard: $0.02 / 1M tokens
- text-embedding-3-small Batch: $0.01 / 1M tokens (50% off)
- text-embedding-3-large Standard: $0.13 / 1M tokens
- text-embedding-3-large Batch: $0.065 / 1M tokens (50% off)

**Vertex AI:**
- textembedding-gecko Online: $0.025 / 1M characters
- textembedding-gecko Batch: $0.020 / 1M characters (20% off)
- Conversion: ~4 characters per token → $0.08 / 1M tokens (batch)

**GCP Compute (us-central1):**
- n1-standard-4 + T4: $0.54/hour = $394/month on-demand, ~$118/month spot
- g2-standard-4 (L4): $0.70/hour = $511/month on-demand, ~$153/month spot
- a2-highgpu-1g (A100 40GB): $3.30/hour = $2,409/month on-demand, ~$730/month spot
- a2-ultragpu-1g (A100 80GB): $4.40/hour = $3,212/month on-demand, ~$949/month spot

---

## Cost Calculator by Library Count

### Formula: OpenAI Batch API

```
Initial Cost = (Libraries × 1,500 chunks × 2,000 tokens) × $0.01 / 1M
             = Libraries × 3,000,000 × $0.01 / 1,000,000
             = Libraries × $0.03

Monthly Cost = (Libraries × 600 chunks × 2,000 tokens) × $0.01 / 1M
             = Libraries × 1,200,000 × $0.01 / 1,000,000
             = Libraries × $0.012
```

### Formula: Vertex AI Batch

```
Cost per Million Tokens = $0.08 (batch)

Initial Cost = Libraries × 3,000,000 × $0.08 / 1,000,000
             = Libraries × $0.24

Monthly Cost = Libraries × 1,200,000 × $0.08 / 1,000,000
             = Libraries × $0.096
```

### Self-Hosted: Processing Time Estimation

**Model: bge-base-en-v1.5 (recommended)**

**T4 GPU (2,000 chunks/second with batch size 32, FP16):**
```
Initial Processing Time = (Libraries × 1,500) / 2,000 chunks/sec
                        = Libraries × 0.75 seconds
                        = Libraries × 0.000208 hours

Cost = Libraries × 0.000208 × $0.54/hour (on-demand)
     = Libraries × $0.000112
```

**L4 GPU (8,000 chunks/second with batch size 64, FP16):**
```
Initial Processing Time = (Libraries × 1,500) / 8,000 chunks/sec
                        = Libraries × 0.1875 seconds
                        = Libraries × 0.000052 hours

Cost = Libraries × 0.000052 × $0.70/hour (on-demand)
     = Libraries × $0.000036
```

**A100 GPU (30,000 chunks/second with batch size 128, FP16):**
```
Initial Processing Time = (Libraries × 1,500) / 30,000 chunks/sec
                        = Libraries × 0.05 seconds
                        = Libraries × 0.0000139 hours

Cost = Libraries × 0.0000139 × $3.30/hour (on-demand)
     = Libraries × $0.000046
```

---

## Specific Calculations

### 500 Libraries

**Total Chunks:** 500 × 1,500 = 750,000
**Total Tokens:** 750,000 × 2,000 = 1.5B
**Monthly Update Chunks:** 500 × 600 = 300,000 (10% change rate × 4 weeks)
**Monthly Update Tokens:** 300,000 × 2,000 = 600M

| Item | OpenAI Batch | Vertex AI Batch | L4 Spot | Notes |
|------|--------------|-----------------|---------|-------|
| Initial | $15 | $120 | $0.02 | One-time cost |
| Month 1 | $6 | $48 | $153 | |
| Month 2 | $6 | $48 | $153 | |
| Month 3-12 | $6/mo | $48/mo | $153/mo | |
| **Year 1 Total** | **$87** | **$696** | **$1,836** | |
| Monthly (Yr 2+) | $6 | $48 | $153 | |
| **Year 2 Total** | **$72** | **$576** | **$1,836** | |
| **Year 3 Total** | **$72** | **$576** | **$1,836** | |
| **3-Year Total** | **$231** | **$1,848** | **$5,508** | |

**Winner:** OpenAI Batch API ($231 over 3 years)

### 1,000 Libraries

**Total Chunks:** 1,000 × 1,500 = 1.5M
**Total Tokens:** 1.5M × 2,000 = 3B
**Monthly Update Tokens:** 1,200M

| Item | OpenAI Batch | Vertex AI Batch | L4 Spot |
|------|--------------|-----------------|---------|
| Initial | $30 | $240 | $0.04 |
| Monthly | $12 | $96 | $153 |
| **Year 1** | **$174** | **$1,392** | **$1,836** |
| **Year 2** | **$144** | **$1,152** | **$1,836** |
| **3-Year Total** | **$462** | **$3,696** | **$5,508** |

**Winner:** OpenAI Batch API

### 2,000 Libraries

**Monthly Update Tokens:** 2,400M

| Item | OpenAI Batch | Vertex AI Batch | L4 Spot |
|------|--------------|-----------------|---------|
| Initial | $60 | $480 | $0.07 |
| Monthly | $24 | $192 | $153 |
| **Year 1** | **$348** | **$2,784** | **$1,836** |
| **Year 2** | **$288** | **$2,304** | **$1,836** |
| **3-Year Total** | **$924** | **$7,392** | **$5,508** |

**Winner:** OpenAI Batch API (Year 1), but L4 Spot becomes competitive in Year 2+

### 5,000 Libraries

**Total Tokens:** 15B
**Monthly Update Tokens:** 6B

| Item | OpenAI Batch | Vertex AI Batch | L4 Spot | A100 Spot |
|------|--------------|-----------------|---------|-----------|
| Initial | $150 | $1,200 | $0.18 | $0.07 |
| Monthly | $60 | $480 | $153 | $730 |
| **Year 1** | **$870** | **$6,960** | **$1,837** | **$8,761** |
| **Year 2** | **$720** | **$5,760** | **$1,836** | **$8,760** |
| **3-Year Total** | **$2,310** | **$18,480** | **$5,509** | **$26,281** |

**Winner:** OpenAI Batch API
**Alternative:** L4 Spot if building ML infrastructure

### 10,000 Libraries

**Monthly Update Tokens:** 12B

| Item | OpenAI Batch | Vertex AI Batch | L4 Spot | A100 Spot |
|------|--------------|-----------------|---------|-----------|
| Initial | $300 | $2,400 | $0.36 | $0.14 |
| Monthly | $120 | $960 | $153 | $730 |
| **Year 1** | **$1,740** | **$13,920** | **$1,837** | **$8,761** |
| **Year 2** | **$1,440** | **$11,520** | **$1,836** | **$8,760** |
| **3-Year Total** | **$4,620** | **$36,960** | **$5,509** | **$26,281** |

**Crossover Point:** L4 Spot becomes more cost-effective in Year 2
**Winner (Year 1):** OpenAI Batch
**Winner (3-Year):** L4 Spot

### 20,000 Libraries

**Monthly Update Tokens:** 24B

| Item | OpenAI Batch | Vertex AI Batch | L4 Spot | A100 Spot |
|------|--------------|-----------------|---------|-----------|
| Initial | $600 | $4,800 | $0.72 | $0.28 |
| Monthly | $240 | $1,920 | $153 | $730 |
| **Year 1** | **$3,480** | **$27,840** | **$1,837** | **$8,761** |
| **Year 2** | **$2,880** | **$23,040** | **$1,836** | **$8,760** |
| **3-Year Total** | **$9,240** | **$73,920** | **$5,509** | **$26,281** |

**Winner:** L4 Spot (40% cheaper than OpenAI in Year 1)

### 33,000 Libraries

**Total Tokens:** 99B
**Monthly Update Tokens:** 39.6B

| Item | OpenAI Batch | Vertex AI Batch | L4 Spot | A100 Spot |
|------|--------------|-----------------|---------|-----------|
| Initial | $990 | $7,920 | $1.20 | $0.46 |
| Monthly | $396 | $3,168 | $153 | $730 |
| **Year 1** | **$5,742** | **$46,016** | **$1,837** | **$8,761** |
| **Year 2** | **$4,752** | **$38,016** | **$1,836** | **$8,760** |
| **3-Year Total** | **$15,246** | **$122,048** | **$5,509** | **$26,281** |

**Winner:** L4 Spot (68% cheaper than OpenAI)
**Alternative:** A100 Spot for faster processing (still 43% cheaper than OpenAI)

### 50,000 Libraries

**Monthly Update Tokens:** 60B

| Item | OpenAI Batch | L4 Spot | A100 Spot |
|------|--------------|---------|-----------|
| Initial | $1,500 | $1.80 | $0.70 |
| Monthly | $600 | $153 | $730 |
| **Year 1** | **$8,700** | **$1,837** | **$8,761** |

**Processing Time per Weekly Update (12M chunks):**
- L4: 25 minutes (acceptable)
- A100: 6.7 minutes (better)

**Winner:** L4 Spot if processing time acceptable, otherwise A100 Spot
Both are 79-90% cheaper than OpenAI at this scale

---

## Advanced Scenarios

### Scenario 1: Multiple Embedding Models

**Use Case:** Different embedding models for different content types

**Example:**
- Code: text-embedding-3-large (higher quality for code)
- Documentation: bge-base-en-v1.5 (cost-effective)
- API references: all-MiniLM-L6-v2 (fast, lightweight)

**Cost Impact (5,000 libraries):**
- 30% code (OpenAI 3-large): $390/month
- 70% docs (self-hosted): $153/month
- **Total: $543/month**
- vs OpenAI all: $780/month (using 3-large)
- vs Self-hosted all: $153/month

**Verdict:** Adds complexity for marginal benefit. Not recommended unless quality difference is significant.

### Scenario 2: Gradual Migration

**Strategy:** Start with OpenAI, migrate to self-hosted over time

**Timeline:**
- **Months 0-6**: OpenAI Batch API only
- **Months 7-9**: Build self-hosted infrastructure, test with 10% traffic
- **Months 10-12**: Migrate to 50% self-hosted, 50% OpenAI
- **Months 13+**: 100% self-hosted, keep OpenAI as fallback

**Cost (5,000 libraries, Year 1):**
- Months 1-6: $60/mo × 6 = $360
- Months 7-9: $60/mo × 3 + $153/mo × 3 = $639
- Months 10-12: $30/mo × 3 + $153/mo × 3 = $549
- **Year 1 Total: $1,548**
- vs OpenAI only: $870
- vs Self-hosted only: $1,837

**Analysis:** Migration adds cost in Year 1, but validates approach before full commitment.

### Scenario 3: Multi-Region Deployment

**Requirement:** Serve embeddings from multiple GCP regions

**Option A: OpenAI (Global)**
- Single API endpoint
- No additional infrastructure
- Cost: Same as single-region

**Option B: Self-Hosted (Multi-Region)**
- L4 instance per region: $153/month × 3 regions = $459/month
- Or: Centralized with higher latency

**Break-Even:** 38,000 libraries ($459 L4 multi-region = $459 OpenAI)

**Recommendation:** Use OpenAI for multi-region until 10K+ libraries per region

### Scenario 4: Burst Capacity

**Use Case:** Index 10,000 new libraries quickly (one-time event)

**OpenAI Batch API:**
- Cost: $300 one-time
- Time: 24 hours (batch SLA)
- Capacity: Unlimited

**Self-Hosted L4:**
- Cost: $0.70/hour × processing time
- Processing time: 10K × 1,500 / 8,000 = 1,875 seconds = 31 minutes
- Cost: $0.36
- Can complete immediately

**Self-Hosted A100 Spot:**
- Processing time: 8.3 minutes
- Cost: $1.00/hour × 0.138 hours = $0.14

**Winner:** Self-hosted for burst capacity (if infrastructure exists)

---

## Decision Matrix

### Choose OpenAI Batch API If:

- [ ] You have <5,000 libraries
- [ ] Simplicity and low operational overhead are priorities
- [ ] You don't have ML infrastructure team
- [ ] Monthly embedding costs are <$100
- [ ] You want latest/best embedding models
- [ ] Fast time-to-market is critical
- [ ] You're okay with external dependencies

### Choose Self-Hosted L4 Spot If:

- [ ] You have 5,000+ libraries (or growing there)
- [ ] Monthly OpenAI costs exceed $150
- [ ] You want no external dependencies
- [ ] You have ML/DevOps team
- [ ] Predictable costs matter
- [ ] Data sovereignty is required
- [ ] You're building broader ML platform

### Choose Self-Hosted A100 Spot If:

- [ ] You have 50,000+ libraries
- [ ] Processing time is critical
- [ ] L4 can't handle throughput
- [ ] You run other GPU workloads (shared infrastructure)
- [ ] Budget allows ($730/month)

### Choose Vertex AI Batch If:

- [ ] Regulatory requirements mandate GCP-native
- [ ] Enterprise support is critical
- [ ] Cost is not a concern
- [ ] GCP lock-in is acceptable

**Note:** Vertex AI is rarely the best choice due to 8× cost premium over OpenAI.

---

## Monthly Cost Quick Calculator

```python
def calculate_monthly_cost(libraries: int):
    """Calculate monthly embedding costs."""

    # OpenAI Batch API (text-embedding-3-small)
    openai_cost = libraries * 0.012

    # Vertex AI Batch (textembedding-gecko)
    vertex_cost = libraries * 0.096

    # Self-hosted (fixed costs)
    l4_spot_cost = 153
    a100_spot_cost = 730

    return {
        'OpenAI Batch': f'${openai_cost:.2f}',
        'Vertex AI Batch': f'${vertex_cost:.2f}',
        'L4 Spot': f'${l4_spot_cost}',
        'A100 Spot': f'${a100_spot_cost}',
        'Recommended': 'OpenAI' if openai_cost < l4_spot_cost else 'L4 Spot'
    }

# Examples
print(calculate_monthly_cost(500))    # OpenAI: $6
print(calculate_monthly_cost(5000))   # OpenAI: $60
print(calculate_monthly_cost(10000))  # L4 Spot: $153
print(calculate_monthly_cost(33000))  # L4 Spot: $153
```

---

## Summary Recommendations

| Scale | Recommended Approach | Monthly Cost | 3-Year TCO |
|-------|---------------------|--------------|------------|
| **100-1,000 libs** | OpenAI Batch API | $1-12 | $87-462 |
| **1,000-5,000 libs** | OpenAI Batch API | $12-60 | $462-2,310 |
| **5,000-10,000 libs** | OpenAI Batch API* | $60-120 | $2,310-4,620 |
| **10,000-20,000 libs** | Self-Hosted L4 Spot | $153 | $5,509 |
| **20,000-50,000 libs** | Self-Hosted L4 Spot | $153 | $5,509 |
| **50,000+ libs** | Self-Hosted A100 Spot | $730 | $26,281 |

*Consider self-hosted if building ML platform

**Key Insight:** Self-hosted becomes cost-effective around 8,000-10,000 libraries, but many organizations stay with OpenAI until 15,000+ due to operational simplicity.

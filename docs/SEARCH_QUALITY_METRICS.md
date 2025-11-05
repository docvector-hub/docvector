# Search Quality Metrics & Evaluation

## Overview

This document defines how to measure the correctness and quality of search results in DocVector. Search quality is critical for user satisfaction and must be continuously monitored.

## Key Question: "How do we know the search is working correctly?"

### The Challenge

Unlike traditional software where correctness is binary (works/doesn't work), search quality is continuous and subjective:
- Is result #1 better than result #2?
- Did we miss relevant documents?
- Are low-ranking results truly less relevant?

### Solution: Multi-Metric Evaluation Framework

We use a combination of:
1. **Offline metrics** (automated, dataset-based)
2. **Online metrics** (production, user-driven)
3. **Human evaluation** (gold standard, expensive)

## 1. Offline Evaluation Metrics

### A. Relevance Metrics

#### Precision @ K

**Definition**: Proportion of relevant results in top-K.

```python
def precision_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """
    Precision@K measures what percentage of top-K results are relevant.

    Args:
        retrieved: List of retrieved document IDs (ranked)
        relevant: Set of relevant document IDs (ground truth)
        k: Number of top results to consider

    Returns:
        Precision score [0, 1]

    Example:
        retrieved = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
        relevant = {'doc1', 'doc3', 'doc5', 'doc7'}
        precision_at_k(retrieved, relevant, 5) = 3/5 = 0.6
    """
    if k == 0:
        return 0.0

    top_k = retrieved[:k]
    relevant_in_top_k = sum(1 for doc in top_k if doc in relevant)

    return relevant_in_top_k / k

# Usage
scores = []
for query, results, ground_truth in eval_dataset:
    p_at_5 = precision_at_k(results, ground_truth, k=5)
    scores.append(p_at_5)

avg_precision_at_5 = np.mean(scores)
print(f"Precision@5: {avg_precision_at_5:.3f}")

# Target: P@5 > 0.80 (80% of top-5 results are relevant)
```

#### Recall @ K

**Definition**: Proportion of relevant documents found in top-K.

```python
def recall_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """
    Recall@K measures what percentage of relevant docs are in top-K.

    Example:
        retrieved = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
        relevant = {'doc1', 'doc3', 'doc5', 'doc7'}  # 4 relevant total
        recall_at_k(retrieved, relevant, 5) = 3/4 = 0.75
    """
    if len(relevant) == 0:
        return 1.0

    top_k = retrieved[:k]
    relevant_in_top_k = sum(1 for doc in top_k if doc in relevant)

    return relevant_in_top_k / len(relevant)

# Target: R@10 > 0.90 (find 90% of relevant docs in top-10)
```

#### F1 Score @ K

**Definition**: Harmonic mean of precision and recall.

```python
def f1_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
    """
    F1@K balances precision and recall.
    """
    p = precision_at_k(retrieved, relevant, k)
    r = recall_at_k(retrieved, relevant, k)

    if p + r == 0:
        return 0.0

    return 2 * (p * r) / (p + r)

# Target: F1@5 > 0.75
```

#### Mean Average Precision (MAP)

**Definition**: Average of precision values at each relevant result position.

```python
def average_precision(retrieved: List[str], relevant: Set[str]) -> float:
    """
    Average Precision for a single query.

    Example:
        retrieved = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
        relevant = {'doc1', 'doc3', 'doc5'}

        Relevant at positions: 1, 3, 5
        P@1 = 1/1 = 1.0
        P@3 = 2/3 = 0.667
        P@5 = 3/5 = 0.6
        AP = (1.0 + 0.667 + 0.6) / 3 = 0.756
    """
    if len(relevant) == 0:
        return 0.0

    precisions = []
    relevant_count = 0

    for i, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant:
            relevant_count += 1
            precision = relevant_count / i
            precisions.append(precision)

    if not precisions:
        return 0.0

    return np.mean(precisions)

def mean_average_precision(queries: List[Tuple]) -> float:
    """
    MAP across all queries.
    """
    aps = []
    for retrieved, relevant in queries:
        ap = average_precision(retrieved, relevant)
        aps.append(ap)

    return np.mean(aps)

# Target: MAP > 0.70
```

#### Normalized Discounted Cumulative Gain (nDCG)

**Definition**: Ranking quality metric that considers position and relevance grades.

```python
def dcg_at_k(relevances: List[float], k: int) -> float:
    """
    Discounted Cumulative Gain.

    Args:
        relevances: List of relevance scores (e.g., [3, 2, 3, 0, 1])
        k: Number of results to consider

    Formula: DCG = Σ(rel_i / log2(i + 1))
    """
    dcg = 0.0
    for i, rel in enumerate(relevances[:k], start=1):
        dcg += rel / np.log2(i + 1)

    return dcg

def ndcg_at_k(retrieved: List[str], relevance_scores: Dict[str, float], k: int) -> float:
    """
    Normalized DCG - compares actual ranking to ideal ranking.

    Args:
        retrieved: List of retrieved document IDs
        relevance_scores: Dict mapping doc_id to relevance score (0-3)
        k: Number of results to consider

    Returns:
        nDCG score [0, 1]

    Example:
        retrieved = ['doc1', 'doc2', 'doc3']
        relevance_scores = {'doc1': 3, 'doc2': 1, 'doc3': 2}

        Actual relevances: [3, 1, 2]
        Ideal relevances:  [3, 2, 1] (sorted descending)

        DCG(actual) = 3/1 + 1/1.58 + 2/2 = 4.63
        DCG(ideal) = 3/1 + 2/1.58 + 1/2 = 4.77
        nDCG = 4.63 / 4.77 = 0.97
    """
    # Get relevances for retrieved docs
    relevances = [relevance_scores.get(doc_id, 0.0) for doc_id in retrieved[:k]]

    # Calculate DCG for actual ranking
    dcg = dcg_at_k(relevances, k)

    # Calculate ideal DCG (best possible ranking)
    ideal_relevances = sorted(relevance_scores.values(), reverse=True)
    idcg = dcg_at_k(ideal_relevances, k)

    if idcg == 0:
        return 0.0

    return dcg / idcg

# Relevance scale:
# 0 = Not relevant
# 1 = Somewhat relevant
# 2 = Relevant
# 3 = Highly relevant

# Target: nDCG@10 > 0.80
```

#### Mean Reciprocal Rank (MRR)

**Definition**: Average of reciprocal rank of first relevant result.

```python
def reciprocal_rank(retrieved: List[str], relevant: Set[str]) -> float:
    """
    Reciprocal rank of first relevant result.

    Example:
        retrieved = ['doc1', 'doc2', 'doc3']
        relevant = {'doc3'}
        First relevant at position 3 → RR = 1/3 = 0.333
    """
    for i, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant:
            return 1.0 / i

    return 0.0

def mean_reciprocal_rank(queries: List[Tuple]) -> float:
    """
    MRR across all queries.
    """
    rrs = []
    for retrieved, relevant in queries:
        rr = reciprocal_rank(retrieved, relevant)
        rrs.append(rr)

    return np.mean(rrs)

# Interpretation:
# MRR = 1.0: First result always relevant
# MRR = 0.5: Relevant result typically at position 2
# MRR = 0.1: Relevant result typically at position 10

# Target: MRR > 0.70 (relevant result in top 2 on average)
```

### B. Ranking Quality Metrics

#### Kendall's Tau

**Definition**: Measures correlation between predicted and ideal ranking.

```python
from scipy.stats import kendalltau

def ranking_correlation(retrieved: List[str], ideal_ranking: List[str]) -> float:
    """
    Measures how well the ranking matches ideal ordering.

    Returns:
        Correlation coefficient [-1, 1]
        1 = perfect agreement
        0 = no correlation
        -1 = opposite ranking
    """
    # Create ranking positions
    retrieved_ranks = {doc: i for i, doc in enumerate(retrieved)}
    ideal_ranks = {doc: i for i, doc in enumerate(ideal_ranking)}

    # Get common documents
    common_docs = set(retrieved_ranks.keys()) & set(ideal_ranks.keys())

    if len(common_docs) < 2:
        return 0.0

    # Compare rankings
    x = [retrieved_ranks[doc] for doc in common_docs]
    y = [ideal_ranks[doc] for doc in common_docs]

    tau, _ = kendalltau(x, y)
    return tau

# Target: τ > 0.7
```

### C. Embedding Quality Metrics

#### Embedding Similarity Distribution

```python
def analyze_embedding_quality(embeddings: np.ndarray, labels: List[str]):
    """
    Analyze embedding space quality.

    Metrics:
    1. Intra-class similarity (should be high)
    2. Inter-class similarity (should be low)
    3. Embedding space coverage
    """
    from sklearn.metrics.pairwise import cosine_similarity

    # Group embeddings by label/source
    label_groups = {}
    for emb, label in zip(embeddings, labels):
        if label not in label_groups:
            label_groups[label] = []
        label_groups[label].append(emb)

    # Calculate intra-class similarity
    intra_similarities = []
    for label, embs in label_groups.items():
        if len(embs) > 1:
            emb_matrix = np.array(embs)
            sims = cosine_similarity(emb_matrix)
            # Average similarity within group (excluding self-similarity)
            mask = ~np.eye(len(embs), dtype=bool)
            intra_sim = sims[mask].mean()
            intra_similarities.append(intra_sim)

    # Calculate inter-class similarity
    inter_similarities = []
    labels_list = list(label_groups.keys())
    for i in range(len(labels_list)):
        for j in range(i + 1, len(labels_list)):
            embs1 = np.array(label_groups[labels_list[i]])
            embs2 = np.array(label_groups[labels_list[j]])
            sims = cosine_similarity(embs1, embs2)
            inter_sim = sims.mean()
            inter_similarities.append(inter_sim)

    return {
        'intra_class_similarity': np.mean(intra_similarities),  # Target: >0.7
        'inter_class_similarity': np.mean(inter_similarities),  # Target: <0.5
        'separation': np.mean(intra_similarities) - np.mean(inter_similarities)  # Target: >0.3
    }
```

#### Embedding Stability

```python
def embedding_stability(texts: List[str], model, n_runs=5) -> float:
    """
    Measure consistency of embeddings across multiple runs.

    A stable model should produce nearly identical embeddings.
    """
    all_embeddings = []

    for _ in range(n_runs):
        embeddings = model.encode(texts)
        all_embeddings.append(embeddings)

    # Calculate variance across runs
    embedding_stack = np.stack(all_embeddings)
    variances = np.var(embedding_stack, axis=0)
    avg_variance = np.mean(variances)

    # Convert to stability score
    stability = 1.0 - min(avg_variance, 1.0)

    return stability  # Target: >0.99
```

## 2. Online Evaluation Metrics

### A. User Engagement Metrics

```python
class SearchMetrics:
    """Track real-world search performance"""

    @staticmethod
    async def track_search_event(query: str, results: List[Result], user_actions: dict):
        """
        Track user interactions with search results.
        """
        metrics = {
            # Basic metrics
            'query': query,
            'timestamp': datetime.utcnow(),
            'results_count': len(results),

            # Engagement metrics
            'clicked_positions': user_actions.get('clicks', []),
            'time_to_first_click': user_actions.get('ttfc'),
            'dwell_time': user_actions.get('dwell_time'),

            # Quality indicators
            'no_click': len(user_actions.get('clicks', [])) == 0,
            'abandoned': user_actions.get('abandoned', False),
            'reformulated': user_actions.get('reformulated', False),

            # Result quality
            'top_result_clicked': 1 in user_actions.get('clicks', []),
            'clicked_rank_avg': np.mean(user_actions.get('clicks', [0])),
        }

        await db.save_search_metrics(metrics)
```

#### Click-Through Rate (CTR)

```python
def calculate_ctr(search_logs: List[dict]) -> Dict[int, float]:
    """
    CTR per position (what % of users click result at position N)

    Target:
    - Position 1: CTR > 40%
    - Position 2: CTR > 20%
    - Position 3: CTR > 10%
    """
    clicks_by_position = defaultdict(int)
    impressions_by_position = defaultdict(int)

    for log in search_logs:
        results_count = log['results_count']
        clicked_positions = log.get('clicked_positions', [])

        for pos in range(1, results_count + 1):
            impressions_by_position[pos] += 1
            if pos in clicked_positions:
                clicks_by_position[pos] += 1

    ctr_by_position = {}
    for pos, impressions in impressions_by_position.items():
        ctr = clicks_by_position[pos] / impressions if impressions > 0 else 0
        ctr_by_position[pos] = ctr

    return ctr_by_position
```

#### Zero-Result Rate

```python
def zero_result_rate(search_logs: List[dict]) -> float:
    """
    Percentage of queries that return no results.

    Target: <5%
    """
    zero_results = sum(1 for log in search_logs if log['results_count'] == 0)
    total = len(search_logs)

    return zero_results / total if total > 0 else 0
```

#### Query Reformulation Rate

```python
def reformulation_rate(search_logs: List[dict]) -> float:
    """
    Percentage of queries where user modifies query without clicking.

    High rate indicates poor initial results.

    Target: <30%
    """
    reformulated = sum(1 for log in search_logs if log.get('reformulated', False))
    total = len(search_logs)

    return reformulated / total if total > 0 else 0
```

### B. Latency Metrics

```python
# Track search latency at each stage

class LatencyTracker:
    async def track_search(self, query: str):
        timings = {}

        # 1. Query processing
        start = time.time()
        processed_query = await self.process_query(query)
        timings['query_processing'] = time.time() - start

        # 2. Embedding generation
        start = time.time()
        embedding = await self.generate_embedding(processed_query)
        timings['embedding'] = time.time() - start

        # 3. Vector search
        start = time.time()
        vector_results = await self.vector_search(embedding)
        timings['vector_search'] = time.time() - start

        # 4. Metadata enrichment
        start = time.time()
        enriched = await self.enrich_results(vector_results)
        timings['enrichment'] = time.time() - start

        # 5. Ranking/reranking
        start = time.time()
        ranked = await self.rank_results(enriched)
        timings['ranking'] = time.time() - start

        timings['total'] = sum(timings.values())

        # Log for analysis
        await self.log_timings(timings)

        return ranked, timings

# Targets:
# - query_processing: <5ms
# - embedding: <50ms (with cache: <5ms)
# - vector_search: <30ms
# - enrichment: <20ms
# - ranking: <10ms
# - total: <100ms (p95)
```

## 3. Ground Truth Dataset Creation

### A. Building Evaluation Dataset

```python
class EvaluationDatasetBuilder:
    """
    Create labeled test set for evaluation.

    Dataset format:
    {
        "query": "how to authenticate users",
        "relevant_docs": ["doc1", "doc3", "doc5"],
        "relevance_scores": {
            "doc1": 3,  # Highly relevant
            "doc2": 0,  # Not relevant
            "doc3": 2,  # Relevant
            "doc4": 1,  # Somewhat relevant
            "doc5": 3   # Highly relevant
        }
    }
    """

    @staticmethod
    def create_from_user_clicks(search_logs: List[dict], min_clicks=5):
        """
        Infer relevance from click data.

        Assumptions:
        - Clicked results are relevant
        - Higher position clicks are stronger signals
        - Dwell time indicates relevance
        """
        query_data = defaultdict(lambda: defaultdict(float))

        for log in search_logs:
            query = log['query']
            clicks = log.get('clicked_positions', [])
            dwell_times = log.get('dwell_times', {})

            for pos in clicks:
                doc_id = log['results'][pos - 1]['id']

                # Score based on position (earlier = better signal)
                position_score = 1.0 / pos

                # Score based on dwell time
                dwell_time = dwell_times.get(pos, 0)
                dwell_score = min(dwell_time / 30.0, 1.0)  # 30s = max

                # Combined score
                relevance = position_score * 0.5 + dwell_score * 0.5
                query_data[query][doc_id] += relevance

        # Convert to evaluation format
        eval_dataset = []
        for query, doc_scores in query_data.items():
            if len(doc_scores) >= min_clicks:
                # Normalize scores to 0-3 scale
                max_score = max(doc_scores.values())
                relevance_scores = {
                    doc_id: int(score / max_score * 3)
                    for doc_id, score in doc_scores.items()
                }

                relevant_docs = [
                    doc_id for doc_id, score in relevance_scores.items()
                    if score >= 2
                ]

                eval_dataset.append({
                    'query': query,
                    'relevant_docs': relevant_docs,
                    'relevance_scores': relevance_scores
                })

        return eval_dataset

    @staticmethod
    def create_synthetic_dataset(documents: List[Document], n_queries=100):
        """
        Generate synthetic queries from documents.

        Useful for initial evaluation before user data is available.
        """
        from transformers import pipeline

        # Use T5 or GPT to generate questions from content
        qa_generator = pipeline("question-generation")

        eval_dataset = []

        for doc in random.sample(documents, min(n_queries, len(documents))):
            # Generate question from document content
            questions = qa_generator(doc.content[:500])

            for q in questions[:2]:  # 2 questions per document
                eval_dataset.append({
                    'query': q['question'],
                    'relevant_docs': [doc.id],
                    'relevance_scores': {doc.id: 3}
                })

        return eval_dataset
```

### B. Human Labeling Interface

```python
@app.get("/admin/evaluate")
async def evaluation_interface():
    """
    Web interface for human evaluation.

    Show evaluator:
    1. Query
    2. Top 10 search results
    3. Rate relevance (0-3) for each result

    Collect data for:
    - Ground truth creation
    - Inter-annotator agreement
    - Model evaluation
    """
    return {
        "query": "...",
        "results": [...],
        "instructions": "Rate each result: 0=Not relevant, 1=Somewhat, 2=Relevant, 3=Highly relevant"
    }
```

## 4. A/B Testing Framework

```python
class ABTestingFramework:
    """
    Compare two search algorithms/models in production.
    """

    async def run_search(self, query: str, user_id: str):
        # Assign user to variant (50/50 split)
        variant = self.get_variant(user_id)

        if variant == 'A':
            # Control: current algorithm
            results = await self.search_v1(query)
        else:
            # Treatment: new algorithm
            results = await self.search_v2(query)

        # Track which variant was used
        await self.track_variant(user_id, query, variant)

        return results

    async def analyze_results(self, days=7):
        """
        Compare metrics between variants.
        """
        metrics_a = await self.get_metrics('A', days)
        metrics_b = await self.get_metrics('B', days)

        comparison = {
            'ctr': {
                'A': metrics_a['ctr'],
                'B': metrics_b['ctr'],
                'improvement': (metrics_b['ctr'] - metrics_a['ctr']) / metrics_a['ctr']
            },
            'avg_click_position': {
                'A': metrics_a['avg_click_position'],
                'B': metrics_b['avg_click_position'],
                'improvement': (metrics_a['avg_click_position'] - metrics_b['avg_click_position']) / metrics_a['avg_click_position']
            },
            'zero_results_rate': {
                'A': metrics_a['zero_results_rate'],
                'B': metrics_b['zero_results_rate'],
                'improvement': (metrics_a['zero_results_rate'] - metrics_b['zero_results_rate']) / metrics_a['zero_results_rate']
            }
        }

        # Statistical significance testing
        from scipy.stats import ttest_ind
        _, p_value = ttest_ind(metrics_a['clicks'], metrics_b['clicks'])

        comparison['statistical_significance'] = p_value < 0.05

        return comparison
```

## 5. Automated Quality Monitoring

```python
class QualityMonitor:
    """
    Continuously monitor search quality in production.
    """

    async def run_daily_evaluation(self):
        """
        Run automated evaluation every day.
        """
        # 1. Get evaluation dataset
        eval_dataset = await self.load_evaluation_dataset()

        # 2. Run queries
        results = []
        for item in eval_dataset:
            query = item['query']
            relevant_docs = item['relevant_docs']
            relevance_scores = item['relevance_scores']

            # Execute search
            search_results = await self.search(query, limit=10)
            retrieved = [r.doc_id for r in search_results]

            # Calculate metrics
            metrics = {
                'precision_at_5': precision_at_k(retrieved, set(relevant_docs), 5),
                'recall_at_10': recall_at_k(retrieved, set(relevant_docs), 10),
                'ndcg_at_10': ndcg_at_k(retrieved, relevance_scores, 10),
                'mrr': reciprocal_rank(retrieved, set(relevant_docs))
            }

            results.append(metrics)

        # 3. Aggregate metrics
        avg_metrics = {
            metric: np.mean([r[metric] for r in results])
            for metric in results[0].keys()
        }

        # 4. Alert if quality drops
        await self.check_quality_thresholds(avg_metrics)

        # 5. Log for tracking
        await self.log_daily_metrics(avg_metrics)

        return avg_metrics

    async def check_quality_thresholds(self, metrics: dict):
        """
        Alert if metrics fall below thresholds.
        """
        thresholds = {
            'precision_at_5': 0.70,
            'recall_at_10': 0.85,
            'ndcg_at_10': 0.75,
            'mrr': 0.65
        }

        alerts = []
        for metric, value in metrics.items():
            if value < thresholds[metric]:
                alerts.append(f"{metric}: {value:.3f} (threshold: {thresholds[metric]})")

        if alerts:
            await self.send_alert(
                f"Search quality degradation detected:\n" + "\n".join(alerts)
            )
```

## 6. Quality Improvement Workflow

### Continuous Improvement Process

```
1. Monitor Metrics (Automated)
   ├─ Daily evaluation runs
   ├─ Production metrics tracked
   └─ Quality dashboard updated

2. Identify Issues (Automated + Manual)
   ├─ Metrics below threshold → Alert
   ├─ User complaints → Investigation
   └─ Unusual patterns → Analysis

3. Root Cause Analysis (Manual)
   ├─ Review failed queries
   ├─ Analyze embedding quality
   ├─ Check ranking correlation
   └─ Inspect edge cases

4. Implement Fix
   ├─ Update embedding model
   ├─ Adjust chunking strategy
   ├─ Tune ranking parameters
   ├─ Improve query processing
   └─ Add domain-specific rules

5. A/B Test (Automated)
   ├─ Deploy to 10% of traffic
   ├─ Monitor for 7 days
   ├─ Compare metrics
   └─ Statistical significance check

6. Roll Out (Conditional)
   ├─ If metrics improve → Full rollout
   ├─ If metrics neutral → Keep or rollback
   └─ If metrics degrade → Rollback immediately
```

## 7. Metrics Dashboard

```python
# Grafana dashboard config (JSON)

dashboard = {
    "title": "Search Quality Metrics",
    "panels": [
        {
            "title": "Precision@5 (Daily)",
            "target": "avg(precision_at_5)",
            "threshold": 0.70,
            "alert": "< 0.70"
        },
        {
            "title": "Search Latency (p95)",
            "target": "histogram_quantile(0.95, search_latency_seconds)",
            "threshold": 0.1,  # 100ms
            "alert": "> 0.15"
        },
        {
            "title": "Cache Hit Rate",
            "target": "cache_hits / (cache_hits + cache_misses)",
            "threshold": 0.80,
            "alert": "< 0.70"
        },
        {
            "title": "Zero Results Rate",
            "target": "zero_results / total_searches",
            "threshold": 0.05,
            "alert": "> 0.10"
        },
        {
            "title": "Click-Through Rate",
            "target": "clicks / impressions",
            "threshold": 0.30,
            "alert": "< 0.20"
        }
    ]
}
```

## Summary: Measuring Correctness

### Offline Metrics (Automated, Pre-Production)
- ✅ **Precision@5**: >0.70 (70% of top-5 are relevant)
- ✅ **Recall@10**: >0.85 (find 85% of relevant docs)
- ✅ **nDCG@10**: >0.75 (ranking quality)
- ✅ **MRR**: >0.65 (first relevant result in top 2)

### Online Metrics (Production, User-Driven)
- ✅ **CTR (Position 1)**: >0.40 (40% click top result)
- ✅ **Zero Results**: <0.05 (5% no results)
- ✅ **Reformulation Rate**: <0.30 (30% modify query)
- ✅ **Search Latency (p95)**: <100ms

### Embedding Quality
- ✅ **Intra-class similarity**: >0.70
- ✅ **Inter-class similarity**: <0.50
- ✅ **Stability**: >0.99

### Monitoring Frequency
- **Real-time**: Latency, error rates
- **Hourly**: CTR, zero results
- **Daily**: Precision, recall, nDCG
- **Weekly**: A/B test analysis

### Action Triggers
- Any metric >20% degradation → Immediate investigation
- Any metric >10% degradation → Scheduled review
- Continuous improvement → Monthly A/B tests

## Conclusion

Measuring search quality requires:
1. **Multiple metrics** (no single metric is sufficient)
2. **Both offline and online** evaluation
3. **Continuous monitoring** (automated dashboards)
4. **Human evaluation** (ground truth datasets)
5. **A/B testing** (validate improvements)
6. **Rapid iteration** (fix issues quickly)

With this framework, you can confidently answer: **"Is our search working correctly?"** with data-driven evidence.

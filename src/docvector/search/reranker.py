"""Multi-stage reranking system for search results."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RankedResult:
    """A search result with reranking scores."""

    id: str
    content: str
    vector_score: float
    relevance_score: float = 0.0
    code_quality_score: float = 0.0
    formatting_score: float = 0.0
    metadata_score: float = 0.0
    initialization_score: float = 0.0
    final_score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class MultiStageReranker:
    """
    Context7-style multi-stage reranker with 5 scoring metrics.

    Metrics:
    1. Relevance Score - How well the content matches the query
    2. Code Quality Score - Quality of code snippets (if present)
    3. Formatting Score - Readability and formatting
    4. Metadata Score - Richness of metadata
    5. Initialization Score - How helpful for getting started
    """

    def __init__(
        self,
        relevance_weight: float = 0.35,
        code_quality_weight: float = 0.25,
        formatting_weight: float = 0.15,
        metadata_weight: float = 0.10,
        initialization_weight: float = 0.15,
    ):
        """
        Initialize the reranker with custom weights.

        Args:
            relevance_weight: Weight for relevance score
            code_quality_weight: Weight for code quality score
            formatting_weight: Weight for formatting score
            metadata_weight: Weight for metadata score
            initialization_weight: Weight for initialization score
        """
        # Normalize weights to sum to 1.0
        total = (
            relevance_weight
            + code_quality_weight
            + formatting_weight
            + metadata_weight
            + initialization_weight
        )

        self.relevance_weight = relevance_weight / total
        self.code_quality_weight = code_quality_weight / total
        self.formatting_weight = formatting_weight / total
        self.metadata_weight = metadata_weight / total
        self.initialization_weight = initialization_weight / total

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        use_stored_scores: bool = True,
    ) -> List[RankedResult]:
        """
        Rerank search results using multi-stage scoring.

        Args:
            query: The search query
            results: List of search results from vector DB
            use_stored_scores: Whether to use pre-computed scores from DB

        Returns:
            List of RankedResult objects sorted by final score
        """
        ranked = []

        for result in results:
            # Extract existing scores if available
            if use_stored_scores and "metadata" in result:
                metadata = result.get("metadata", {})
                relevance = metadata.get("relevance_score", 0.0)
                code_quality = metadata.get("code_quality_score", 0.0)
                formatting = metadata.get("formatting_score", 0.0)
                metadata_score = metadata.get("metadata_score", 0.0)
                initialization = metadata.get("initialization_score", 0.0)
            else:
                # Compute scores on the fly
                content = result.get("content", "")
                relevance = self._compute_relevance_score(query, content)
                code_quality = self._compute_code_quality_score(content)
                formatting = self._compute_formatting_score(content)
                metadata_score = self._compute_metadata_score(result)
                initialization = self._compute_initialization_score(content, query)

            # Combine scores with weights
            final_score = (
                relevance * self.relevance_weight
                + code_quality * self.code_quality_weight
                + formatting * self.formatting_weight
                + metadata_score * self.metadata_weight
                + initialization * self.initialization_weight
            )

            # Also factor in original vector similarity score
            vector_score = result.get("score", 0.0)
            # Blend vector score with reranked score (70% reranked, 30% vector)
            final_score = 0.7 * final_score + 0.3 * vector_score

            ranked_result = RankedResult(
                id=result.get("id", ""),
                content=result.get("content", ""),
                vector_score=vector_score,
                relevance_score=relevance,
                code_quality_score=code_quality,
                formatting_score=formatting,
                metadata_score=metadata_score,
                initialization_score=initialization,
                final_score=final_score,
                metadata=result.get("metadata"),
            )

            ranked.append(ranked_result)

        # Sort by final score descending
        ranked.sort(key=lambda x: x.final_score, reverse=True)

        return ranked

    def _compute_relevance_score(self, query: str, content: str) -> float:
        """
        Compute relevance score based on query-content match.

        Args:
            query: Search query
            content: Result content

        Returns:
            Relevance score (0-1)
        """
        query_lower = query.lower()
        content_lower = content.lower()

        score = 0.0

        # Exact phrase match
        if query_lower in content_lower:
            score += 0.4

        # Word overlap
        query_words = set(re.findall(r'\w+', query_lower))
        content_words = set(re.findall(r'\w+', content_lower))

        if query_words:
            overlap = len(query_words & content_words) / len(query_words)
            score += 0.3 * overlap

        # Term frequency
        query_terms = query_lower.split()
        for term in query_terms:
            if len(term) < 3:  # Skip very short terms
                continue
            count = content_lower.count(term)
            if count > 0:
                # Logarithmic scoring for term frequency
                score += min(0.1 * (count / 10), 0.3)

        return min(score, 1.0)

    def _compute_code_quality_score(self, content: str) -> float:
        """
        Compute code quality score.

        Args:
            content: Content to analyze

        Returns:
            Code quality score (0-1)
        """
        # Check if content contains code
        has_code_block = bool(re.search(r'```|<code>|<pre>', content))
        if not has_code_block and not self._looks_like_code(content):
            return 0.0

        score = 0.0

        # Has imports/requires
        if re.search(
            r'(?:^|\n)(?:import|from|require|include|using)\s+',
            content,
            re.MULTILINE | re.IGNORECASE,
        ):
            score += 0.2

        # Has function definitions
        if re.search(r'(?:^|\n)(?:def|function|fn|func|class|public|private)\s+', content):
            score += 0.2

        # Has comments
        if re.search(r'(?://|#|/\*|\"\"\"|\'\'\')', content):
            score += 0.2

        # Reasonable length
        line_count = len(content.split('\n'))
        if 5 <= line_count <= 50:
            score += 0.2
        elif line_count > 50:
            score += 0.1

        # Has typical code structure
        if re.search(r'[{}\[\]()\;]', content):
            score += 0.2

        return min(score, 1.0)

    def _compute_formatting_score(self, content: str) -> float:
        """
        Compute formatting quality score.

        Args:
            content: Content to analyze

        Returns:
            Formatting score (0-1)
        """
        score = 0.0

        lines = content.split('\n')

        # Not too long, not too short
        if 3 <= len(lines) <= 100:
            score += 0.3

        # Has headings/structure
        if re.search(r'^#{1,6}\s+\w+', content, re.MULTILINE):
            score += 0.2

        # Proper spacing (not wall of text)
        if '\n\n' in content:
            score += 0.2

        # Not excessively long lines
        max_line_length = max(len(line) for line in lines) if lines else 0
        if max_line_length <= 100:
            score += 0.3
        elif max_line_length <= 120:
            score += 0.2

        return min(score, 1.0)

    def _compute_metadata_score(self, result: Dict[str, Any]) -> float:
        """
        Compute metadata richness score.

        Args:
            result: Search result with metadata

        Returns:
            Metadata score (0-1)
        """
        score = 0.0
        metadata = result.get("metadata", {})

        # Has title
        if metadata.get("title"):
            score += 0.2

        # Has language info
        if metadata.get("language") or metadata.get("code_language"):
            score += 0.2

        # Has topics
        topics = metadata.get("topics", [])
        if topics:
            score += 0.3

        # Has enrichment/explanation
        if metadata.get("enrichment"):
            score += 0.3

        return min(score, 1.0)

    def _compute_initialization_score(self, content: str, query: str) -> float:
        """
        Compute initialization/getting-started score.

        Args:
            content: Content to analyze
            query: Original query

        Returns:
            Initialization score (0-1)
        """
        score = 0.0

        # Query suggests getting started
        query_lower = query.lower()
        getting_started_terms = [
            'install',
            'setup',
            'start',
            'begin',
            'initialize',
            'init',
            'example',
            'basic',
            'simple',
            'quick',
            'tutorial',
        ]

        for term in getting_started_terms:
            if term in query_lower:
                score += 0.2
                break

        # Content has initialization keywords
        content_lower = content.lower()
        init_keywords = [
            'install',
            'setup',
            'initialize',
            'getting started',
            'quick start',
            'example',
            'usage',
        ]

        for keyword in init_keywords:
            if keyword in content_lower:
                score += 0.2
                break

        # Has main/entry point
        if re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]', content):
            score += 0.2

        # Has basic instantiation
        if re.search(r'new\s+\w+|=\s*\w+\(', content):
            score += 0.2

        # Has import statements (common in getting started)
        if re.search(r'(?:^|\n)(?:import|from|require)\s+', content, re.MULTILINE):
            score += 0.2

        return min(score, 1.0)

    def _looks_like_code(self, content: str) -> bool:
        """
        Heuristic to detect if content looks like code.

        Args:
            content: Content to check

        Returns:
            True if content looks like code
        """
        # Has typical code patterns
        code_indicators = [
            r'[{}\[\]();]',  # Brackets and parens
            r'(?:def|function|class|var|let|const)\s+\w+',  # Declarations
            r'(?:if|for|while|return|import)\s+',  # Keywords
            r'[=<>!+\-*/]+',  # Operators
        ]

        indicator_count = 0
        for pattern in code_indicators:
            if re.search(pattern, content):
                indicator_count += 1

        return indicator_count >= 2

"""Tests for search functionality."""

import pytest

from docvector.search import HybridSearch, VectorSearch
from docvector.search.vector_search import SearchResultItem


class TestVectorSearch:
    """Test vector similarity search."""

    @pytest.fixture
    def vector_search(self, mocker, mock_embedder):
        """Create vector search with mocks."""
        mock_vectordb = mocker.AsyncMock()

        # Mock search results
        mock_result = mocker.Mock()
        mock_result.id = "chunk1"
        mock_result.score = 0.95
        mock_result.payload = {
            "chunk_id": "chunk1",
            "document_id": "doc1",
            "content": "test content",
            "title": "Test Title",
            "url": "https://example.com",
        }

        mock_vectordb.search.return_value = [mock_result]

        return VectorSearch(
            vectordb=mock_vectordb,
            embedder=mock_embedder,
            collection_name="test_collection",
        )

    @pytest.mark.asyncio
    async def test_search_basic(self, vector_search, mock_embedder):
        """Test basic search."""
        results = await vector_search.search(
            query="test query",
            limit=10,
        )

        assert len(results) == 1
        assert results[0].chunk_id == "chunk1"
        assert results[0].score == 0.95
        assert results[0].content == "test content"

        # Verify embedder was called
        mock_embedder.embed_query.assert_called_once_with("test query")

    @pytest.mark.asyncio
    async def test_search_with_filters(self, vector_search):
        """Test search with filters."""
        results = await vector_search.search(
            query="test query",
            limit=5,
            filters={"access_level": "public"},
        )

        # Verify vectordb.search was called with filters
        vector_search.vectordb.search.assert_called_once()
        call_args = vector_search.vectordb.search.call_args
        assert call_args[1]["filter"] == {"access_level": "public"}

    @pytest.mark.asyncio
    async def test_search_with_score_threshold(self, vector_search):
        """Test search with score threshold."""
        results = await vector_search.search(
            query="test query",
            limit=10,
            score_threshold=0.8,
        )

        # Verify score_threshold was passed
        call_args = vector_search.vectordb.search.call_args
        assert call_args[1]["score_threshold"] == 0.8

    @pytest.mark.asyncio
    async def test_search_result_item_creation(self, vector_search):
        """Test SearchResultItem creation."""
        results = await vector_search.search("test", limit=1)

        assert isinstance(results[0], SearchResultItem)
        assert results[0].title == "Test Title"
        assert results[0].url == "https://example.com"


class TestHybridSearch:
    """Test hybrid search."""

    @pytest.fixture
    def hybrid_search(self, mocker):
        """Create hybrid search with mocks."""
        mock_vector_search = mocker.AsyncMock()

        # Mock search results
        result_item = SearchResultItem(
            chunk_id="chunk1",
            document_id="doc1",
            score=0.95,
            content="test content",
            title="Test Title",
        )

        mock_vector_search.search.return_value = [result_item]

        return HybridSearch(
            vector_search=mock_vector_search,
            vector_weight=0.7,
            keyword_weight=0.3,
        )

    @pytest.mark.asyncio
    async def test_hybrid_search_basic(self, hybrid_search):
        """Test basic hybrid search."""
        results = await hybrid_search.search(
            query="test query",
            limit=10,
        )

        assert len(results) == 1
        assert results[0].chunk_id == "chunk1"

    @pytest.mark.asyncio
    async def test_hybrid_search_applies_weighting(self, hybrid_search):
        """Test that hybrid search applies score weighting."""
        results = await hybrid_search.search(
            query="test query",
            limit=10,
        )

        # Score should be weighted
        # Original: 0.95, with vector_weight 0.7, should be 0.95 * 0.7
        assert results[0].score == pytest.approx(0.665, rel=0.01)

    @pytest.mark.asyncio
    async def test_hybrid_search_with_filters(self, hybrid_search):
        """Test hybrid search with filters."""
        results = await hybrid_search.search(
            query="test query",
            limit=5,
            filters={"access_level": "private"},
        )

        # Verify filters were passed to vector search
        call_args = hybrid_search.vector_search.search.call_args
        assert call_args[1]["filters"] == {"access_level": "private"}

    @pytest.mark.asyncio
    async def test_hybrid_search_sorts_by_score(self, hybrid_search, mocker):
        """Test that results are sorted by score."""
        # Create multiple results with different scores
        results = [
            SearchResultItem("c1", "d1", 0.5, "content1"),
            SearchResultItem("c2", "d2", 0.9, "content2"),
            SearchResultItem("c3", "d3", 0.7, "content3"),
        ]

        hybrid_search.vector_search.search.return_value = results

        sorted_results = await hybrid_search.search("query", limit=10)

        # Should be sorted by score descending
        scores = [r.score for r in sorted_results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_hybrid_search_respects_limit(self, hybrid_search, mocker):
        """Test that hybrid search respects result limit."""
        # Create many results
        results = [
            SearchResultItem(f"c{i}", f"d{i}", 0.9 - i * 0.1, f"content{i}")
            for i in range(20)
        ]

        hybrid_search.vector_search.search.return_value = results

        limited_results = await hybrid_search.search("query", limit=5)

        assert len(limited_results) == 5

    def test_weight_normalization(self):
        """Test that weights are normalized."""
        # Create with non-normalized weights
        hybrid = HybridSearch(
            vector_search=None,
            vector_weight=2.0,
            keyword_weight=3.0,
        )

        # Should normalize to sum to 1
        assert hybrid.vector_weight == pytest.approx(0.4, rel=0.01)
        assert hybrid.keyword_weight == pytest.approx(0.6, rel=0.01)

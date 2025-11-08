"""Tests for vector database."""

import pytest
from unittest.mock import Mock
from qdrant_client.http.exceptions import UnexpectedResponse

from docvector.vectordb import QdrantVectorDB, SearchResult


class TestSearchResult:
    """Test SearchResult dataclass."""

    def test_create_search_result(self):
        """Test creating a search result."""
        result = SearchResult(
            id="test-id",
            score=0.95,
            payload={"content": "test"},
        )

        assert result.id == "test-id"
        assert result.score == 0.95
        assert result.payload["content"] == "test"

    def test_search_result_repr(self):
        """Test string representation."""
        result = SearchResult(id="test", score=0.85, payload={})
        repr_str = repr(result)

        assert "test" in repr_str
        assert "0.85" in repr_str


class TestQdrantVectorDB:
    """Test Qdrant vector database implementation."""

    @pytest.fixture
    def vectordb(self, mocker, mock_qdrant_client):
        """Create vector DB with mocked client."""
        db = QdrantVectorDB()
        # Patch the client creation
        mocker.patch.object(db, 'client', mock_qdrant_client)
        return db

    @pytest.mark.asyncio
    async def test_initialize(self, vectordb, mock_qdrant_client):
        """Test initialization."""
        await vectordb.initialize()
        # Should initialize client (mocked, so just verify it's set)
        assert vectordb.client is not None

    @pytest.mark.asyncio
    async def test_create_collection(self, vectordb, mock_qdrant_client):
        """Test creating a collection."""
        await vectordb.initialize()
        await vectordb.create_collection(
            collection_name="test_collection",
            vector_size=384,
        )

        mock_qdrant_client.create_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_collection_already_exists(self, vectordb, mock_qdrant_client):
        """Test creating collection that already exists."""
        # Create a mock response object for UnexpectedResponse
        mock_response = Mock()
        mock_response.status_code = 409
        mock_response.reason_phrase = "already exists"
        mock_response.content = b"already exists"
        mock_response.text = "already exists"

        mock_qdrant_client.create_collection.side_effect = UnexpectedResponse(
            status_code=409,
            reason_phrase="already exists",
            content=b"already exists",
            response=mock_response,
        )

        await vectordb.initialize()
        # Should not raise exception
        await vectordb.create_collection("test", 384)

    @pytest.mark.asyncio
    async def test_collection_exists_true(self, vectordb, mock_qdrant_client):
        """Test checking if collection exists (true)."""
        mock_qdrant_client.get_collection.return_value = {"name": "test"}

        await vectordb.initialize()
        exists = await vectordb.collection_exists("test")

        assert exists is True

    @pytest.mark.asyncio
    async def test_collection_exists_false(self, vectordb, mock_qdrant_client):
        """Test checking if collection exists (false)."""
        mock_qdrant_client.get_collection.side_effect = Exception("Not found")

        await vectordb.initialize()
        exists = await vectordb.collection_exists("test")

        assert exists is False

    @pytest.mark.asyncio
    async def test_upsert(self, vectordb, mock_qdrant_client, sample_embeddings):
        """Test upserting vectors."""
        await vectordb.initialize()

        ids = ["id1", "id2", "id3"]
        payloads = [{"content": f"doc{i}"} for i in range(3)]

        await vectordb.upsert(
            collection_name="test",
            ids=ids,
            vectors=sample_embeddings,
            payloads=payloads,
        )

        mock_qdrant_client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_empty(self, vectordb, mock_qdrant_client):
        """Test upserting empty data."""
        await vectordb.initialize()

        await vectordb.upsert(
            collection_name="test",
            ids=[],
            vectors=[],
            payloads=[],
        )

        # Should not call upsert for empty data
        mock_qdrant_client.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_search(self, vectordb, mock_qdrant_client, mocker):
        """Test searching vectors."""
        # Mock search results
        mock_result = mocker.Mock()
        mock_result.id = "result-1"
        mock_result.score = 0.95
        mock_result.payload = {"content": "test"}

        mock_qdrant_client.search.return_value = [mock_result]

        await vectordb.initialize()

        results = await vectordb.search(
            collection_name="test",
            query_vector=[0.1] * 384,
            limit=10,
        )

        assert len(results) == 1
        assert results[0].id == "result-1"
        assert results[0].score == 0.95

    @pytest.mark.asyncio
    async def test_search_with_filter(self, vectordb, mock_qdrant_client):
        """Test searching with filters."""
        mock_qdrant_client.search.return_value = []

        await vectordb.initialize()

        await vectordb.search(
            collection_name="test",
            query_vector=[0.1] * 384,
            limit=10,
            filter={"access_level": "public"},
        )

        # Verify filter was built and passed
        call_args = mock_qdrant_client.search.call_args
        assert call_args[1]["query_filter"] is not None

    @pytest.mark.asyncio
    async def test_delete(self, vectordb, mock_qdrant_client):
        """Test deleting vectors."""
        await vectordb.initialize()

        await vectordb.delete(
            collection_name="test",
            ids=["id1", "id2"],
        )

        mock_qdrant_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_empty(self, vectordb, mock_qdrant_client):
        """Test deleting with empty IDs."""
        await vectordb.initialize()

        await vectordb.delete(
            collection_name="test",
            ids=[],
        )

        # Should not call delete for empty IDs
        mock_qdrant_client.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_get(self, vectordb, mock_qdrant_client, mocker):
        """Test getting vectors by IDs."""
        mock_result = mocker.Mock()
        mock_result.id = "id1"
        mock_result.vector = [0.1] * 384
        mock_result.payload = {"content": "test"}

        mock_qdrant_client.retrieve.return_value = [mock_result]

        await vectordb.initialize()

        results = await vectordb.get(
            collection_name="test",
            ids=["id1"],
        )

        assert len(results) == 1
        assert results[0]["id"] == "id1"

    @pytest.mark.asyncio
    async def test_count(self, vectordb, mock_qdrant_client):
        """Test counting vectors."""
        await vectordb.initialize()

        count = await vectordb.count(collection_name="test")

        assert count == 10  # From mock

    def test_build_filter_simple(self, vectordb):
        """Test building simple filter."""
        filter_dict = {"field": "value"}
        result = vectordb._build_filter(filter_dict)

        assert result.must is not None
        assert len(result.must) == 1

    def test_build_filter_in(self, vectordb):
        """Test building filter with $in operator."""
        filter_dict = {"field": {"$in": ["val1", "val2"]}}
        result = vectordb._build_filter(filter_dict)

        assert result.must is not None

    def test_build_filter_range(self, vectordb):
        """Test building filter with range operators."""
        filter_dict = {"age": {"$gt": 18, "$lt": 65}}
        result = vectordb._build_filter(filter_dict)

        assert result.must is not None
        assert len(result.must) == 2  # Two range conditions

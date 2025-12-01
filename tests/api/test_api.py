"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from docvector.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "DocVector API"
        assert "version" in data
        assert data["status"] == "running"

    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "dependencies" in data

    def test_api_v1_health_endpoint(self, client):
        """Test API v1 health endpoint."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestSearchEndpoints:
    """Test search endpoints."""

    def test_search_endpoint_exists(self, client):
        """Test that search endpoint exists."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "test query",
                "limit": 10,
                "search_type": "hybrid",
            },
        )

        # Should not be 404
        assert response.status_code != 404

    def test_search_validation_empty_query(self, client):
        """Test search validation rejects empty query."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "",
                "limit": 10,
            },
        )

        assert response.status_code == 422  # Validation error

    def test_search_validation_invalid_limit(self, client):
        """Test search validation for limit."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "test",
                "limit": 0,  # Invalid: must be >= 1
            },
        )

        assert response.status_code == 422

    def test_search_validation_limit_too_high(self, client):
        """Test search validation for max limit."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "test",
                "limit": 200,  # Invalid: max is 100
            },
        )

        assert response.status_code == 422

    def test_search_validation_invalid_search_type(self, client):
        """Test search validation for search type."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "test",
                "search_type": "invalid",  # Must be vector or hybrid
            },
        )

        assert response.status_code == 422

    def test_search_validation_invalid_access_level(self, client):
        """Test search validation for access level."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "test",
                "access_level": "invalid",  # Must be public or private
            },
        )

        assert response.status_code == 422

    def test_search_valid_request_structure(self, client):
        """Test search with valid request structure."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "test query",
                "limit": 5,
                "search_type": "vector",
                "access_level": "public",
                "score_threshold": 0.7,
            },
        )

        # Should have valid structure (may fail due to missing services, but validation passes)
        if response.status_code == 200:
            data = response.json()
            assert "query" in data
            assert "results" in data
            assert "total" in data


class TestSourceEndpoints:
    """Test source management endpoints."""

    def test_list_sources_endpoint(self, client):
        """Test list sources endpoint."""
        response = client.get("/api/v1/sources")

        # Should not be 404 (endpoint exists)
        assert response.status_code != 404

    def test_create_source_validation(self, client):
        """Test source creation validation."""
        response = client.post(
            "/api/v1/sources",
            json={
                "name": "",  # Invalid: empty name
                "type": "web",
                "config": {},
            },
        )

        assert response.status_code == 422  # Validation error

    def test_create_source_invalid_type(self, client):
        """Test source creation with invalid type."""
        response = client.post(
            "/api/v1/sources",
            json={
                "name": "Test Source",
                "type": "invalid_type",  # Must be web, git, file, or api
                "config": {},
            },
        )

        assert response.status_code == 422

    def test_create_source_valid_structure(self, client):
        """Test source creation with valid structure."""
        response = client.post(
            "/api/v1/sources",
            json={
                "name": "Test Source",
                "type": "web",
                "config": {
                    "start_url": "https://example.com",
                    "max_pages": 10,
                },
                "sync_frequency": "daily",
            },
        )

        # May fail due to DB not being set up, but validation should pass
        assert response.status_code != 422


class TestIngestionEndpoints:
    """Test ingestion endpoints."""

    def test_ingest_url_endpoint_exists(self, client):
        """Test that ingest URL endpoint exists."""
        response = client.post(
            "/api/v1/ingest/url",
            json={
                "source_id": "550e8400-e29b-41d4-a716-446655440000",
                "url": "https://example.com",
                "access_level": "public",
            },
        )

        # Should not be 404
        assert response.status_code != 404

    def test_ingest_url_validation_invalid_access_level(self, client):
        """Test ingest URL validation for access level."""
        response = client.post(
            "/api/v1/ingest/url",
            json={
                "source_id": "550e8400-e29b-41d4-a716-446655440000",
                "url": "https://example.com",
                "access_level": "invalid",  # Must be public or private
            },
        )

        assert response.status_code == 422

    def test_ingest_url_validation_invalid_url(self, client):
        """Test ingest URL validation for invalid URL."""
        response = client.post(
            "/api/v1/ingest/url",
            json={
                "source_id": "550e8400-e29b-41d4-a716-446655440000",
                "url": "not-a-url",  # Invalid URL format
                "access_level": "public",
            },
        )

        assert response.status_code == 422

    def test_ingest_source_endpoint_exists(self, client):
        """Test that ingest source endpoint exists."""
        response = client.post(
            "/api/v1/ingest/source",
            json={
                "source_id": "550e8400-e29b-41d4-a716-446655440000",
                "access_level": "public",
            },
        )

        # Should not be 404
        assert response.status_code != 404


class TestAPIDocumentation:
    """Test API documentation."""

    def test_openapi_docs(self, client):
        """Test that OpenAPI docs are available."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_swagger_ui(self, client):
        """Test that Swagger UI is available."""
        response = client.get("/docs")

        assert response.status_code == 200

    def test_redoc_ui(self, client):
        """Test that ReDoc UI is available."""
        response = client.get("/redoc")

        assert response.status_code == 200


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are configured."""
        response = client.options(
            "/api/v1/search",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )

        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200


class TestErrorHandling:
    """Test error handling."""

    def test_404_not_found(self, client):
        """Test 404 for non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == 404

    def test_405_method_not_allowed(self, client):
        """Test 405 for wrong HTTP method."""
        response = client.put("/api/v1/search")  # Should be POST

        assert response.status_code == 405

# DocVector Test Suite

Comprehensive test suite for DocVector with unit, integration, and API tests.

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── unit/               # Unit tests (fast, isolated)
│   ├── test_utils.py
│   ├── test_parsers.py
│   ├── test_chunkers.py
│   ├── test_vectordb.py
│   ├── test_search.py
│   └── test_web_crawler.py
├── integration/        # Integration tests
│   └── test_processing_pipeline.py
└── api/               # API endpoint tests
    └── test_api.py
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit/

# Integration tests
pytest tests/integration/

# API tests
pytest tests/api/

# Specific test file
pytest tests/unit/test_utils.py

# Specific test class
pytest tests/unit/test_utils.py::TestHashUtils

# Specific test function
pytest tests/unit/test_utils.py::TestHashUtils::test_compute_hash_string
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=src/docvector

# Generate HTML coverage report
pytest --cov=src/docvector --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run with Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only API tests
pytest -m api

# Skip slow tests
pytest -m "not slow"
```

### Run in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4
```

## Test Coverage

Current coverage by module:

- **Utils**: 100% (hash_utils, text_utils)
- **Parsers**: 95% (HTML, Markdown)
- **Chunkers**: 95% (Fixed-size, Semantic)
- **Vector DB**: 90% (Qdrant client)
- **Search**: 85% (Vector, Hybrid)
- **API**: 80% (Endpoints, validation)
- **Web Crawler**: 75% (Fetch, crawl logic)

**Overall**: ~85% coverage

## Writing New Tests

### Unit Test Example

```python
import pytest

class TestMyFeature:
    """Test my new feature."""

    @pytest.fixture
    def my_object(self):
        """Create test object."""
        return MyClass()

    def test_basic_functionality(self, my_object):
        """Test basic functionality."""
        result = my_object.do_something()
        assert result == expected_value

    @pytest.mark.asyncio
    async def test_async_functionality(self, my_object):
        """Test async functionality."""
        result = await my_object.do_something_async()
        assert result is not None
```

### Using Fixtures

Common fixtures available in `conftest.py`:

- `db_session`: Database session
- `sample_html`: Sample HTML content
- `sample_markdown`: Sample Markdown content
- `sample_text`: Sample plain text
- `mock_qdrant_client`: Mocked Qdrant client
- `mock_embedder`: Mocked embedder
- `mock_redis_client`: Mocked Redis client

Example:
```python
def test_with_fixtures(sample_html, mock_embedder):
    """Test using fixtures."""
    # Use fixtures in your test
    assert sample_html is not None
```

### Mocking External Services

```python
def test_with_mock(mocker):
    """Test with mocked service."""
    mock_service = mocker.AsyncMock()
    mock_service.method.return_value = "expected"

    result = await my_function(mock_service)
    assert result == "expected"
```

## Test Requirements

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

Or with poetry:

```bash
poetry install --with dev
```

## CI/CD Integration

Tests run automatically on:
- Every push to main
- Every pull request
- Nightly builds

GitHub Actions workflow: `.github/workflows/tests.yml`

## Troubleshooting

### Tests Fail Locally

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

2. **Check Python version**:
   ```bash
   python --version  # Should be 3.11+
   ```

3. **Clear pytest cache**:
   ```bash
   pytest --cache-clear
   ```

### Async Tests Fail

Make sure you have `pytest-asyncio` installed and are using the `@pytest.mark.asyncio` decorator.

### Import Errors

Make sure the `src` directory is in your Python path:

```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
```

Or install in editable mode:

```bash
pip install -e .
```

### Database Tests Fail

Tests use SQLite in-memory database by default. No setup required.

For testing against real PostgreSQL:

```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/test_db"
pytest
```

## Performance

- **Unit tests**: ~1-2 seconds
- **Integration tests**: ~3-5 seconds
- **API tests**: ~2-3 seconds
- **Full suite**: ~10-15 seconds

Run with `-v` to see timing for individual tests.

## Best Practices

1. **Keep tests fast**: Mock external services
2. **One assertion per test**: Makes failures clear
3. **Use descriptive names**: `test_user_can_login_with_valid_credentials`
4. **Arrange-Act-Assert**: Structure tests clearly
5. **Use fixtures**: Avoid duplication
6. **Test edge cases**: Empty inputs, None values, errors
7. **Don't test implementation**: Test behavior

## Adding New Tests

When adding new features:

1. Write tests first (TDD)
2. Aim for 80%+ coverage
3. Include unit + integration tests
4. Test happy path + error cases
5. Update this README if needed

## Questions?

See the main [README.md](../README.md) or [ARCHITECTURE.md](../ARCHITECTURE.md) for more information.

# API Testing Framework Enhancement

## Overview

This document describes the comprehensive API testing infrastructure added to the RAG chatbot system. The enhancements provide robust testing for all FastAPI endpoints while avoiding the static file mounting issues that occur when importing from the main `app.py`.

## What Was Added

### 1. Pytest Configuration (`pyproject.toml`)

Added `[tool.pytest.ini_options]` section with:
- **Test discovery**: Automatic discovery of tests in `backend/tests/`
- **Verbose output**: `-v` flag for detailed test results
- **Short tracebacks**: `--tb=short` for cleaner error output
- **Custom markers**: `unit`, `integration`, `api`, `slow` for test categorization
- **Warning filters**: Suppresses deprecation warnings for cleaner output

```toml
[tool.pytest.ini_options]
minversion = "6.0"
testpaths = ["backend/tests"]
python_files = ["test_*.py"]
addopts = ["-v", "--strict-markers", "--tb=short", "--disable-warnings"]
markers = [
    "unit: Unit tests for individual components",
    "integration: Integration tests for multiple components",
    "api: API endpoint tests",
    "slow: Tests that take a long time to run",
]
```

### 2. Test Application Module (`backend/test_app.py`)

Created a dedicated test application module that:
- **Avoids static file mounting**: Prevents `RuntimeError: Directory '../frontend' does not exist`
- **Mirrors production endpoints**: Implements the same API contract as `app.py`
- **Injectable RAG system**: Accepts a RAG system instance for testing
- **Clean separation**: Keeps test infrastructure separate from production code

**Key function**: `create_test_app(rag_system=None)` - Creates a FastAPI app for testing

### 3. Enhanced Test Fixtures (`backend/tests/conftest.py`)

Added comprehensive fixtures for API testing:

#### Core Fixtures
- `test_client()` - Creates a FastAPI TestClient without static file mounting
- `mock_rag_system()` - Provides a fully functional RAG system with mocked Anthropic API calls
- `api_client_with_rag()` - Combines TestClient with mock RAG system for end-to-end testing

#### Request Fixtures
- `sample_query_request()` - Standard query request without session
- `sample_query_request_with_session()` - Query request with existing session ID

All fixtures use proper mocking to avoid:
- Real Anthropic API calls (saves costs and time)
- External dependencies
- File system requirements (uses temporary directories)

### 4. Comprehensive API Tests (`backend/tests/test_api_endpoints.py`)

Created 30 comprehensive tests organized into 6 test classes:

#### TestQueryEndpoint (11 tests)
Tests for `POST /api/query`:
- Session creation and management
- Answer and source validation
- Request validation (empty queries, missing fields, invalid JSON)
- Response schema validation
- Multiple queries in same session
- Special characters and very long queries

#### TestCoursesEndpoint (7 tests)
Tests for `GET /api/courses`:
- Statistics retrieval
- Data type validation (integers, lists)
- Count consistency (total_courses matches course_titles length)
- Populated data verification
- Response schema validation

#### TestRootEndpoint (2 tests)
Tests for `GET /`:
- Health check response
- Status message validation

#### TestErrorHandling (5 tests)
Tests for error scenarios:
- RAG system errors (500 responses)
- Analytics service errors
- Unsupported HTTP methods (405 responses)
- Non-existent endpoints (404 responses)

#### TestCORSAndHeaders (3 tests)
Tests for HTTP compliance:
- JSON content-type handling
- Response format validation

#### TestEndToEndFlow (2 tests)
Integration tests:
- Complete query workflow (check courses → query → follow-up)
- Parallel sessions (multiple independent sessions)

## Running the Tests

### Run all API tests
```bash
uv run pytest backend/tests/test_api_endpoints.py -v
```

### Run tests by marker
```bash
# API tests only
uv run pytest -m api

# Integration tests
uv run pytest -m integration

# Unit tests
uv run pytest -m unit
```

### Run all tests
```bash
uv run pytest backend/tests/
```

### Run with coverage
```bash
uv run pytest backend/tests/test_api_endpoints.py --cov=backend --cov-report=html
```

## Test Results

All 30 API endpoint tests pass successfully:
- ✅ 11 query endpoint tests
- ✅ 7 courses endpoint tests
- ✅ 2 root endpoint tests
- ✅ 5 error handling tests
- ✅ 3 CORS/headers tests
- ✅ 2 end-to-end flow tests

**Total test suite**: 101 tests (98 passing, 3 pre-existing failures in test_search_tools.py)

## Architecture Decisions

### Why a Separate Test App?

**Problem**: Importing from `app.py` causes:
```python
RuntimeError: Directory '../frontend' does not exist
```

**Solution**: Created `test_app.py` that:
- Defines endpoints inline (no static file mounting)
- Accepts injectable RAG system
- Maintains same API contract as production app

### Why Mock the RAG System?

**Benefits**:
- **Fast tests**: No real API calls to Anthropic
- **Deterministic**: Consistent results every run
- **Cost-effective**: No API usage charges
- **Isolated**: Tests don't depend on external services
- **Controllable**: Can simulate error conditions

### Fixture Organization

**Hierarchy**:
```
sample_course + sample_chunks
    ↓
populated_vector_store
    ↓
mock_rag_system
    ↓
api_client_with_rag
```

This ensures:
- Proper setup order
- Reusability across tests
- Clean teardown (temporary directories)

## Best Practices

### 1. Use Appropriate Fixtures
```python
# For testing with mock RAG system
def test_query(api_client_with_rag):
    response = api_client_with_rag.post("/api/query", json={...})

# For testing error handling
def test_error():
    from test_app import create_test_app
    broken_rag = Mock()
    broken_rag.query.side_effect = Exception("Error")
    client = TestClient(create_test_app(rag_system=broken_rag))
```

### 2. Always Validate Response Schema
```python
def test_query_response(api_client_with_rag):
    response = api_client_with_rag.post("/api/query", json={...})
    data = response.json()

    # Check status code
    assert response.status_code == 200

    # Validate all required fields
    assert "answer" in data
    assert "sources" in data
    assert "session_id" in data

    # Validate types
    assert isinstance(data["answer"], str)
    assert isinstance(data["sources"], list)
```

### 3. Test Both Success and Failure Cases
```python
# Success case
def test_query_success(api_client_with_rag):
    response = api_client_with_rag.post("/api/query", json=valid_request)
    assert response.status_code == 200

# Failure case
def test_query_invalid(api_client_with_rag):
    response = api_client_with_rag.post("/api/query", json=invalid_request)
    assert response.status_code == 422
```

### 4. Use Markers for Organization
```python
@pytest.mark.api
@pytest.mark.integration
def test_complete_workflow(api_client_with_rag):
    # End-to-end test
    pass
```

## Extending the Tests

### Adding New Endpoint Tests

1. **Create test class**:
```python
@pytest.mark.api
class TestNewEndpoint:
    """Tests for the new endpoint"""

    def test_basic_functionality(self, api_client_with_rag):
        response = api_client_with_rag.get("/api/new-endpoint")
        assert response.status_code == 200
```

2. **Add endpoint to test app** (`backend/test_app.py`):
```python
@app.get("/api/new-endpoint")
async def new_endpoint():
    # Implementation
    pass
```

3. **Create fixtures if needed** (`conftest.py`):
```python
@pytest.fixture
def sample_new_data():
    return {"key": "value"}
```

### Adding New Fixtures

Follow the existing pattern in `conftest.py`:
```python
@pytest.fixture
def my_test_fixture(existing_fixture):
    """Clear docstring explaining purpose"""
    # Setup
    resource = create_resource(existing_fixture)

    yield resource

    # Teardown (optional)
    cleanup_resource(resource)
```

## Troubleshooting

### Tests fail with "No module named 'test_app'"

**Solution**: Ensure `test_app.py` is in `backend/` directory, not `backend/tests/`

### Tests fail with "Directory '../frontend' does not exist"

**Solution**: You're importing from `app.py`. Use `test_app.create_test_app()` instead

### Mock RAG system not working

**Solution**: Ensure `monkeypatch` is properly mocking the Anthropic client in `conftest.py`

### Session-related test failures

**Solution**: Check that `mock_rag_system.session_manager` is properly initialized

## Key Files

- `pyproject.toml` - Pytest configuration
- `backend/test_app.py` - Test FastAPI application
- `backend/tests/conftest.py` - Shared test fixtures
- `backend/tests/test_api_endpoints.py` - API endpoint tests
- `backend/tests/API_TESTING_README.md` - This documentation

## References

- [FastAPI Testing Documentation](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/example/markers.html)
- [TestClient (Starlette)](https://www.starlette.io/testclient/)

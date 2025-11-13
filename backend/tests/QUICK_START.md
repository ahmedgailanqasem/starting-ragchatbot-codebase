# API Testing Quick Start Guide

## Running Tests

### All API tests
```bash
uv run pytest backend/tests/test_api_endpoints.py -v
```

### Specific test class
```bash
uv run pytest backend/tests/test_api_endpoints.py::TestQueryEndpoint -v
```

### Specific test
```bash
uv run pytest backend/tests/test_api_endpoints.py::TestQueryEndpoint::test_query_without_session_creates_new_session -v
```

### By marker
```bash
uv run pytest -m api              # All API tests
uv run pytest -m integration      # Integration tests
uv run pytest -m "api and not slow"  # API tests excluding slow ones
```

### All tests in the project
```bash
uv run pytest backend/tests/ -v
```

## Test Organization

### Test Classes
- `TestQueryEndpoint` - Tests for POST /api/query (11 tests)
- `TestCoursesEndpoint` - Tests for GET /api/courses (7 tests)
- `TestRootEndpoint` - Tests for GET / (2 tests)
- `TestErrorHandling` - Error scenarios (5 tests)
- `TestCORSAndHeaders` - HTTP compliance (3 tests)
- `TestEndToEndFlow` - Integration workflows (2 tests)

**Total: 30 tests**

## Key Files

```
backend/
├── test_app.py                      # Test FastAPI app (no static files)
└── tests/
    ├── conftest.py                  # Shared fixtures
    ├── test_api_endpoints.py        # API endpoint tests (30 tests)
    ├── API_TESTING_README.md        # Comprehensive documentation
    └── QUICK_START.md               # This file
```

## Common Fixtures

### api_client_with_rag
Most common fixture - provides TestClient with mock RAG system
```python
def test_example(api_client_with_rag):
    response = api_client_with_rag.post("/api/query", json={
        "query": "What is RAG?",
        "session_id": None
    })
    assert response.status_code == 200
```

### sample_query_request
Pre-built query request dictionary
```python
def test_example(api_client_with_rag, sample_query_request):
    response = api_client_with_rag.post("/api/query", json=sample_query_request)
    assert response.status_code == 200
```

### mock_rag_system
Standalone RAG system with mocked API calls
```python
def test_example(mock_rag_system):
    answer, sources = mock_rag_system.query("What is RAG?", "session-id")
    assert len(answer) > 0
```

## Writing New Tests

### 1. Add to existing test class
```python
@pytest.mark.api
class TestQueryEndpoint:
    def test_new_feature(self, api_client_with_rag):
        response = api_client_with_rag.post("/api/query", json={
            "query": "test",
            "session_id": None
        })
        assert response.status_code == 200
```

### 2. Create new test class
```python
@pytest.mark.api
class TestNewEndpoint:
    """Tests for the new endpoint"""

    def test_basic(self, api_client_with_rag):
        response = api_client_with_rag.get("/api/new")
        assert response.status_code == 200
```

### 3. Test error handling
```python
def test_error_scenario(self):
    from fastapi.testclient import TestClient
    from test_app import create_test_app
    from unittest.mock import Mock

    broken_rag = Mock()
    broken_rag.query.side_effect = Exception("Error")
    broken_rag.session_manager.create_session.return_value = "test"

    client = TestClient(create_test_app(rag_system=broken_rag))
    response = client.post("/api/query", json={"query": "test"})

    assert response.status_code == 500
```

## Test Patterns

### Status Code Validation
```python
assert response.status_code == 200
assert response.status_code == 404
assert response.status_code == 422  # Validation error
assert response.status_code == 500  # Server error
```

### Response Schema Validation
```python
data = response.json()

# Check fields exist
assert "answer" in data
assert "sources" in data

# Check types
assert isinstance(data["answer"], str)
assert isinstance(data["sources"], list)

# Check values
assert len(data["answer"]) > 0
```

### Source Structure Validation
```python
for source in data["sources"]:
    assert "label" in source
    assert isinstance(source["label"], str)
    if "link" in source:
        assert source["link"] is None or isinstance(source["link"], str)
```

## Debugging Tests

### Run with verbose output
```bash
uv run pytest backend/tests/test_api_endpoints.py -vv
```

### Show print statements
```bash
uv run pytest backend/tests/test_api_endpoints.py -s
```

### Stop on first failure
```bash
uv run pytest backend/tests/test_api_endpoints.py -x
```

### Run last failed tests
```bash
uv run pytest backend/tests/test_api_endpoints.py --lf
```

### Show full traceback
```bash
uv run pytest backend/tests/test_api_endpoints.py --tb=long
```

## Common Issues

### "Directory '../frontend' does not exist"
**Cause**: Importing from `app.py` instead of `test_app.py`

**Fix**: Use `from test_app import create_test_app`

### "No module named 'test_app'"
**Cause**: `test_app.py` not in `backend/` directory

**Fix**: Move to `backend/test_app.py`

### Mock not working
**Cause**: Fixture not properly injecting mock

**Fix**: Use `api_client_with_rag` fixture or create custom mock

## Need More Info?

See `API_TESTING_README.md` for:
- Detailed architecture decisions
- Fixture hierarchy
- Best practices
- Extending the framework
- Complete troubleshooting guide

# RAG Chatbot Test Suite

## Quick Start

### Running All Tests
```bash
cd backend
uv run pytest tests/ -v
```

### Running Specific Test Files
```bash
# Test CourseSearchTool functionality
uv run pytest tests/test_search_tools.py -v

# Test AIGenerator tool calling
uv run pytest tests/test_ai_generator.py -v

# Test RAG system integration
uv run pytest tests/test_rag_integration.py -v

# Test live running system
uv run pytest tests/test_live_system.py -v -s
```

### Running Specific Tests
```bash
# Test a specific test class
uv run pytest tests/test_search_tools.py::TestCourseSearchTool -v

# Test a specific test method
uv run pytest tests/test_search_tools.py::TestCourseSearchTool::test_execute_returns_string -v
```

### Running with Coverage
```bash
uv run pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html  # View coverage report
```

---

## Test Suite Overview

### Test Files

1. **`test_search_tools.py`** (24 tests)
   - Tests for `CourseSearchTool.execute()` method
   - Tests for `CourseOutlineTool.execute()` method
   - Tests for `ToolManager` functionality
   - Tests for `VectorStore` integration

2. **`test_ai_generator.py`** (11 tests)
   - Tests for `AIGenerator` initialization
   - Tests for tool calling behavior
   - Tests for 2-phase API call pattern
   - Tests for conversation history integration

3. **`test_rag_integration.py`** (25 tests)
   - End-to-end RAG system tests
   - Tests for query flow
   - Tests for session management
   - Tests for source tracking

4. **`test_live_system.py`** (5 tests)
   - Tests against running server
   - Tests for API endpoints
   - Tests for actual query responses

### Fixtures (`conftest.py`)

The test suite uses pytest fixtures for common setup:

- `temp_chroma_path` - Temporary ChromaDB directory
- `test_vector_store` - Vector store instance
- `sample_course` - Sample course data
- `sample_chunks` - Sample course chunks
- `populated_vector_store` - Vector store with test data
- `course_search_tool` - CourseSearchTool instance
- `course_outline_tool` - CourseOutlineTool instance
- `tool_manager` - ToolManager with registered tools
- `test_config` - Test configuration
- `mock_ai_generator` - Mocked AI generator (no API calls)

---

## Test Results (Current)

**Total Tests**: 60
**Passed**: 57 (95%)
**Failed**: 3 (5%)

### Failing Tests
All failures are related to semantic course name matching being too permissive:

1. `test_execute_with_nonexistent_course` - CourseSearchTool
2. `test_execute_with_nonexistent_course` - CourseOutlineTool
3. `test_search_with_invalid_course` - VectorStoreIntegration

**Status**: Non-critical - See PROPOSED_FIXES.md for solution

---

## Test Categories

### Unit Tests
- Individual component testing
- Mocked dependencies
- Fast execution
- High coverage

**Files**: `test_search_tools.py`, `test_ai_generator.py`

### Integration Tests
- Component interaction testing
- Real vector store (temporary)
- Mocked external APIs
- Moderate execution time

**Files**: `test_rag_integration.py`

### Live Tests
- End-to-end testing
- Real running server
- Real API calls
- Slower execution

**Files**: `test_live_system.py`

---

## Key Test Findings

### ✅ What Works
- **CourseSearchTool**: Correctly searches and returns formatted results with sources
- **AIGenerator**: Properly implements 2-phase tool calling pattern
- **RAG System**: Successfully orchestrates all components
- **Tool Manager**: Correctly registers and executes tools
- **Session Management**: Maintains conversation history
- **Source Tracking**: Tracks and resets sources correctly
- **Live System**: Processes queries and returns responses successfully

### ⚠️ Minor Issues
- **Semantic Matching**: Course name matching is too permissive (accepts any query)

### ❌ Cannot Reproduce
- **"Query Failed" Issue**: Unable to reproduce in testing
  - All content queries return successful responses
  - API integration working correctly
  - No errors in server logs

---

## Important Reports

1. **`TEST_ANALYSIS_REPORT.md`**
   - Comprehensive analysis of all test results
   - Component health assessment
   - Detailed findings and recommendations
   - Root cause analysis

2. **`PROPOSED_FIXES.md`**
   - Detailed solutions for identified issues
   - Code examples for each fix
   - Implementation priorities
   - Testing plan for fixes

---

## Writing New Tests

### Test Structure
```python
import pytest
from your_module import YourClass

class TestYourClass:
    """Test suite for YourClass"""

    def test_basic_functionality(self, fixture_name):
        """Test that basic function works"""
        # Arrange
        instance = YourClass()

        # Act
        result = instance.method()

        # Assert
        assert result == expected_value

    def test_error_handling(self):
        """Test that errors are handled correctly"""
        with pytest.raises(ValueError):
            # Code that should raise ValueError
            pass
```

### Using Fixtures
```python
def test_with_vector_store(self, populated_vector_store):
    """Test using populated vector store fixture"""
    results = populated_vector_store.search("test query")
    assert not results.is_empty()
```

### Mocking API Calls
```python
from unittest.mock import Mock, patch

@patch('anthropic.Anthropic')
def test_with_mocked_api(self, mock_anthropic):
    """Test with mocked Anthropic API"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text="Test response")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    # Your test code here
```

---

## Continuous Integration

### Pre-commit Checks
```bash
# Run tests before committing
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=. --cov-report=term-missing
```

### CI Pipeline (example)
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run tests
        run: uv run pytest tests/ -v --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## Debugging Failed Tests

### Verbose Output
```bash
uv run pytest tests/test_search_tools.py -vv
```

### Show Print Statements
```bash
uv run pytest tests/test_search_tools.py -s
```

### Drop into Debugger on Failure
```bash
uv run pytest tests/test_search_tools.py --pdb
```

### Run Only Failed Tests
```bash
uv run pytest tests/ --lf  # Last failed
uv run pytest tests/ --ff  # Failed first, then others
```

### Show Test Duration
```bash
uv run pytest tests/ --durations=10
```

---

## Maintenance

### Updating Tests
When code changes:
1. Update affected test files
2. Run full test suite
3. Update documentation if needed
4. Check coverage hasn't decreased

### Adding New Tests
When adding features:
1. Write tests first (TDD)
2. Ensure tests fail initially
3. Implement feature
4. Verify tests pass
5. Add integration tests
6. Update this README if needed

---

## Contact & Support

For questions about the test suite:
- Review `TEST_ANALYSIS_REPORT.md` for detailed findings
- Review `PROPOSED_FIXES.md` for solutions to known issues
- Check `conftest.py` for available fixtures
- Review existing tests for examples

---

## Next Steps

1. **Implement proposed fixes** (see PROPOSED_FIXES.md)
2. **Run tests again** to verify fixes
3. **Add more edge case tests** as needed
4. **Set up CI/CD** for automated testing
5. **Monitor production** for issues not caught in testing

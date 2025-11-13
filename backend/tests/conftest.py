"""
Pytest configuration and fixtures for RAG system tests
"""

import os
import shutil
import sys
import tempfile
from typing import List
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_generator import AIGenerator
from config import Config
from models import Course, CourseChunk, Lesson
from rag_system import RAGSystem
from search_tools import CourseOutlineTool, CourseSearchTool, ToolManager
from vector_store import SearchResults, VectorStore


@pytest.fixture
def temp_chroma_path():
    """Create a temporary ChromaDB path for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_vector_store(temp_chroma_path):
    """Create a test vector store instance"""
    return VectorStore(
        chroma_path=temp_chroma_path, embedding_model="all-MiniLM-L6-v2", max_results=5
    )


@pytest.fixture
def sample_course():
    """Create a sample course for testing"""
    return Course(
        title="Introduction to RAG Systems",
        course_link="https://example.com/rag-course",
        instructor="Dr. Test",
        lessons=[
            Lesson(
                lesson_number=0,
                title="Course Overview",
                lesson_link="https://example.com/lesson-0",
            ),
            Lesson(
                lesson_number=1,
                title="What is RAG",
                lesson_link="https://example.com/lesson-1",
            ),
            Lesson(
                lesson_number=2,
                title="Vector Databases",
                lesson_link="https://example.com/lesson-2",
            ),
            Lesson(
                lesson_number=3,
                title="Embeddings",
                lesson_link="https://example.com/lesson-3",
            ),
        ],
    )


@pytest.fixture
def sample_chunks():
    """Create sample course chunks for testing"""
    return [
        CourseChunk(
            content="RAG stands for Retrieval-Augmented Generation. It combines retrieval from a knowledge base with language model generation.",
            course_title="Introduction to RAG Systems",
            lesson_number=1,
            lesson_link="https://example.com/lesson-1",
            chunk_index=0,
        ),
        CourseChunk(
            content="Vector databases store embeddings which are numerical representations of text. Popular vector databases include ChromaDB, Pinecone, and Weaviate.",
            course_title="Introduction to RAG Systems",
            lesson_number=2,
            lesson_link="https://example.com/lesson-2",
            chunk_index=1,
        ),
        CourseChunk(
            content="Embeddings are created using embedding models like SentenceTransformers. These models convert text into dense vectors that capture semantic meaning.",
            course_title="Introduction to RAG Systems",
            lesson_number=3,
            lesson_link="https://example.com/lesson-3",
            chunk_index=2,
        ),
    ]


@pytest.fixture
def populated_vector_store(test_vector_store, sample_course, sample_chunks):
    """Create a vector store populated with test data"""
    test_vector_store.add_course_metadata(sample_course)
    test_vector_store.add_course_content(sample_chunks)
    return test_vector_store


@pytest.fixture
def course_search_tool(populated_vector_store):
    """Create a CourseSearchTool instance with populated data"""
    return CourseSearchTool(populated_vector_store)


@pytest.fixture
def course_outline_tool(populated_vector_store):
    """Create a CourseOutlineTool instance with populated data"""
    return CourseOutlineTool(populated_vector_store)


@pytest.fixture
def tool_manager(course_search_tool, course_outline_tool):
    """Create a ToolManager with registered tools"""
    manager = ToolManager()
    manager.register_tool(course_search_tool)
    manager.register_tool(course_outline_tool)
    return manager


@pytest.fixture
def test_config(temp_chroma_path):
    """Create a test configuration"""
    config = Config()
    config.CHROMA_PATH = temp_chroma_path
    # Use a dummy API key for testing (tests should mock API calls)
    if not config.ANTHROPIC_API_KEY:
        config.ANTHROPIC_API_KEY = "test-api-key"
    return config


@pytest.fixture
def mock_ai_generator(monkeypatch):
    """Create a mock AI generator that doesn't make real API calls"""

    class MockAnthropicClient:
        class Messages:
            class Content:
                def __init__(self, text):
                    self.text = text
                    self.type = "text"

            class Response:
                def __init__(self, text, stop_reason="end_turn"):
                    self.content = [MockAnthropicClient.Messages.Content(text)]
                    self.stop_reason = stop_reason

            def create(self, **kwargs):
                # Return a simple mock response
                return MockAnthropicClient.Messages.Response("Mock response")

        def __init__(self, api_key):
            self.messages = self.Messages()

    def mock_anthropic_init(api_key):
        return MockAnthropicClient(api_key)

    import anthropic

    monkeypatch.setattr(anthropic, "Anthropic", mock_anthropic_init)

    return AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")


# ===== API Testing Fixtures =====

@pytest.fixture
def test_client():
    """Create a FastAPI test client without static file mounting"""
    from fastapi.testclient import TestClient
    from test_app import create_test_app

    # Create test app without RAG system (will be injected later)
    test_app = create_test_app(rag_system=None)
    client = TestClient(test_app)

    return client


@pytest.fixture
def mock_rag_system(test_config, populated_vector_store, monkeypatch):
    """Create a mock RAG system for API testing"""
    # Mock the AIGenerator to avoid real API calls
    class MockAnthropicClient:
        class Messages:
            class Content:
                def __init__(self, text):
                    self.text = text
                    self.type = "text"

            class Response:
                def __init__(self, text, stop_reason="end_turn"):
                    self.content = [MockAnthropicClient.Messages.Content(text)]
                    self.stop_reason = stop_reason

            def create(self, **kwargs):
                return MockAnthropicClient.Messages.Response(
                    "Based on the course materials, RAG systems combine retrieval and generation."
                )

        def __init__(self, api_key):
            self.messages = self.Messages()

    def mock_anthropic_init(api_key):
        return MockAnthropicClient(api_key)

    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", mock_anthropic_init)

    # Create RAG system with test config
    rag = RAGSystem(test_config)
    rag.vector_store = populated_vector_store

    return rag


@pytest.fixture
def api_client_with_rag(mock_rag_system):
    """Create a test client with a mock RAG system injected"""
    from fastapi.testclient import TestClient
    from test_app import create_test_app

    # Create test app with the mock RAG system
    test_app = create_test_app(rag_system=mock_rag_system)
    client = TestClient(test_app)

    return client


@pytest.fixture
def sample_query_request():
    """Sample query request for testing"""
    return {
        "query": "What is RAG?",
        "session_id": None
    }


@pytest.fixture
def sample_query_request_with_session():
    """Sample query request with session ID for testing"""
    return {
        "query": "Tell me more about vector databases",
        "session_id": "test-session-123"
    }

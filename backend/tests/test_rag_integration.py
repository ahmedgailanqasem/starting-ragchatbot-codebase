"""
Integration tests for RAG system query handling
"""

import shutil
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest
from config import Config
from rag_system import RAGSystem


class TestRAGSystemIntegration:
    """Integration tests for RAG system query handling"""

    @pytest.fixture
    def test_rag_system(self, test_config, sample_course, sample_chunks):
        """Create a test RAG system with populated data"""
        rag = RAGSystem(test_config)

        # Populate with test data
        rag.vector_store.add_course_metadata(sample_course)
        rag.vector_store.add_course_content(sample_chunks)

        return rag

    def test_rag_system_initialization(self, test_config):
        """Test that RAG system initializes correctly"""
        rag = RAGSystem(test_config)

        assert rag.vector_store is not None
        assert rag.ai_generator is not None
        assert rag.tool_manager is not None
        assert rag.search_tool is not None
        assert rag.outline_tool is not None

    def test_tool_manager_has_tools_registered(self, test_rag_system):
        """Test that tools are properly registered"""
        tools = test_rag_system.tool_manager.get_tool_definitions()

        assert len(tools) >= 2
        tool_names = [t["name"] for t in tools]
        assert "search_course_content" in tool_names
        assert "get_course_outline" in tool_names

    @patch("anthropic.Anthropic")
    def test_query_without_tools_direct_response(self, mock_anthropic, test_rag_system):
        """Test query that doesn't require tools (general knowledge)"""
        # Mock API response - no tool use
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [
            Mock(text="RAG stands for Retrieval-Augmented Generation")
        ]
        mock_response.stop_reason = "end_turn"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Reinitialize AI generator with mocked client
        test_rag_system.ai_generator = MagicMock()
        test_rag_system.ai_generator.generate_response.return_value = (
            "RAG stands for Retrieval-Augmented Generation"
        )

        # Test
        response, sources = test_rag_system.query("What does RAG stand for?")

        assert isinstance(response, str)
        assert len(response) > 0

    @patch("anthropic.Anthropic")
    def test_query_with_tool_use(self, mock_anthropic, test_rag_system):
        """Test query that triggers tool use"""
        # Mock API responses
        mock_client = Mock()

        # First response - tool use
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {"query": "vector databases"}

        initial_response = Mock()
        initial_response.content = [mock_tool_block]
        initial_response.stop_reason = "tool_use"

        # Second response - final answer
        final_response = Mock()
        final_response.content = [Mock(text="Vector databases store embeddings...")]
        final_response.stop_reason = "end_turn"

        mock_client.messages.create.side_effect = [initial_response, final_response]
        mock_anthropic.return_value = mock_client

        # Reinitialize with mock
        from ai_generator import AIGenerator

        test_rag_system.ai_generator = AIGenerator(
            api_key=test_rag_system.config.ANTHROPIC_API_KEY,
            model=test_rag_system.config.ANTHROPIC_MODEL,
        )

        # Test
        response, sources = test_rag_system.query("Tell me about vector databases")

        assert isinstance(response, str)
        assert isinstance(sources, list)

    def test_query_returns_tuple(self, test_rag_system):
        """Test that query returns (response, sources) tuple"""
        # Mock the AI generator
        test_rag_system.ai_generator.generate_response = Mock(
            return_value="Test response"
        )

        result = test_rag_system.query("Test query")

        assert isinstance(result, tuple)
        assert len(result) == 2
        response, sources = result
        assert isinstance(response, str)
        assert isinstance(sources, list)

    def test_query_with_session_id(self, test_rag_system):
        """Test query with session ID for conversation history"""
        test_rag_system.ai_generator.generate_response = Mock(return_value="Response")

        session_id = "test_session_123"
        response, sources = test_rag_system.query("Test query", session_id=session_id)

        # Session should be created/updated
        history = test_rag_system.session_manager.get_conversation_history(session_id)
        assert history is not None

    def test_query_updates_session_history(self, test_rag_system):
        """Test that query updates session history"""
        test_rag_system.ai_generator.generate_response = Mock(
            return_value="Response to question"
        )

        session_id = "test_session_456"

        # First query
        test_rag_system.query("First question", session_id=session_id)

        # Second query
        test_rag_system.query("Second question", session_id=session_id)

        # History should contain both exchanges
        history = test_rag_system.session_manager.get_conversation_history(session_id)
        assert "First question" in history
        assert "Second question" in history

    def test_query_passes_tools_to_ai_generator(self, test_rag_system):
        """Test that query passes tools to AI generator"""
        mock_generate = Mock(return_value="Response")
        test_rag_system.ai_generator.generate_response = mock_generate

        test_rag_system.query("Test query")

        # Verify generate_response was called with tools
        assert mock_generate.called
        call_kwargs = mock_generate.call_args[1]
        assert "tools" in call_kwargs
        assert len(call_kwargs["tools"]) >= 2

    def test_query_passes_tool_manager(self, test_rag_system):
        """Test that query passes tool_manager to AI generator"""
        mock_generate = Mock(return_value="Response")
        test_rag_system.ai_generator.generate_response = mock_generate

        test_rag_system.query("Test query")

        call_kwargs = mock_generate.call_args[1]
        assert "tool_manager" in call_kwargs
        assert call_kwargs["tool_manager"] is test_rag_system.tool_manager

    def test_sources_tracked_from_search_tool(self, test_rag_system):
        """Test that sources are tracked when search tool is used"""
        # Simulate tool execution that populates sources
        test_rag_system.search_tool.last_sources = [
            {"label": "Course A - Lesson 1", "link": "http://example.com/1"},
            {"label": "Course A - Lesson 2", "link": "http://example.com/2"},
        ]

        # Mock AI to not actually call API
        test_rag_system.ai_generator.generate_response = Mock(return_value="Response")

        # Manually populate sources as if search tool was used
        test_rag_system.search_tool.execute(query="test")

        # Get sources
        sources = test_rag_system.tool_manager.get_last_sources()

        assert len(sources) > 0
        for source in sources:
            assert "label" in source
            assert "link" in source

    def test_sources_reset_after_query(self, test_rag_system):
        """Test that sources are reset after each query"""
        # Populate sources
        test_rag_system.search_tool.last_sources = [
            {"label": "Test", "link": "http://test.com"}
        ]

        test_rag_system.ai_generator.generate_response = Mock(return_value="Response")

        # Execute query - should reset sources
        test_rag_system.query("Test query")

        # Sources should be reset
        sources = test_rag_system.tool_manager.get_last_sources()
        assert len(sources) == 0


class TestRAGSystemContentQueries:
    """Specific tests for content-related queries"""

    @pytest.fixture
    def rag_with_data(self, test_config, sample_course, sample_chunks):
        """RAG system with test data"""
        rag = RAGSystem(test_config)
        rag.vector_store.add_course_metadata(sample_course)
        rag.vector_store.add_course_content(sample_chunks)
        return rag

    def test_content_query_can_search(self, rag_with_data):
        """Test that content queries can successfully search"""
        # Test the search tool directly
        result = rag_with_data.search_tool.execute(query="What is RAG?")

        assert isinstance(result, str)
        assert len(result) > 0
        assert "query failed" not in result.lower()

    def test_content_query_finds_relevant_chunks(self, rag_with_data):
        """Test that content queries find relevant information"""
        result = rag_with_data.search_tool.execute(query="vector databases")

        # Should find the chunk about vector databases
        assert "No relevant content found" not in result
        assert len(result) > 0

    def test_content_query_with_course_filter(self, rag_with_data):
        """Test content query with course filter"""
        result = rag_with_data.search_tool.execute(
            query="embeddings", course_name="Introduction to RAG Systems"
        )

        assert isinstance(result, str)
        assert "query failed" not in result.lower()

    @patch("anthropic.Anthropic")
    def test_full_query_flow_with_search(self, mock_anthropic, rag_with_data):
        """Test full query flow that uses search tool"""
        # Setup mock to simulate tool use
        mock_client = Mock()

        # Tool use request
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_course_content"
        mock_tool_block.id = "tool_123"
        mock_tool_block.input = {"query": "embeddings"}

        tool_response = Mock()
        tool_response.content = [mock_tool_block]
        tool_response.stop_reason = "tool_use"

        # Final response
        final_response = Mock()
        final_response.content = [
            Mock(text="Embeddings are numerical representations created by models...")
        ]
        final_response.stop_reason = "end_turn"

        mock_client.messages.create.side_effect = [tool_response, final_response]
        mock_anthropic.return_value = mock_client

        # Reinitialize AI generator
        from ai_generator import AIGenerator

        rag_with_data.ai_generator = AIGenerator(
            api_key=rag_with_data.config.ANTHROPIC_API_KEY,
            model=rag_with_data.config.ANTHROPIC_MODEL,
        )

        # Execute query
        response, sources = rag_with_data.query("What are embeddings?")

        # Verify response
        assert isinstance(response, str)
        assert len(response) > 0
        assert "query failed" not in response.lower()

    def test_vector_store_has_data(self, rag_with_data):
        """Verify vector store actually has data"""
        count = rag_with_data.vector_store.get_course_count()
        assert count > 0, "Vector store should have courses"

        titles = rag_with_data.vector_store.get_existing_course_titles()
        assert len(titles) > 0, "Vector store should have course titles"

    def test_search_tool_can_access_vector_store(self, rag_with_data):
        """Test that search tool can access vector store data"""
        # Direct vector store search
        results = rag_with_data.vector_store.search(query="RAG")

        assert not results.is_empty(), "Vector store should return results"
        assert results.error is None, "Should not have errors"
        assert len(results.documents) > 0, "Should have documents"


class TestRAGSystemErrorHandling:
    """Test error handling in RAG system"""

    def test_query_with_empty_vector_store(self, test_config):
        """Test query when vector store is empty"""
        rag = RAGSystem(test_config)
        rag.ai_generator.generate_response = Mock(
            return_value="I don't have information about that"
        )

        response, sources = rag.query("What is RAG?")

        # Should handle gracefully
        assert isinstance(response, str)
        assert isinstance(sources, list)

    def test_query_with_invalid_session_id(self, test_config):
        """Test query with non-existent session ID"""
        rag = RAGSystem(test_config)
        rag.ai_generator.generate_response = Mock(return_value="Response")

        # Should create new session
        response, sources = rag.query("Test", session_id="nonexistent_session")

        assert isinstance(response, str)

    @patch("anthropic.Anthropic")
    def test_query_handles_api_errors_gracefully(self, mock_anthropic, test_config):
        """Test that API errors are handled gracefully"""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client

        rag = RAGSystem(test_config)

        # Should raise or handle the exception
        with pytest.raises(Exception):
            rag.query("Test query")

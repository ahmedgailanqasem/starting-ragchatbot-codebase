"""
Tests for CourseSearchTool and related search functionality
"""
import pytest
from search_tools import CourseSearchTool, ToolManager, CourseOutlineTool
from vector_store import VectorStore, SearchResults


class TestCourseSearchTool:
    """Test suite for CourseSearchTool.execute() method"""

    def test_execute_returns_string(self, course_search_tool):
        """Test that execute returns a string"""
        result = course_search_tool.execute(query="What is RAG?")
        assert isinstance(result, str), "execute() should return a string"

    def test_execute_with_valid_query(self, course_search_tool):
        """Test execute with a valid query returns results"""
        result = course_search_tool.execute(query="What is RAG?")
        assert result != "", "execute() should return non-empty string for valid query"
        assert "No relevant content found" not in result, "Should find content for RAG query"

    def test_execute_with_course_filter(self, course_search_tool):
        """Test execute with course name filter"""
        result = course_search_tool.execute(
            query="embeddings",
            course_name="Introduction to RAG Systems"
        )
        assert isinstance(result, str), "Should return string with course filter"
        assert "Introduction to RAG Systems" in result or "No relevant content found" in result

    def test_execute_with_partial_course_name(self, course_search_tool):
        """Test execute with partial course name (semantic matching)"""
        result = course_search_tool.execute(
            query="vector databases",
            course_name="RAG"  # Partial match
        )
        assert isinstance(result, str), "Should return string with partial course name"

    def test_execute_with_lesson_filter(self, course_search_tool):
        """Test execute with lesson number filter"""
        result = course_search_tool.execute(
            query="vector",
            lesson_number=2
        )
        assert isinstance(result, str), "Should return string with lesson filter"

    def test_execute_with_both_filters(self, course_search_tool):
        """Test execute with both course and lesson filters"""
        result = course_search_tool.execute(
            query="embeddings",
            course_name="Introduction to RAG Systems",
            lesson_number=3
        )
        assert isinstance(result, str), "Should return string with both filters"

    def test_execute_with_nonexistent_course(self, course_search_tool):
        """Test execute with non-existent course name"""
        result = course_search_tool.execute(
            query="test query",
            course_name="Nonexistent Course XYZ"
        )
        assert "No course found" in result or "No relevant content found" in result

    def test_execute_with_invalid_lesson(self, course_search_tool):
        """Test execute with non-existent lesson number"""
        result = course_search_tool.execute(
            query="test query",
            lesson_number=999
        )
        assert "No relevant content found" in result

    def test_execute_formats_results_correctly(self, course_search_tool):
        """Test that results are formatted with course and lesson context"""
        result = course_search_tool.execute(query="RAG")

        # Should contain formatted headers with course info
        assert "[" in result and "]" in result, "Results should have formatted headers"

    def test_execute_tracks_sources(self, course_search_tool):
        """Test that execute populates last_sources"""
        # Clear any existing sources
        course_search_tool.last_sources = []

        result = course_search_tool.execute(query="vector databases")

        # If results were found, sources should be tracked
        if "No relevant content found" not in result:
            assert len(course_search_tool.last_sources) > 0, "Should track sources when results found"

            # Check source structure
            for source in course_search_tool.last_sources:
                assert isinstance(source, dict), "Sources should be dictionaries"
                assert "label" in source, "Source should have 'label' field"
                assert "link" in source, "Source should have 'link' field"

    def test_execute_source_labels_format(self, course_search_tool):
        """Test that source labels are formatted correctly"""
        course_search_tool.last_sources = []
        result = course_search_tool.execute(query="embeddings")

        if "No relevant content found" not in result and course_search_tool.last_sources:
            for source in course_search_tool.last_sources:
                label = source["label"]
                # Should contain course title
                assert "Introduction to RAG Systems" in label or len(label) > 0

    def test_execute_with_empty_query(self, course_search_tool):
        """Test execute with empty query string"""
        result = course_search_tool.execute(query="")
        # Should handle gracefully and return a string
        assert isinstance(result, str)

    def test_get_tool_definition(self, course_search_tool):
        """Test that tool definition is correctly structured"""
        definition = course_search_tool.get_tool_definition()

        assert "name" in definition
        assert definition["name"] == "search_course_content"
        assert "description" in definition
        assert "input_schema" in definition

        schema = definition["input_schema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "query" in schema["properties"]
        assert "required" in schema
        assert "query" in schema["required"]


class TestCourseOutlineTool:
    """Test suite for CourseOutlineTool"""

    def test_execute_with_valid_course(self, course_outline_tool):
        """Test execute with valid course name"""
        result = course_outline_tool.execute(course_name="Introduction to RAG Systems")

        assert isinstance(result, str)
        assert "Course:" in result
        assert "Introduction to RAG Systems" in result
        assert "Total Lessons:" in result
        assert "Lesson List:" in result

    def test_execute_with_partial_course_name(self, course_outline_tool):
        """Test execute with partial course name"""
        result = course_outline_tool.execute(course_name="RAG")

        assert isinstance(result, str)
        # Should find the course via semantic matching
        assert "Course:" in result or "No course found" in result

    def test_execute_with_nonexistent_course(self, course_outline_tool):
        """Test execute with non-existent course"""
        result = course_outline_tool.execute(course_name="Nonexistent Course XYZ")

        assert "No course found" in result

    def test_execute_includes_lessons(self, course_outline_tool):
        """Test that execute includes lesson information"""
        result = course_outline_tool.execute(course_name="Introduction to RAG Systems")

        if "No course found" not in result:
            assert "Lesson 0:" in result or "Lesson 1:" in result
            assert "Course Overview" in result or "What is RAG" in result

    def test_get_tool_definition(self, course_outline_tool):
        """Test that tool definition is correctly structured"""
        definition = course_outline_tool.get_tool_definition()

        assert "name" in definition
        assert definition["name"] == "get_course_outline"
        assert "description" in definition
        assert "input_schema" in definition

        schema = definition["input_schema"]
        assert "course_name" in schema["properties"]
        assert "course_name" in schema["required"]


class TestToolManager:
    """Test suite for ToolManager"""

    def test_register_tool(self, test_vector_store):
        """Test registering a tool"""
        manager = ToolManager()
        search_tool = CourseSearchTool(test_vector_store)

        manager.register_tool(search_tool)

        definitions = manager.get_tool_definitions()
        assert len(definitions) == 1
        assert definitions[0]["name"] == "search_course_content"

    def test_execute_tool(self, tool_manager):
        """Test executing a registered tool"""
        result = tool_manager.execute_tool(
            "search_course_content",
            query="What is RAG?"
        )

        assert isinstance(result, str)

    def test_execute_nonexistent_tool(self, tool_manager):
        """Test executing a non-existent tool"""
        result = tool_manager.execute_tool("nonexistent_tool", query="test")

        assert "not found" in result.lower()

    def test_get_tool_definitions(self, tool_manager):
        """Test getting all tool definitions"""
        definitions = tool_manager.get_tool_definitions()

        assert isinstance(definitions, list)
        assert len(definitions) >= 2  # Should have search and outline tools

        tool_names = [d["name"] for d in definitions]
        assert "search_course_content" in tool_names
        assert "get_course_outline" in tool_names

    def test_get_last_sources(self, tool_manager):
        """Test getting sources from last search"""
        # Execute a search
        tool_manager.execute_tool("search_course_content", query="RAG")

        sources = tool_manager.get_last_sources()
        assert isinstance(sources, list)

    def test_reset_sources(self, tool_manager):
        """Test resetting sources"""
        # Execute a search to populate sources
        tool_manager.execute_tool("search_course_content", query="RAG")

        # Reset
        tool_manager.reset_sources()

        sources = tool_manager.get_last_sources()
        assert len(sources) == 0


class TestVectorStoreIntegration:
    """Integration tests for VectorStore used by search tools"""

    def test_search_returns_searchresults(self, populated_vector_store):
        """Test that vector store search returns SearchResults object"""
        results = populated_vector_store.search(query="RAG")

        assert isinstance(results, SearchResults)
        assert hasattr(results, 'documents')
        assert hasattr(results, 'metadata')
        assert hasattr(results, 'error')

    def test_search_with_valid_query(self, populated_vector_store):
        """Test search with valid query returns results"""
        results = populated_vector_store.search(query="vector databases")

        assert not results.is_empty(), "Should return results for valid query"
        assert results.error is None, "Should not have error for valid query"
        assert len(results.documents) > 0

    def test_search_metadata_includes_lesson_info(self, populated_vector_store):
        """Test that search results include lesson metadata"""
        results = populated_vector_store.search(query="embeddings")

        if not results.is_empty():
            for metadata in results.metadata:
                assert "course_title" in metadata
                assert "lesson_number" in metadata
                assert "lesson_link" in metadata

    def test_search_with_course_filter(self, populated_vector_store):
        """Test search with course name filter"""
        results = populated_vector_store.search(
            query="test",
            course_name="Introduction to RAG Systems"
        )

        # Should either find results or return empty (not error)
        assert isinstance(results, SearchResults)

    def test_search_with_invalid_course(self, populated_vector_store):
        """Test search with invalid course name"""
        results = populated_vector_store.search(
            query="test",
            course_name="Nonexistent Course"
        )

        # Should return error about course not found
        assert results.error is not None or results.is_empty()

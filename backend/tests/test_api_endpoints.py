"""
Comprehensive API endpoint tests for the RAG system FastAPI application

These tests verify:
- POST /api/query endpoint for querying course materials
- GET /api/courses endpoint for retrieving course statistics
- GET / root endpoint for health check
- Request/response validation
- Error handling
- Session management
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.api
class TestQueryEndpoint:
    """Tests for the POST /api/query endpoint"""

    def test_query_without_session_creates_new_session(self, api_client_with_rag, sample_query_request):
        """Test that querying without a session ID creates a new session"""
        response = api_client_with_rag.post("/api/query", json=sample_query_request)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data

        # Verify session was created
        assert data["session_id"] is not None
        assert len(data["session_id"]) > 0

    def test_query_with_session_uses_existing_session(self, api_client_with_rag, sample_query_request_with_session):
        """Test that querying with a session ID uses that session"""
        response = api_client_with_rag.post("/api/query", json=sample_query_request_with_session)

        assert response.status_code == 200
        data = response.json()

        # Verify the session ID matches the one provided
        assert data["session_id"] == "test-session-123"

    def test_query_returns_answer_and_sources(self, api_client_with_rag, sample_query_request):
        """Test that query returns both answer and sources"""
        response = api_client_with_rag.post("/api/query", json=sample_query_request)

        assert response.status_code == 200
        data = response.json()

        # Verify answer is a non-empty string
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0

        # Verify sources is a list
        assert isinstance(data["sources"], list)

    def test_query_sources_have_correct_structure(self, api_client_with_rag, sample_query_request):
        """Test that source items have label and optional link"""
        response = api_client_with_rag.post("/api/query", json=sample_query_request)

        assert response.status_code == 200
        data = response.json()

        # Check each source item structure
        for source in data["sources"]:
            assert "label" in source
            assert isinstance(source["label"], str)
            # Link is optional, so we just check if it exists, it's a string or None
            if "link" in source:
                assert source["link"] is None or isinstance(source["link"], str)

    def test_query_with_empty_query_string(self, api_client_with_rag):
        """Test querying with an empty query string"""
        request_data = {"query": "", "session_id": None}
        response = api_client_with_rag.post("/api/query", json=request_data)

        # Should still return 200, but the answer might be generic
        # The system should handle empty queries gracefully
        assert response.status_code in [200, 400, 422]

    def test_query_with_missing_query_field(self, api_client_with_rag):
        """Test querying with missing query field returns validation error"""
        request_data = {"session_id": None}
        response = api_client_with_rag.post("/api/query", json=request_data)

        # FastAPI validation should catch this
        assert response.status_code == 422

    def test_query_with_invalid_json(self, api_client_with_rag):
        """Test querying with invalid JSON returns error"""
        response = api_client_with_rag.post(
            "/api/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_query_response_schema_validation(self, api_client_with_rag, sample_query_request):
        """Test that the response matches the QueryResponse schema"""
        response = api_client_with_rag.post("/api/query", json=sample_query_request)

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields are present
        required_fields = ["answer", "sources", "session_id"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify types
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)

    def test_multiple_queries_same_session(self, api_client_with_rag):
        """Test multiple queries using the same session maintain context"""
        # First query
        request1 = {"query": "What is RAG?", "session_id": None}
        response1 = api_client_with_rag.post("/api/query", json=request1)
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Second query with same session
        request2 = {"query": "Tell me more", "session_id": session_id}
        response2 = api_client_with_rag.post("/api/query", json=request2)
        assert response2.status_code == 200

        # Session should be the same
        assert response2.json()["session_id"] == session_id

    def test_query_with_special_characters(self, api_client_with_rag):
        """Test querying with special characters in query"""
        request_data = {
            "query": "What is RAG? How does it work with embeddings & vectors?",
            "session_id": None
        }
        response = api_client_with_rag.post("/api/query", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_query_with_very_long_query(self, api_client_with_rag):
        """Test querying with a very long query string"""
        long_query = "What is RAG? " * 100  # Create a long query
        request_data = {"query": long_query, "session_id": None}
        response = api_client_with_rag.post("/api/query", json=request_data)

        # Should handle long queries gracefully
        assert response.status_code in [200, 400, 413, 422]


@pytest.mark.api
class TestCoursesEndpoint:
    """Tests for the GET /api/courses endpoint"""

    def test_get_courses_returns_statistics(self, api_client_with_rag):
        """Test that /api/courses returns course statistics"""
        response = api_client_with_rag.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "total_courses" in data
        assert "course_titles" in data

    def test_courses_total_count_is_integer(self, api_client_with_rag):
        """Test that total_courses is an integer"""
        response = api_client_with_rag.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["total_courses"], int)
        assert data["total_courses"] >= 0

    def test_courses_titles_is_list(self, api_client_with_rag):
        """Test that course_titles is a list of strings"""
        response = api_client_with_rag.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["course_titles"], list)
        # All items should be strings
        for title in data["course_titles"]:
            assert isinstance(title, str)

    def test_courses_count_matches_titles_length(self, api_client_with_rag):
        """Test that total_courses matches the length of course_titles"""
        response = api_client_with_rag.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        assert data["total_courses"] == len(data["course_titles"])

    def test_courses_with_populated_data(self, api_client_with_rag):
        """Test courses endpoint with populated test data"""
        response = api_client_with_rag.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        # We have sample data from the fixtures
        assert data["total_courses"] > 0
        assert len(data["course_titles"]) > 0

        # Verify the test course is in the list
        assert "Introduction to RAG Systems" in data["course_titles"]

    def test_courses_endpoint_accepts_no_parameters(self, api_client_with_rag):
        """Test that courses endpoint works without parameters"""
        # Should work with no query parameters
        response = api_client_with_rag.get("/api/courses")
        assert response.status_code == 200

    def test_courses_response_schema_validation(self, api_client_with_rag):
        """Test that the response matches the CourseStats schema"""
        response = api_client_with_rag.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields are present
        required_fields = ["total_courses", "course_titles"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify types
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)


@pytest.mark.api
class TestRootEndpoint:
    """Tests for the GET / root endpoint"""

    def test_root_endpoint_returns_health_status(self, api_client_with_rag):
        """Test that root endpoint returns a health check response"""
        response = api_client_with_rag.get("/")

        assert response.status_code == 200
        data = response.json()

        # Verify basic health check response
        assert "status" in data
        assert data["status"] == "ok"

    def test_root_endpoint_has_message(self, api_client_with_rag):
        """Test that root endpoint includes a descriptive message"""
        response = api_client_with_rag.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert isinstance(data["message"], str)
        assert len(data["message"]) > 0


@pytest.mark.api
class TestErrorHandling:
    """Tests for API error handling"""

    def test_query_handles_rag_system_error_gracefully(self):
        """Test that query endpoint handles RAG system errors gracefully"""
        from fastapi.testclient import TestClient
        from test_app import create_test_app

        # Create a client with a broken RAG system
        broken_rag = Mock()
        broken_rag.query.side_effect = Exception("Database connection failed")
        broken_rag.session_manager.create_session.return_value = "test-session"

        # Create test app with the broken RAG system
        test_app = create_test_app(rag_system=broken_rag)
        client = TestClient(test_app)

        request_data = {"query": "What is RAG?", "session_id": None}
        response = client.post("/api/query", json=request_data)

        # Should return 500 error
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_courses_handles_analytics_error_gracefully(self):
        """Test that courses endpoint handles analytics errors gracefully"""
        from fastapi.testclient import TestClient
        from test_app import create_test_app

        # Create a client with a broken RAG system
        broken_rag = Mock()
        broken_rag.get_course_analytics.side_effect = Exception("Analytics service unavailable")

        # Create test app with the broken RAG system
        test_app = create_test_app(rag_system=broken_rag)
        client = TestClient(test_app)

        response = client.get("/api/courses")

        # Should return 500 error
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_unsupported_http_method_on_query(self, api_client_with_rag):
        """Test that unsupported HTTP methods return error"""
        # GET on a POST endpoint
        response = api_client_with_rag.get("/api/query")
        assert response.status_code == 405  # Method Not Allowed

    def test_unsupported_http_method_on_courses(self, api_client_with_rag):
        """Test that unsupported HTTP methods return error"""
        # POST on a GET endpoint
        response = api_client_with_rag.post("/api/courses", json={})
        assert response.status_code == 405  # Method Not Allowed

    def test_nonexistent_endpoint_returns_404(self, api_client_with_rag):
        """Test that accessing non-existent endpoint returns 404"""
        response = api_client_with_rag.get("/api/nonexistent")
        assert response.status_code == 404


@pytest.mark.api
class TestCORSAndHeaders:
    """Tests for CORS and HTTP headers (if applicable in test environment)"""

    def test_query_accepts_json_content_type(self, api_client_with_rag, sample_query_request):
        """Test that query endpoint accepts JSON content type"""
        response = api_client_with_rag.post(
            "/api/query",
            json=sample_query_request,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200

    def test_response_is_json(self, api_client_with_rag, sample_query_request):
        """Test that responses are JSON formatted"""
        response = api_client_with_rag.post("/api/query", json=sample_query_request)

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_courses_response_is_json(self, api_client_with_rag):
        """Test that courses endpoint returns JSON"""
        response = api_client_with_rag.get("/api/courses")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


@pytest.mark.api
@pytest.mark.integration
class TestEndToEndFlow:
    """Integration tests for complete API workflows"""

    def test_complete_query_flow(self, api_client_with_rag):
        """Test a complete query flow from start to finish"""
        # Step 1: Check available courses
        courses_response = api_client_with_rag.get("/api/courses")
        assert courses_response.status_code == 200
        courses_data = courses_response.json()
        assert courses_data["total_courses"] > 0

        # Step 2: Query about a topic
        query_request = {
            "query": "What is RAG and how does it work?",
            "session_id": None
        }
        query_response = api_client_with_rag.post("/api/query", json=query_request)
        assert query_response.status_code == 200
        query_data = query_response.json()

        # Verify we got an answer
        assert len(query_data["answer"]) > 0
        session_id = query_data["session_id"]

        # Step 3: Follow-up query in same session
        followup_request = {
            "query": "Can you explain more about embeddings?",
            "session_id": session_id
        }
        followup_response = api_client_with_rag.post("/api/query", json=followup_request)
        assert followup_response.status_code == 200
        followup_data = followup_response.json()

        # Should maintain same session
        assert followup_data["session_id"] == session_id
        assert len(followup_data["answer"]) > 0

    def test_parallel_sessions(self, api_client_with_rag):
        """Test that multiple sessions can be active simultaneously"""
        # Create first session
        request1 = {"query": "What is RAG?", "session_id": None}
        response1 = api_client_with_rag.post("/api/query", json=request1)
        session1 = response1.json()["session_id"]

        # Create second session
        request2 = {"query": "What are embeddings?", "session_id": None}
        response2 = api_client_with_rag.post("/api/query", json=request2)
        session2 = response2.json()["session_id"]

        # Sessions should be different
        assert session1 != session2

        # Both sessions should work independently
        request1_followup = {"query": "Tell me more about RAG", "session_id": session1}
        response1_followup = api_client_with_rag.post("/api/query", json=request1_followup)
        assert response1_followup.status_code == 200
        assert response1_followup.json()["session_id"] == session1

        request2_followup = {"query": "Tell me more about embeddings", "session_id": session2}
        response2_followup = api_client_with_rag.post("/api/query", json=request2_followup)
        assert response2_followup.status_code == 200
        assert response2_followup.json()["session_id"] == session2

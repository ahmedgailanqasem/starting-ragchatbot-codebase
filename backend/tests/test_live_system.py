"""
Live tests against the running RAG system to diagnose 'query failed' issue
"""
import requests
import pytest


BASE_URL = "http://localhost:8000"


class TestLiveSystem:
    """Tests against the live running system"""

    def test_server_is_running(self):
        """Test that the server is accessible"""
        try:
            response = requests.get(f"{BASE_URL}/")
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")

    def test_api_query_endpoint_exists(self):
        """Test that /api/query endpoint exists"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/query",
                json={"query": "test"}
            )
            assert response.status_code in [200, 400, 422, 500]
        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")

    def test_content_query_response(self):
        """Test actual content query to see the response"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/query",
                json={"query": "What is RAG?"}
            )
            print(f"\n=== QUERY: 'What is RAG?' ===")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")

            if response.status_code == 200:
                data = response.json()
                print(f"Answer: {data.get('answer', 'N/A')}")
                print(f"Sources: {data.get('sources', 'N/A')}")

                # Check if response contains 'query failed'
                answer = data.get('answer', '')
                if 'query failed' in answer.lower():
                    print("\n!!! FOUND 'query failed' IN RESPONSE !!!")
                    pytest.fail(f"Query returned 'query failed': {answer}")

        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")

    def test_multiple_content_queries(self):
        """Test multiple content queries to identify pattern"""
        test_queries = [
            "What is RAG?",
            "Tell me about vector databases",
            "How do embeddings work?",
            "What courses are available?",
            "Hello"
        ]

        try:
            for query in test_queries:
                response = requests.post(
                    f"{BASE_URL}/api/query",
                    json={"query": query}
                )

                print(f"\n=== QUERY: '{query}' ===")
                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get('answer', '')
                    sources = data.get('sources', [])

                    print(f"Answer length: {len(answer)} chars")
                    print(f"Sources count: {len(sources)}")
                    print(f"Answer preview: {answer[:200]}...")

                    if 'query failed' in answer.lower():
                        print(f"!!! 'query failed' in response for: {query}")
                        print(f"Full answer: {answer}")
                else:
                    print(f"Error response: {response.text}")

        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")

    def test_get_courses_endpoint(self):
        """Test /api/courses endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/api/courses")
            print(f"\n=== GET /api/courses ===")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Total courses: {data.get('total_courses', 0)}")
                print(f"Course titles: {data.get('course_titles', [])}")

        except requests.exceptions.ConnectionError:
            pytest.skip("Server is not running")


if __name__ == "__main__":
    # Run with: uv run pytest tests/test_live_system.py -v -s
    pytest.main([__file__, "-v", "-s"])

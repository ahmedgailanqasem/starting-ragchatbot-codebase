"""
Test application module for API testing

This module defines a FastAPI app specifically for testing purposes,
avoiding the static file mounting issue that occurs when importing from app.py
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional


# Pydantic models matching the main app
class QueryRequest(BaseModel):
    """Request model for course queries"""
    query: str
    session_id: Optional[str] = None


class SourceItem(BaseModel):
    """Represents a single source with optional link"""
    label: str
    link: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for course queries"""
    answer: str
    sources: List[SourceItem]
    session_id: str


class CourseStats(BaseModel):
    """Response model for course statistics"""
    total_courses: int
    course_titles: List[str]


def create_test_app(rag_system=None):
    """
    Create a test FastAPI application without static file mounting

    Args:
        rag_system: Optional RAG system instance to use for endpoints

    Returns:
        FastAPI application configured for testing
    """
    app = FastAPI(title="Test Course Materials RAG System")

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """Process a query and return response with sources"""
        if rag_system is None:
            raise HTTPException(status_code=503, detail="RAG system not initialized")

        try:
            session_id = request.session_id
            if not session_id:
                session_id = rag_system.session_manager.create_session()

            answer, sources = rag_system.query(request.query, session_id)
            source_items = [SourceItem(label=s["label"], link=s["link"]) for s in sources]

            return QueryResponse(
                answer=answer,
                sources=source_items,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """Get course analytics and statistics"""
        if rag_system is None:
            raise HTTPException(status_code=503, detail="RAG system not initialized")

        try:
            analytics = rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/")
    async def root():
        """Root endpoint for health check"""
        return {"status": "ok", "message": "RAG System API"}

    return app

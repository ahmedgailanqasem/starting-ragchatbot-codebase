# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **RAG (Retrieval-Augmented Generation) chatbot system** for querying course materials. It combines semantic search through ChromaDB with Anthropic's Claude API to provide intelligent, context-aware answers about course content.

**Tech Stack:** FastAPI + ChromaDB + Anthropic Claude + SentenceTransformers

## Essential Commands

### Running the Application
```bash
# Quick start (recommended)
./run.sh

# Manual start
cd backend && uv run uvicorn app:app --reload --port 8000
```

Access at:
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Dependency Management
```bash
# Install all dependencies
uv sync

# Install in editable mode (for development)
uv pip install -e .
```

### Environment Setup
Create `.env` file in root:
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Architecture

### High-Level Flow

**Two-Phase Process:**

1. **Startup Phase (Document Indexing)**
   - FastAPI `@app.on_event("startup")` triggers document loading
   - `DocumentProcessor` chunks documents (800 chars, 100 overlap)
   - Embeddings generated via SentenceTransformer
   - Stored in ChromaDB (persistent at `./chroma_db/`)

2. **Query Phase (User Request)**
   - User query → Frontend → FastAPI endpoint
   - `RAGSystem.query()` orchestrates the flow
   - **Two Claude API calls per query:**
     - Call #1: Claude decides whether to use search tool
     - Call #2: Claude synthesizes search results into answer
   - Session-based conversation history maintained

### Core Component Responsibilities

**RAGSystem (`rag_system.py`)** - Main orchestrator
- Coordinates document processing, AI generation, and search
- Manages session history through SessionManager
- Routes between DocumentProcessor, VectorStore, and AIGenerator

**AIGenerator (`ai_generator.py`)** - Claude API interaction
- Makes two API calls per query (tool decision → synthesis)
- System prompt guides tool usage: "one search maximum"
- Temperature=0, max_tokens=800 for deterministic responses

**VectorStore (`vector_store.py`)** - ChromaDB interface
- Two collections: `course_catalog` (metadata) and `course_content` (chunks)
- Semantic search with configurable filters (course name, lesson number)
- Returns top-K results (default: 5)

**DocumentProcessor (`document_processor.py`)** - Text chunking
- Expects structured format: Course Title/Link/Instructor (lines 1-3), then lessons
- Sentence-based chunking with overlap for context preservation
- Adds contextual prefixes: "Course X Lesson Y content: ..."

**ToolManager & CourseSearchTool (`search_tools.py`)** - Tool execution
- Implements Anthropic tool-calling pattern
- `CourseSearchTool` wraps VectorStore for Claude to use
- Tracks sources for citation in UI

**SessionManager (`session_manager.py`)** - Conversation context
- Maintains per-session conversation history
- Configurable history length (default: 2 exchanges)

### Data Models (`models.py`)
- `Course`: title, instructor, course_link, lessons[]
- `Lesson`: lesson_number, title, lesson_link
- `CourseChunk`: content, course_title, lesson_number, chunk_index

## Important Architectural Patterns

### Why Two Claude API Calls?

**Call #1 (Tool Decision):**
- Claude receives user query + available tools
- Autonomously decides if search is needed
- Returns tool use request with search parameters

**Call #2 (Answer Synthesis):**
- Claude receives original query + search results
- Synthesizes multiple sources into coherent answer
- No tools available (prevents infinite loops)

This pattern allows Claude to:
- Skip search for general knowledge questions
- Determine optimal search parameters
- Provide grounded answers with source attribution

### Tool-Based Architecture

The system uses Anthropic's tool calling (formerly function calling):
- Tools defined with JSON schema (`search_tools.py`)
- Claude chooses when and how to use tools
- System enforces "one search maximum" via system prompt
- Tool results added to conversation before final synthesis

### Document Processing Strategy

**Chunking approach:**
- Sentence-based splitting (handles abbreviations)
- 800 character target, 100 character overlap
- Preserves context across chunk boundaries
- First chunk of each lesson gets special prefix

**Why sentence-based?**
- Avoids mid-sentence cuts that break semantic meaning
- Overlap ensures no information loss at boundaries
- Variable chunk size better than fixed character splitting

### Vector Search Flow

1. Query embedded using same model as documents (`all-MiniLM-L6-v2`)
2. ChromaDB performs cosine similarity search
3. Optional filters applied (course name, lesson number)
4. Top-K results returned with metadata
5. Sources tracked for UI citation

## Configuration (`backend/config.py`)

Critical settings that affect behavior:
- `CHUNK_SIZE`: 800 - Balance between context and precision
- `CHUNK_OVERLAP`: 100 - Prevents context loss
- `MAX_RESULTS`: 5 - Search results per query
- `MAX_HISTORY`: 2 - Conversation exchanges to remember
- `ANTHROPIC_MODEL`: claude-sonnet-4-20250514

## Document Format Expectations

Documents in `docs/` folder should follow this structure:
```
Course Title: [title]
Course Link: [url]
Course Instructor: [name]

Lesson 0: Introduction
Lesson Link: [url]
[lesson content...]

Lesson 1: Next Topic
[content...]
```

Supported formats: `.txt`, `.pdf`, `.docx`

## Frontend-Backend Contract

**POST /api/query**
```json
Request: {
  "query": "What is RAG?",
  "session_id": "session_abc" // optional, created if null
}

Response: {
  "answer": "RAG is...",
  "sources": ["Course Title - Lesson 2", ...],
  "session_id": "session_abc"
}
```

**GET /api/courses**
```json
Response: {
  "total_courses": 4,
  "course_titles": ["Course 1", "Course 2", ...]
}
```

## Development Notes

### Adding New Documents
- Place in `docs/` folder
- Server auto-loads on startup via `@app.on_event("startup")`
- Deduplication prevents re-processing existing courses

### Modifying Search Behavior
- Tool definition in `search_tools.py:27-50`
- System prompt in `ai_generator.py:8-30`
- Search implementation in `vector_store.py:61-100`

### Session Management
- Sessions created on first query if not provided
- History limited by `MAX_HISTORY` config
- No persistence - sessions reset on server restart

### ChromaDB Storage
- Persistent at `./chroma_db/`
- Delete folder to rebuild index from scratch
- Two collections: catalog (metadata) + content (chunks)

## Common Pitfalls

1. **pyproject.toml package discovery**: Must specify `packages = ["backend"]` in `[tool.setuptools]` due to multiple top-level directories
2. **Two API calls are intentional**: Don't optimize away - it's the core pattern
3. **Temperature=0**: Deterministic responses important for consistent citations
4. **Session history formatting**: Must be plain text string, not structured objects
5. **Tool result format**: Must match `{"type": "tool_result", "tool_use_id": ..., "content": ...}` exactly

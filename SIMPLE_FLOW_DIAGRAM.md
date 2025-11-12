# RAG Chatbot - Simple Flow Diagram

## System Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Browser   │◄───────►│   FastAPI   │◄───────►│   Claude    │
│  (Frontend) │  HTTP   │  (Backend)  │   API   │    API      │
└─────────────┘         └──────┬──────┘         └─────────────┘
                               │
                               │
                        ┌──────┴──────┐
                        │             │
                   ┌────▼────┐   ┌────▼────┐
                   │ChromaDB │   │ Session │
                   │ Vector  │   │ Manager │
                   │  Store  │   │         │
                   └─────────┘   └─────────┘
```

---

## Startup Flow (Document Processing)

```
1. Load Documents        2. Parse & Chunk         3. Store Vectors
   (docs/*.txt)    ──►    (800 char chunks)  ──►   (ChromaDB)
                           with 100 overlap

Result: 4 courses → 528 chunks → 528 embeddings
```

---

## Query Flow (User Asks Question)

```
┌──────────────────────────────────────────────────────────────────┐
│                      "What is RAG?"                              │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │    Frontend     │
                    │  POST /api/query│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    FastAPI      │
                    │  Create Session │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   RAG System    │
                    │  Get History    │
                    └────────┬────────┘
                             │
                             ▼
            ┌────────────────────────────────┐
            │    Claude API Call #1          │
            │  "Should I search courses?"    │
            │  Response: "Yes, search RAG"   │
            └────────────┬───────────────────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │    Vector Search        │
            │  1. Embed query         │
            │  2. Find similar chunks │
            │  3. Return top 5        │
            └────────────┬────────────┘
                         │
                         ▼
            ┌────────────────────────────────┐
            │    Claude API Call #2          │
            │  Receives: Search results      │
            │  Returns: Synthesized answer   │
            └────────────┬───────────────────┘
                         │
                         ▼
                    ┌─────────────────┐
                    │  Save to Session│
                    │  Return Response│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Frontend     │
                    │  Display Answer │
                    │  Show Sources   │
                    └─────────────────┘
```

---

## Key Components

| Component | Purpose |
|-----------|---------|
| **Frontend** | User interface (HTML/CSS/JS) |
| **FastAPI** | REST API server |
| **RAG System** | Orchestrates the flow |
| **Document Processor** | Chunks documents (800 chars) |
| **Vector Store** | ChromaDB semantic search |
| **AI Generator** | Calls Claude API (2x per query) |
| **Session Manager** | Tracks conversation history |
| **Tool Manager** | Executes search tool |

---

## Data Flow Summary

```
User Query
    ↓
Frontend (JavaScript)
    ↓
Backend API (FastAPI)
    ↓
RAG System (Python)
    ↓
├─► Session Manager (Get History)
│
├─► Claude API #1 (Decide to search)
│
├─► Tool Manager (Execute search)
│   ├─► Vector Store (Semantic search)
│   └─► ChromaDB (Find similar chunks)
│
├─► Claude API #2 (Synthesize answer)
│
└─► Session Manager (Save exchange)
    ↓
Return to Frontend
    ↓
Display to User
```

---

## Two Claude API Calls

```
Call #1: Decision Phase
├─ Input: User question + available tools
├─ Output: "Use search_course_content tool"
└─ Purpose: Let Claude decide if search is needed

Call #2: Answer Phase
├─ Input: User question + search results
├─ Output: Final synthesized answer
└─ Purpose: Generate answer from retrieved context
```

---

## Vector Search Process

```
1. Query Text
   "What is RAG?"
       ↓
2. Embedding
   [0.23, -0.15, 0.67, ...] (384 dimensions)
       ↓
3. Similarity Search
   Compare with 528 stored embeddings
       ↓
4. Top 5 Results
   Most similar chunks returned
       ↓
5. Format & Return
   "[Course - Lesson] content..."
```

---

## Current Setup

```
✅ Server: http://localhost:8000
✅ Courses: 4
✅ Chunks: 528
✅ Embeddings: 528
⚠️  API Credits: Needed for queries
```

---

## File Structure

```
.
├── frontend/
│   ├── index.html      → Chat UI
│   ├── script.js       → API calls & display
│   └── style.css       → Styling
│
├── backend/
│   ├── app.py          → FastAPI endpoints
│   ├── rag_system.py   → Main orchestrator
│   ├── ai_generator.py → Claude API calls
│   ├── vector_store.py → ChromaDB interface
│   ├── document_processor.py → Text chunking
│   ├── search_tools.py → Search tool
│   └── session_manager.py → Conversation history
│
└── docs/
    └── *.txt           → Course documents
```

---

## Quick Summary

**What it does:** Answers questions about course materials using RAG (Retrieval-Augmented Generation)

**How it works:**
1. Loads course documents and creates searchable embeddings
2. User asks a question via web interface
3. Claude decides if it needs to search the courses
4. System searches vector database for relevant content
5. Claude synthesizes the search results into an answer
6. User sees answer with source citations

**Tech Stack:** FastAPI + ChromaDB + Claude + SentenceTransformers

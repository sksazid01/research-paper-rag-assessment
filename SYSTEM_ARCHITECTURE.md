# RAG System Architecture - Detailed Workflow

## Overview

This document describes the complete system architecture for the Research Paper RAG (Retrieval-Augmented Generation) Assessment system. The system enables PDF upload, intelligent chunking, semantic search, and retrieval of research paper content.

---

## System Components Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (Frontend)                       │
│                     (Postman/Browser/API Client)                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ HTTP/REST API
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                    FastAPI Backend Server                       │
│                        (routes.py)                              │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  File Upload  │    │  Query Endpoint  │    │ Delete Endpoint │
│   /upload     │    │    /query        │    │    /delete      │
└───────┬───────┘    └────────┬─────────┘    └────────┬────────┘
        │                     │                       │
        │                     │                       │
┌───────▼─────────────────────▼───────────────────────▼────────┐
│                   Core Processing Layer                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ PDF Processor   │  │  Chunking    │  │  Embedding       │ │
│  │ (PyPDF2)        │  │  Service     │  │  Service         │ │
│  │                 │  │              │  │  (sentence-      │ │
│  │ • Extract text  │  │ • Sentence   │  │   transformers)  │ │
│  │ • Extract meta  │  │   grouping   │  │                  │ │
│  │ • Page info     │  │ • Max 1000   │  │                  │ │
│  │                 │  │        chars │  │ • 384-dim        │ │
│  │                 │  │              │  │   vectors        │ │
│  └─────────────────┘  └──────────────┘  └──────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                                │
                                │
        ┌───────────────────────┼──────────────────────┐
        │                       │                      │
        ▼                       ▼                      ▼
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ PostgreSQL DB │    │  Qdrant Vector   │    │  Local File     │
│  (ragdb)      │    │     Database     │    │  System (temp/) │
├───────────────┤    ├──────────────────┤    ├─────────────────┤
│ • papers      │    │ • Vector store   │    │ • PDFs          │
│ • queries     │    │ • 384-dim embed  │    │ • JSON chunks   │
│ • query_papers│    │ • HNSW index     │    │                 │
│               │    │ • Cosine sim     │    │                 │
│               │    │   search         │    │                 │
│               │    │ • Payload index  │    │                 │
└───────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Detailed Workflow Diagrams

### 1. Upload & Indexing Pipeline

```
             ┌─────────────┐
             │  User sends │
             │  PDF files  │
             └──────┬──────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  Step 1: Pre-processing Validation      │
├─────────────────────────────────────────┤
│ • Check file type (.pdf extension)      │
│ • Check MIME type (application/pdf)     │
│ • Check duplicates in batch             │
│ • Check duplicates in database          │
│ • Reject if validation fails            │
└──────────────────┬──────────────────────┘
                   │ ✓ Valid
                   ▼
┌─────────────────────────────────────────┐
│  Step 2: File Storage                   │
├─────────────────────────────────────────┤
│ • Save to temp/ directory               │
│ • Keep original filename                │
│ • Binary write mode                     │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 3: PDF Extraction (PyPDF2)        │
├─────────────────────────────────────────┤
│ • Open PDF with PyPDF2.PdfReader        │
│ • Extract metadata from PDF info:       │
│   - Title (with validation)             │
│   - Authors (with heuristics)           │
│   - Year (regex pattern matching)       │
│   - Page count                          │
│ • Extract text per page (PyPDF2)        │
│ • Detect sections with regex patterns   │
│ • Split into sentences per section      │
│ • Return: (metadata, sentences[])       │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 4: Chunking Strategy              │
├─────────────────────────────────────────┤
│ • Group sentences into chunks           │
│ • Max 1000 characters per chunk         │
│ • 150 character overlap between chunks  │
│ • Preserve section boundaries (flush)   │
│ • Track page_start, page_end            │
│ • Assign chunk_index (0,1,2...)         │
│                                         │
│ Chunk structure:                        │
│  {                                      │
│    "text": "...",                       │
│    "section": "Introduction",           │
│    "page_start": 1,                     │
│    "page_end": 2,                       │
│    "chunk_index": 0                     │
│  }                                      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 5: Embedding Generation           │
├─────────────────────────────────────────┤
│ • Use sentence-transformers model       │
│ • Model: all-MiniLM-L6-v2               │
│ • Output: 384-dimensional vectors       │
│ • Process in batches for efficiency     │
│ • Each chunk → one 384-dim vector       │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 6: Database Operations            │
├─────────────────────────────────────────┤
│                                         │
│  A) PostgreSQL (ragdb):                 │
│     • INSERT INTO papers                │
│     • Get auto-generated paper_id       │
│     • Store: title, authors, year,      │
│              filename, pages, created_at│
│     • Using SQLAlchemy ORM              │
│                                         │
│  B) Qdrant Vector DB:                   │
│     • Create/ensure collection          │
│     • Dimension: 384                    │
│     • Distance: Cosine similarity       │
│     • HNSW indexing (m=16, ef=100)      │
│     • Payload index on paper_id         │
│     • Generate UUID-based point IDs     │
│     • Upsert vectors with payload:      │
│       {                                 │
│         "paper_id": 123,                │
│         "paper_title": "...",           │
│         "section": "Methods",           │
│         "page_start": 5,                │
│         "page_end": 6,                  │
│         "chunk_index": 12,              │
│         "text": "full chunk text..."    │
│       }                                 │
│                                         │
│  C) Local filesystem:                   │
│     • Save chunks as JSON for debug     │
│     • File: {filename}_chunks.json      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 7: Response                       │
├─────────────────────────────────────────┤
│  Return JSON:                           │
│  {                                      │
│    "processed": [...],                  │
│    "summary": {                         │
│      "total": 3,                        │
│      "successful": 2,                   │
│      "failed": 1                        │
│    }                                    │
│  }                                      │
└─────────────────────────────────────────┘
```

### 2. Query & Retrieval Pipeline

```
┌──────────────┐
│ User sends   │
│ text query   │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Step 1: Query Embedding                │
├─────────────────────────────────────────┤
│ • Use same embedding model              │
│ • Convert query → 384-dim vector        │
│ • Example: "What is machine learning?"  │
│   → [0.123, -0.456, 0.789, ...]         │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 2: Vector Similarity Search       │
├─────────────────────────────────────────┤
│ • Search Qdrant with query vector       │
│ • Use cosine similarity                 │
│ • Get top_k results (default: 5)        │
│ • Each result contains:                 │
│   - Similarity score (0-1)              │
│   - Chunk text                          │
│   - Metadata (paper_id, title, section) │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 3: Post-processing                │
├─────────────────────────────────────────┤
│ • Filter by minimum score threshold     │
│ • Sort by relevance score               │
│ • Enrich with paper metadata from DB    │
│ • Group by paper_id if needed           │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 4: Return Results                 │
├─────────────────────────────────────────┤
│  {                                      │
│    "query": "machine learning",         │
│    "results": [                         │
│      {                                  │
│        "score": 0.87,                   │
│        "paper_id": 5,                   │
│        "paper_title": "ML Survey",      │
│        "section": "Introduction",       │
│        "text": "Machine learning is...",│
│        "page_start": 2,                 │
│        "page_end": 3                    │
│      },                                 │
│      ...                                │
│    ]                                    │
│  }                                      │
└─────────────────────────────────────────┘
```

### Realtime Streaming (SSE) Flow

```
Client (Accept: text/event-stream)
  │ POST /query/stream { question, top_k, paper_ids?, model? }
  ▼
Backend builds contexts → reranks (CrossEncoder) → assembles prompt → streams LLM tokens
  │
  ├─ data: {"type":"token","content":"..."}
  ├─ data: {"type":"token","content":"..."}
  ├─ data: {"type":"metadata","citations":[...],"sources_used":[...],"confidence":0.xx,"paper_ids_used":[...]}
  └─ data: {"type":"done"}
```

Operational details:
- Initial `:\n\n` SSE comment flushes the stream early.
- Response headers disable buffering and caching for low latency.
- Frontend splits on double newlines and parses each `data:` line JSON.

### 3. Delete Pipeline

```
┌──────────────┐
│ User sends   │
│ paper_id     │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Step 1: Verify Paper Exists            │
├─────────────────────────────────────────┤
│ • Query PostgreSQL for paper_id         │
│ • Return 404 if not found               │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 2: Delete from PostgreSQL         │
├─────────────────────────────────────────┤
│ DELETE FROM papers WHERE id = ?         │
│ CASCADE deletes query_papers entries    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 3: Delete from Qdrant             │
├─────────────────────────────────────────┤
│ • Query all vectors with paper_id       │
│ • Delete matching vectors               │
│ • Remove all chunks for that paper      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 4: (Optional) Clean filesystem    │
├─────────────────────────────────────────┤
│ • Remove PDF from temp/                 │
│ • Remove chunks JSON                    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Return: {"status": "deleted"}          │
└─────────────────────────────────────────┘
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Framework** | FastAPI | REST endpoints, async support, auto docs |
| **PDF Processing** | PyPDF2 + pdfminer.six | Text extraction, metadata parsing, layout analysis |
| **Embedding Model** | sentence-transformers<br/>(all-MiniLM-L6-v2) | Generate 384-dim semantic vectors |
| **Vector Store** | Qdrant | Similarity search, HNSW indexing, metadata filtering |
| **Metadata Store** | PostgreSQL + SQLAlchemy | Paper metadata, query history, deduplication |
| **Chunking** | Custom logic | Max 1000 chars, 150 char overlap, section-aware |
| **Concurrency** | asyncio.Semaphore(3) | Process 3 PDFs in parallel |
| **Frontend** | Next.js + TypeScript | User interface |
| **Containerization** | Docker + Docker Compose | Multi-service orchestration |

---

## Data Models

### PostgreSQL Schema (ragdb)

```sql
-- Papers table: stores research paper metadata
CREATE TABLE papers (
    id SERIAL PRIMARY KEY,
    title VARCHAR(512),
    authors VARCHAR(1024),
    year VARCHAR(8),
    filename VARCHAR(512) NOT NULL,
    pages INTEGER,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Queries table: tracks user queries and performance
CREATE TABLE queries (
    id SERIAL PRIMARY KEY,
    question VARCHAR(2000) NOT NULL,
    response_time_ms INTEGER,
    confidence VARCHAR(16),
    rating INTEGER,  -- User satisfaction rating (1-5)
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Query-Paper junction table: links queries to papers
CREATE TABLE query_papers (
    id SERIAL PRIMARY KEY,
    query_id INTEGER REFERENCES queries(id) ON DELETE CASCADE,
    paper_id INTEGER REFERENCES papers(id) ON DELETE SET NULL
);
```

### Qdrant Vector Payload

```json
{
  "paper_id": 123,
  "paper_title": "Deep Learning Survey",
  "section": "Introduction",
  "page_start": 1,
  "page_end": 2,
  "chunk_index": 0,
  "text": "Full text of the chunk..."
}
```

### Chunk Structure (JSON)

```json
{
  "text": "Machine learning is a subset of artificial intelligence...",
  "section": "Introduction",
  "page_start": 1,
  "page_end": 2,
  "chunk_index": 0,
  "token_count": 128
}
```

---

## API Endpoints

### POST /papers/upload
Upload one or more PDF research papers.

**Request:**
- Content-Type: `multipart/form-data`
- Field: `files[]` (array of PDF files)

**Response:**
```json
{
  "processed": [
    {
      "filename": "paper1.pdf",
      "paper_id": 5,
      "chunks": 23,
      "status": "success"
    }
  ],
  "summary": {
    "total": 1,
    "successful": 1,
    "failed": 0
  }
}
```

### POST /query
Search papers using semantic similarity.

**Request:**
```json
{
  "query": "What are the applications of deep learning?",
  "top_k": 5,
  "min_score": 0.5
}
```

**Response:**
```json
{
  "query": "What are the applications of deep learning?",
  "results": [
    {
      "score": 0.87,
      "paper_id": 5,
      "paper_title": "Deep Learning Survey",
      "section": "Applications",
      "text": "Deep learning has applications in...",
      "page_start": 10,
      "page_end": 11
    }
  ]
}
```

### POST /query/stream (SSE)
Stream tokenized answers in real time using Server-Sent Events.

Request:
- Method: POST
- Headers: `Accept: text/event-stream`
- Body (JSON):
```json
{
  "question": "What are the applications of deep learning?",
  "top_k": 5,
  "paper_ids": [1, 3],
  "model": "llama3"
}
```

Response:
- Content-Type: `text/event-stream; charset=utf-8`
- Headers: `Cache-Control: no-cache, no-transform`, `Connection: keep-alive`, `X-Accel-Buffering: no`
- Streamed events (each line begins with `data: ` and ends with a blank line):
```
:

data: {"type":"token","content":"Deep"}

data: {"type":"token","content":" learning"}

data: {"type":"metadata","citations":[...],"sources_used":["paper1.pdf"],"confidence":0.82,"paper_ids_used":[5]}

data: {"type":"done"}

```

Possible event types:
- `token`: incremental chunk of the answer
- `metadata`: citations, sources, confidence, paper_ids used
- `done`: completion sentinel
- `error`: error details if the stream fails

Notes:
- The server sends an initial SSE comment `:\n\n` to open the stream promptly.
- The backend uses FastAPI `StreamingResponse` and streams from the LLM client.
- Ensure reverse proxies (e.g., Nginx) don’t buffer SSE (handled via `X-Accel-Buffering: no`).

### DELETE /papers/{paper_id}
Delete a paper and all its associated data.

**Response:**
```json
{
  "status": "deleted",
  "paper_id": 5
}
```

### GET /papers
List all uploaded papers.

**Response:**
```json
{
  "papers": [
    {
      "id": 5,
      "title": "Deep Learning Survey",
      "authors": "Smith, J. et al.",
      "year": 2023,
      "filename": "deep_learning.pdf",
      "pages": 25
    }
  ]
}
```

---

## Data Flow Summary

```
┌─────────┐
│   PDF   │
└────┬────┘
     │
     ▼
┌─────────────┐
│   Extract   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Chunk     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Embed     │ (384-dim vectors)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Store     │ (Qdrant + PostgreSQL)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Query     │ ← User text query
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Embed     │ (Query → vector)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Search    │ (Cosine similarity)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Retrieve   │ (Top-k results)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Return    │ → User
└─────────────┘
```

---

## Key Features

### 1. **Intelligent Chunking**
- Respects section boundaries (Abstract, Introduction, Methods, etc.)
- Maximum 1000 characters per chunk
- 150 character overlap between consecutive chunks for context continuity
- Preserves page information for citation
- Assigns sequential chunk indices
- Flushes buffer on section change to maintain semantic coherence

### 2. **Semantic Search**
- 384-dimensional embeddings using sentence-transformers (all-MiniLM-L6-v2)
- Cosine similarity for relevance scoring
- HNSW (Hierarchical Navigable Small World) indexing for O(log n) search complexity
- Payload indexing on paper_id for fast filtering
- LRU cache for query embeddings (max 100 entries)
- Optional score threshold filtering
- Metadata-rich results

### 3. **Concurrent Processing**
- Async file upload handling
- Semaphore-limited parallel processing (max 3 PDFs at once)
- Non-blocking I/O operations

### 4. **Robust Validation**
- File type checking (extension + MIME)
- Duplicate detection (batch + database)
- Error handling with detailed messages

### 5. **Metadata Preservation**
- Paper title, authors, year extraction
- Page tracking for each chunk
- Section labeling for context

---

## Performance Considerations

- **Embedding Generation:** Batched for efficiency (default batch_size=64)
- **Query Caching:** LRU cache for repeated query embeddings (MD5-hashed keys)
- **Concurrent Uploads:** Limited to 3 simultaneous PDFs to avoid CPU thrashing
- **Vector Search:** O(log n) complexity with Qdrant HNSW index (m=16, ef_construct=100)
- **Payload Indexing:** Integer index on paper_id for fast filtering
- **Database:** PostgreSQL with connection pooling for concurrent access
- **Chunk Overlap:** 150 chars overlap maintains context across boundaries
- **UUID Generation:** Random IDs avoid collisions in concurrent uploads

---

## Error Handling

- **Invalid file type:** HTTP 422 with detailed message
- **Duplicate file:** HTTP 409 with existing paper_id
- **Processing failure:** Individual file errors don't block batch
- **Empty PDF:** Validation catches zero-chunk documents

---

## Future Enhancements

- [ ] Add reranking for improved relevance
- [ ] Support for more document formats (DOCX, TXT)
- [ ] Multi-language support
- [ ] Advanced filtering (by year, author, section)
- [ ] Query result highlighting
- [ ] Citation extraction and linking
- [ ] Full-text LLM integration for answer generation

---

## Directory Structure

```
research-paper-rag-assessment/
├── src/
│   ├── api/
│   │   └── routes.py          # API endpoints
│   ├── services/
│   │   ├── pdf_processor.py   # PDF extraction
│   │   ├── chunking.py        # Text chunking
│   │   ├── embedding_service.py # Embeddings
│   │   ├── qdrant_client.py   # Vector DB
│   │   └── rag_pipeline.py    # Query pipeline
│   ├── models/
│   │   └── db.py              # PostgreSQL operations
│   └── main.py                # FastAPI app
├── temp/                      # Uploaded PDFs + chunks
├── frontend/                  # Next.js UI
├── tests/                     # Unit + integration tests
├── docker-compose.yml         # Orchestration
└── requirements.txt           # Python dependencies
```

---

## Deployment

### Docker Compose

```bash
docker-compose up -d
```

Services:
- **Backend (api):** FastAPI on port 8000 (host network mode)
- **PostgreSQL:** Database on port 5433 (mapped from container 5432)
- **Qdrant:** Vector DB on ports 6333 (HTTP) and 6334 (gRPC)
- **Frontend:** Next.js on port 3456

Environment Variables:
- `DATABASE_URL`: PostgreSQL connection string
- `QDRANT_HOST`, `QDRANT_PORT`: Qdrant connection settings
- `QDRANT_COLLECTION`: Collection name (default: research_papers)
- `OLLAMA_BASE_URL`: LLM service endpoint (optional)

### Manual Setup

```bash
# Backend
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://rag_user:rag_pass@localhost:5433/ragdb"
export QDRANT_HOST="localhost"
export QDRANT_PORT="6333"
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend
npm install
export NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

---

**Last Updated:** November 3, 2025

# Research Paper RAG System - API Documentation

## Intelligent Query System (`POST /api/query`)

### Overview
The Query System uses Retrieval-Augmented Generation (RAG) to answer questions about uploaded research papers. It retrieves relevant context from the vector database, generates answers using a local LLM (Ollama), and provides citations with confidence scores.

### Endpoint
```
POST /api/query
Content-Type: application/json
```

### Request Body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `question` | string | ✅ Yes | - | The question to answer |
| `top_k` | integer | ❌ No | 5 | Number of relevant chunks to retrieve (1-50) |
| `paper_ids` | array[int] | ❌ No | null | Limit search to specific papers (by database ID) |
| `model` | string | ❌ No | "llama3" | Ollama model to use for generation |

### Response Format

```json
{
  "answer": "The transformer paper uses a self-attention mechanism...",
  "citations": [
    {
      "paper_title": "Attention is All You Need",
      "section": "Methodology",
      "page": "3-4",
      "relevance_score": 0.89
    }
  ],
  "sources_used": ["paper3_nlp_transformers.pdf"],
  "confidence": 0.85
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Generated answer based on retrieved context |
| `citations` | array | List of sources cited in the answer |
| `citations[].paper_title` | string | Title of the cited paper |
| `citations[].section` | string | Section where information was found (e.g., "Methods", "Results") |
| `citations[].page` | string | Page range (e.g., "3-4") |
| `citations[].relevance_score` | float | Similarity score (0.0-1.0) indicating relevance |
| `sources_used` | array[string] | List of paper filenames used |
| `confidence` | float | Overall confidence score (0.0-1.0) |

### Examples

#### Example 1: Simple Query
```bash
curl -X POST "http://127.0.0.1:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is blockchain scalability?",
    "top_k": 5
  }'
```

**Response:**
```json
{
  "answer": "Blockchain scalability refers to the ability of a blockchain network to handle an increasing number of transactions and users efficiently...",
  "citations": [
    {
      "paper_title": "Sustainability in Blockchain",
      "section": "Introduction",
      "page": "2-3",
      "relevance_score": 0.92
    }
  ],
  "sources_used": ["paper_1.pdf"],
  "confidence": 0.87
}
```

#### Example 2: Query with Paper Filter
```bash
curl -X POST "http://127.0.0.1:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What methodology was used?",
    "top_k": 3,
    "paper_ids": [1, 3]
  }'
```

**Response:**
```json
{
  "answer": "The methodology involved...",
  "citations": [
    {
      "paper_title": "Research Paper Title",
      "section": "Methods",
      "page": "5-6",
      "relevance_score": 0.88
    }
  ],
  "sources_used": ["paper_1.pdf"],
  "confidence": 0.82
}
```

#### Example 3: Python Client
```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/api/query",
    json={
        "question": "What are the main challenges in blockchain?",
        "top_k": 5
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")
print(f"Sources: {result['sources_used']}")

for citation in result['citations']:
    print(f"  - {citation['paper_title']} ({citation['section']}, p.{citation['page']})")
```

### Error Responses

#### 422 Unprocessable Entity
```json
{
  "detail": "Field 'question' is required and cannot be empty"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Query processing failed: [error details]"
}
```

### How It Works

1. **Query Embedding**: Your question is converted to a vector using sentence-transformers
2. **Retrieval**: Top-k most similar chunks are retrieved from Qdrant vector database
3. **Filtering**: If `paper_ids` is provided, only chunks from those papers are considered
4. **Context Assembly**: Retrieved chunks are formatted with metadata (title, section, page)
5. **LLM Generation**: Ollama generates an answer with explicit citation instructions
6. **Citation Extraction**: Citations are parsed and mapped to source metadata
7. **Confidence Calculation**: Score based on retrieval quality and answer characteristics

### Confidence Score

The confidence score (0.0-1.0) is calculated based on:
- Average relevance scores of top retrieved chunks (weighted by rank)
- Presence of citations in the answer (+0.1 boost)
- Uncertainty phrases like "I don't know" (-0.2 penalty)

Higher confidence indicates the system found relevant information and generated a well-supported answer.

### Best Practices

1. **Use specific questions**: More specific questions yield better results
   - ✅ Good: "What methodology was used to evaluate blockchain scalability?"
   - ❌ Poor: "Tell me about the paper"

2. **Filter by paper_ids**: When you know which papers are relevant
   ```json
   { "question": "...", "paper_ids": [1, 3, 5] }
   ```

3. **Adjust top_k**: 
   - Smaller (3-5): Fast, focused answers
   - Larger (10-20): More comprehensive, but slower

4. **Check confidence**: Low confidence (<0.5) may indicate insufficient information

5. **Use citations**: Citations show which parts of which papers support the answer

### Testing

Run the provided test scripts:

```bash
# Bash script
./test_query_api.sh

# Python script
python test_query_examples.py
```

### Requirements

- Server running: `uvicorn src.main:app --reload`
- Papers uploaded via `/api/papers/upload`
- Ollama running locally with `llama3` model
- Qdrant vector database accessible

---

## Upload System (`POST /api/papers/upload`)

### Overview
Upload research papers (PDFs) for processing and indexing.

### Endpoint
```
POST /api/papers/upload
Content-Type: multipart/form-data
```

### Request

Upload files using form field `files` or `file` (supports multiple):

```bash
curl -X POST "http://127.0.0.1:8000/api/papers/upload" \
  -F "files=@sample_papers/paper_1.pdf" \
  -F "files=@sample_papers/paper_2.pdf"
```

### Response
```json
{
  "processed": [
    {
      "filename": "paper_1.pdf",
      "paper_id": 1,
      "metadata": {
        "title": "Sustainability in Blockchain",
        "authors": "...",
        "year": "2023",
        "pages": 24
      },
      "chunks": 119,
      "chunks_file": "temp/paper_1_chunks.json"
    }
  ]
}
```

---

## Full API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/papers/upload` | POST | Upload and process PDF papers |
| `/api/query` | POST | Query papers using RAG |

---

## Setup & Run

1. **Start Services**
```bash
# Qdrant
docker run -p 6333:6333 qdrant/qdrant

# PostgreSQL (via docker-compose)
docker-compose up -d postgres

# Ollama
ollama serve
ollama pull llama3
```

2. **Run API Server**
```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

3. **Upload Papers**
```bash
curl -X POST "http://127.0.0.1:8000/api/papers/upload" \
  -F "files=@sample_papers/paper_1.pdf"
```

4. **Query Papers**
```bash
curl -X POST "http://127.0.0.1:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is blockchain scalability?", "top_k": 5}'
```

---

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│   FastAPI Application           │
│  ┌────────────────────────────┐ │
│  │  RAG Pipeline              │ │
│  │  - Query embedding         │ │
│  │  - Vector search (Qdrant)  │ │
│  │  - Context assembly        │ │
│  │  - LLM generation (Ollama) │ │
│  │  - Citation extraction     │ │
│  └────────────────────────────┘ │
└────┬──────────────────┬─────────┘
     │                  │
     ▼                  ▼
┌─────────┐      ┌──────────────┐
│ Qdrant  │      │ PostgreSQL   │
│ Vectors │      │ Metadata     │
└─────────┘      └──────────────┘
```

---

## Support

For questions or issues, check:
- Task_Instructions.md
- APPROACH.md
- GitHub Issues

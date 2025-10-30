# 🎓 Research Paper RAG System

A production-ready Retrieval-Augmented Generation (RAG) service for querying academic research papers using vector search and LLMs.

## 🚀 Quick Start (One Command)

**Prerequisites:** 
- Docker and Docker Compose installed
- Ollama running on your host machine with `llama3` model

```bash
# 1. Install Ollama (one-time setup)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3

# 2. Clone and run the project
git clone <your-repo-url>
cd research-paper-rag-assessment
docker-compose up --build
```

That's it! The system will be ready at http://localhost:8000

**Quick test:**
```bash
curl -X POST -F "files=@sample_papers/paper_1.pdf" http://localhost:8000/api/papers/upload
```

**Note:** On first run, copy `.env.example` to `.env` if it doesn't exist:
```bash
cp .env.example .env
```

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Setup Instructions](#-setup-instructions)
- [API Documentation](#-api-documentation)
- [Usage Examples](#-usage-examples)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

### Core Features
- ✅ **PDF Upload & Processing** - Multi-file upload with section-aware extraction
- ✅ **Intelligent Query System** - RAG pipeline with citations and confidence scores
- ✅ **Paper Management** - CRUD operations for managing uploaded papers
- ✅ **Vector Search** - Semantic search using Qdrant vector database
- ✅ **Citation Extraction** - Automatic citation mapping with source tracking
- ✅ **Confidence Scoring** - AI-generated confidence levels for answers

### Technical Features
- 🐳 **Docker-Based** - One-command deployment
- 🔄 **Live Reload** - Development mode with auto-reload
- 🗄️ **PostgreSQL Storage** - Persistent metadata storage
- 🔍 **Qdrant Vector DB** - Fast similarity search
- 🤖 **Ollama Integration** - Local LLM for answer generation
- 📊 **Structured Responses** - JSON API with proper error handling

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client (HTTP)                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Application (Port 8000)             │
│  ┌──────────────────────────────────────────────────┐   │
│  │          Document Ingestion Pipeline             │   │
│  │  • PDF text extraction (PyPDF2)                  │   │
│  │  • Section-aware parsing (Abstract, Methods...)  │   │
│  │  • Intelligent chunking (semantic boundaries)    │   │
│  │  • Embedding generation (sentence-transformers)  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │              RAG Query Pipeline                   │   │
│  │  1. Query embedding                               │   │
│  │  2. Vector similarity search (Qdrant)            │   │
│  │  3. Context assembly with citations              │   │
│  │  4. LLM generation (Ollama/llama3)               │   │
│  │  5. Citation extraction & confidence scoring     │   │
│  └──────────────────────────────────────────────────┘   │
└────────┬────────────────────────┬───────────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────────┐
│   Qdrant DB     │    │   PostgreSQL DB      │
│  (Port 6333)    │    │   (Port 5433)        │
│                 │    │                      │
│ • Vector store  │    │ • Paper metadata     │
│ • Embeddings    │    │ • Author info        │
│ • Payloads      │    │ • Timestamps         │
└─────────────────┘    └──────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│      Ollama LLM Server          │
│      (Host: localhost:11434)    │
│                                 │
│  • Model: llama3                │
│  • Local inference              │
│  • No API costs                 │
└─────────────────────────────────┘
```

---

## 🛠️ Setup Instructions

### Prerequisites

1. **Docker & Docker Compose**
   ```bash
   # Check if installed
   docker --version
   docker-compose --version
   
   # Install if needed: https://docs.docker.com/get-docker/
   ```

2. **Ollama (for LLM)**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull the model
   ollama pull llama3
   
   # Verify it's running
   curl http://localhost:11434/api/tags
   ```

### Installation

#### Simple Setup (Just Docker)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd research-paper-rag-assessment

# 2. Create .env file (one-time)
cp .env.example .env

# 3. Start all services
docker-compose up --build
```

That's it! The system will:
- Build all Docker images
- Start API, PostgreSQL, and Qdrant
- Initialize databases
- Be ready at http://localhost:8000

#### Advanced: With User Permissions (Linux/macOS)

If you want files created by the container to match your user (avoids permission issues):

```bash
# Set your user ID
export UID=$(id -u)
export GID=$(id -g)

# Start services
docker-compose up --build
```

#### Using the Setup Script (Optional)

For automated checks and setup:
```bash
chmod +x setup.sh
./setup.sh
```

The script adds:
- ✅ Prerequisite validation (Docker, Ollama)
- ✅ Auto-detection of OS and user
- ✅ Service health checks
- ✅ Pretty output with status messages

### Verify Installation

```bash
# Check all services are running
docker-compose ps

# Test API health
curl http://localhost:8000/docs

# Test Qdrant
curl http://localhost:6333/collections
```

---

## 📡 API Documentation

### Base URL
```
http://localhost:8000
```

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

#### 1. Upload Papers
```http
POST /api/papers/upload
Content-Type: multipart/form-data

files: (multiple PDF files)
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/papers/upload" \
  -F "files=@sample_papers/paper_1.pdf" \
  -F "files=@sample_papers/paper_2.pdf"
```

**Response:**
```json
{
  "processed": [
    {
      "filename": "paper_1.pdf",
      "paper_id": 1,
      "metadata": {
        "title": "Sustainability in Blockchain",
        "authors": "Hani Alshahrani et al.",
        "year": "2023",
        "pages": 24
      },
      "chunks": 119
    }
  ]
}
```

#### 2. Query Papers (RAG)
```http
POST /api/query?question={query}&top_k={k}&model={model}&paper_ids={ids}
```

**Parameters:**
- `question` (required): Your research question
- `top_k` (optional, default=5): Number of chunks to retrieve
- `model` (optional, default=llama3): LLM model to use
- `paper_ids` (optional): Comma-separated paper IDs to filter

**Example:**
```bash
curl -X POST "http://localhost:8000/api/query?question=What%20is%20blockchain%3F&top_k=5"
```

**Response:**
```json
{
  "answer": "Based on the provided context, blockchain is defined as...",
  "citations": [
    {
      "paper_title": "Sustainability in Blockchain",
      "section": "Introduction",
      "page": "8-8",
      "relevance_score": 0.77
    }
  ],
  "sources_used": ["paper_1.pdf"],
  "confidence": 0.54
}
```

#### 3. List All Papers
```http
GET /api/papers
```

**Example:**
```bash
curl http://localhost:8000/api/papers
```

#### 4. Get Paper Details
```http
GET /api/papers/{id}
```

**Example:**
```bash
curl http://localhost:8000/api/papers/1
```

#### 5. Delete Paper
```http
DELETE /api/papers/{id}
```

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/papers/1
```

#### 6. Get Paper Statistics
```http
GET /api/papers/{id}/stats
```

**Example:**
```bash
curl http://localhost:8000/api/papers/1/stats
```

**Response:**
```json
{
  "paper_id": 1,
  "title": "Sustainability in Blockchain",
  "total_chunks": 119,
  "sections": {
    "Introduction": 35,
    "Results": 33,
    "Methods": 12
  },
  "avg_chunk_length": 450
}
```

The interactive API documentation at /docs reflects all available endpoints.

---

## 💡 Usage Examples

### Example 1: Upload and Query a Paper

```bash
# 1. Upload a paper
curl -X POST "http://localhost:8000/api/papers/upload" \
  -F "files=@sample_papers/paper_1.pdf"

# 2. Ask a question
curl -X POST "http://localhost:8000/api/query?question=What%20are%20the%20scalability%20challenges%3F&top_k=5"
```

### Example 2: Multi-Paper Analysis

```bash
# Upload multiple papers
curl -X POST "http://localhost:8000/api/papers/upload" \
  -F "files=@sample_papers/paper_1.pdf" \
  -F "files=@sample_papers/paper_2.pdf"

# Query specific papers (assuming IDs 1 and 2)
curl -X POST "http://localhost:8000/api/query?question=Compare%20the%20approaches&paper_ids=1,2&top_k=5"
```

### Example 3: Python Client

```python
import requests

# Upload papers
files = [
    ('files', open('sample_papers/paper_1.pdf', 'rb')),
    ('files', open('sample_papers/paper_2.pdf', 'rb'))
]
response = requests.post('http://localhost:8000/api/papers/upload', files=files)
print(response.json())

# Query
params = {
    'question': 'What is blockchain?',
    'top_k': 5,
    'model': 'llama3'
}
response = requests.post('http://localhost:8000/api/query', params=params)
result = response.json()

print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")
print(f"Citations: {len(result['citations'])}")
```

---

## 📁 Project Structure

```
research-paper-rag-assessment/
├── src/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                # API endpoint definitions
│   ├── models/
│   │   ├── __init__.py
│   │   └── db.py                    # SQLAlchemy models (papers, queries)
│   └── services/
│       ├── __init__.py
│       ├── pdf_processor.py         # PDF extraction logic
│       ├── embedding_service.py     # Sentence transformers
│       ├── qdrant_client.py         # Qdrant vector DB client
│       ├── rag_pipeline.py          # RAG query pipeline
│       ├── ollama_client.py         # Ollama LLM client
│       └── chunking.py              # Text chunking strategies
├── sample_papers/                   # Test PDF files
├── temp/                            # Uploaded files & chunks (auto-created)
├── docker-compose.yml               # Docker services configuration
├── Dockerfile                       # API service container
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables example
├── .env                             # Environment variables (local)
├── setup.sh                         # One-command setup script
├── verify.sh                        # Quick environment verification
├── README.md                        # This file
└── tests/                           # Test scripts
  ├── test_query_api.sh
  ├── test_query_examples.py
  └── test_paper_management.{py,sh}
```

---

## ⚙️ Configuration

### Environment Variables

The system uses `.env` (or docker-compose envs) for configuration:

```bash
# Database (docker-compose defaults)
DATABASE_URL=postgresql+psycopg2://rag_user:rag_pass@localhost:5433/ragdb

# Qdrant Vector DB
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=research_papers

# Ollama LLM
OLLAMA_BASE_URL=http://localhost:11434

# Docker user mapping (auto-detected)
UID=1000
GID=1000
```

### Docker Services

The `docker-compose.yml` defines three services:

1. **API (FastAPI)** - Port 8000
2. **PostgreSQL** - Port 5433 (mapped from 5432)
3. **Qdrant** - Ports 6333, 6334

All services use persistent volumes to preserve data.

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Ollama Connection Refused
**Symptom:** Queries return empty answers

**Solution:**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve

# Pull the model
ollama pull llama3
```

If the above steps don't help, check container logs via docker-compose logs.

#### 2. Permission Denied on temp/ Directory
**Symptom:** Cannot delete files in temp/

**Solution:** The setup script automatically handles this. If issues persist:
```bash
# Fix ownership (one-time)
sudo chown -R $USER:$USER temp/

# Rebuild containers
docker-compose down
./setup.sh
```

#### 3. Port Already in Use
**Symptom:** Docker fails to start

**Solution:**
```bash
# Check what's using the port
sudo lsof -i :8000

# Stop conflicting service or change port in docker-compose.yml
```

#### 4. Container Fails to Start
**Solution:**
```bash
# Check logs
docker-compose logs api

# Rebuild from scratch
docker-compose down -v
docker system prune -f
./setup.sh
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# Follow API logs
docker-compose logs -f api

# Check container status
docker-compose ps

# Enter API container
docker exec -it rag_api bash
```

---

## 🧪 Testing

### Automated Tests

```bash
# Run query tests (bash)
./tests/test_query_api.sh

# Run query tests (Python)
python tests/test_query_examples.py

# Run paper management tests
./tests/test_paper_management.sh
```

### Manual Testing

1. **Upload a paper:**
   ```bash
   curl -X POST "http://localhost:8000/api/papers/upload" \
     -F "files=@sample_papers/paper_1.pdf"
   ```

2. **Test query:**
   ```bash
   curl -X POST "http://localhost:8000/api/query?question=What%20is%20blockchain%3F&top_k=5"
   ```

3. **Check results:** View [QUERY_TEST_RESULTS.md](QUERY_TEST_RESULTS.md)

---

## 🔧 Development

### Running in Development Mode

```bash
# With live reload
docker-compose up

# View logs in real-time
docker-compose logs -f api
```

### Making Changes

1. Edit code in `src/`
2. Container auto-reloads (no restart needed)
3. Test changes via API

### Stopping Services

```bash
# Stop containers (data persists)
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## 📊 Performance

- **Upload Speed:** ~5-10 papers per minute
- **Query Latency:** 15-40 seconds (depends on top_k and context size)
- **Concurrent Queries:** Supports multiple simultaneous requests
- **Storage:** ~5MB per 20-page paper (including vectors)

---

## 📄 License

[Your License Here]

---

## 🙏 Acknowledgments

- **Qdrant** - Vector database
- **Ollama** - Local LLM inference
- **FastAPI** - Web framework
- **sentence-transformers** - Embedding models

---

**Built with ❤️ for the Research Community**

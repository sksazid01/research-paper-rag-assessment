# 🚀 Quick Start Guide

## Single-Command Deployment

This project is designed for **one-command deployment**. Just run:

```bash
docker-compose up --build
```

That's it! No configuration files needed, no environment variables to set up.

## Prerequisites

You only need **3 things** installed:

1. **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
2. **Docker Compose** - Usually comes with Docker Desktop
3. **Ollama with llama3** - [Install Ollama](https://ollama.ai/download)

### Ollama Setup (One-Time)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the llama3 model
ollama pull llama3

# Verify it's running
ollama list
```

## First-Time Setup

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd research-paper-rag-assessment

# 2. Start everything with one command
docker-compose up --build
```

**That's it!** 🎉

The first build takes 5-10 minutes because it downloads PyTorch and other ML libraries.

## What Gets Started

When you run `docker-compose up --build`, three services start automatically:

1. **PostgreSQL** - Database on port `5433`
2. **Qdrant** - Vector database on ports `6333` & `6334`
3. **FastAPI** - Your API on port `8000`

## Verify It's Working

Open another terminal and try:

```bash
# 1. Check API health
curl http://localhost:8000/health

# 2. Upload a test paper
curl -X POST -F "files=@sample_papers/paper_1.pdf" \
  http://localhost:8000/api/papers/upload

# 3. Query the paper
curl -X POST http://localhost:8000/api/papers/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is blockchain?",
    "paper_ids": ["paper_1"]
  }'
```

## Access the API

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Upload Endpoint**: http://localhost:8000/api/papers/upload
- **Query Endpoint**: http://localhost:8000/api/papers/query

## Stopping the Services

```bash
# Stop all services (keeps data)
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Troubleshooting

### Issue: "Cannot connect to Ollama"
**Solution**: Make sure Ollama is running on your host machine
```bash
ollama serve
```

### Issue: "Port already in use"
**Solution**: Stop the conflicting service or change the port in `docker-compose.yml`

### Issue: Build takes too long
**Solution**: This is normal for the first build (downloads ~1GB of dependencies). Subsequent builds are much faster thanks to Docker caching.

### Issue: Permission denied
**Solution**: The project automatically handles permissions using your user's UID/GID. If you see permission errors, check that Docker has access to your home directory.

## Project Structure

```
research-paper-rag-assessment/
├── docker-compose.yml    # Service orchestration (one command!)
├── Dockerfile            # API container definition
├── requirements.txt      # Python dependencies
├── src/                  # Application code
│   ├── main.py          # FastAPI app
│   ├── api/             # API routes
│   └── services/        # Core services
├── sample_papers/       # Test PDFs
└── temp/                # Temporary files
```

## Development Mode

The API runs in **live-reload mode** by default, meaning code changes are immediately reflected without rebuilding:

```bash
# Edit any Python file in src/
# Changes are automatically detected and the API reloads
```

## Next Steps

1. ✅ Start the services: `docker-compose up --build`
2. ✅ Upload your research papers
3. ✅ Query the RAG system
4. ✅ Check out the API docs at http://localhost:8000/docs

For more details, see the main [README.md](README.md)

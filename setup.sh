#!/bin/bash
set -e

echo "=========================================="
echo "Research Paper RAG System - Setup Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="Windows"
else
    OS="Unknown"
fi

echo "Detected OS: $OS"
echo ""

# Set UID/GID based on OS
if [[ "$OS" == "Windows" ]]; then
    # Windows doesn't have UID/GID, use defaults
    CURRENT_UID=1000
    CURRENT_GID=1000
    echo -e "${YELLOW}⚠${NC} Windows detected - using default UID/GID (1000:1000)"
else
    # Linux/macOS - detect actual user
    CURRENT_UID=$(id -u)
    CURRENT_GID=$(id -g)
    echo -e "${GREEN}✓${NC} Detected user: $(whoami) (UID: $CURRENT_UID, GID: $CURRENT_GID)"
fi

echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓${NC} Created .env file from .env.example"
    else
        echo -e "${RED}✗${NC} .env.example not found!"
        exit 1
    fi
fi

# Export for docker-compose
export UID=$CURRENT_UID
export GID=$CURRENT_GID

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗${NC} Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗${NC} Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker Compose is installed"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗${NC} Docker daemon is not running"
    echo "Please start Docker and try again"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker daemon is running"

echo ""

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ollama is running on localhost:11434"
else
    echo -e "${YELLOW}⚠${NC} Ollama is not running on localhost:11434"
    echo "  The API will not be able to generate answers without Ollama"
    echo "  Install Ollama: https://ollama.ai/"
    echo "  Then run: ollama pull llama3"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "Starting Docker containers..."
echo "=========================================="
echo ""

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start containers
echo "Building and starting containers..."
UID=$CURRENT_UID GID=$CURRENT_GID docker-compose up -d --build

echo ""
echo "=========================================="
echo "Waiting for services to be ready..."
echo "=========================================="
echo ""

# Wait for API to be ready
echo -n "Waiting for API"
for i in {1..30}; do
    if curl -s http://localhost:8000/docs &> /dev/null; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Wait for PostgreSQL
echo -n "Waiting for PostgreSQL"
for i in {1..30}; do
    if docker exec rag_postgres pg_isready -U rag_user &> /dev/null; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Wait for Qdrant
echo -n "Waiting for Qdrant"
for i in {1..30}; do
    if curl -s http://localhost:6333/collections &> /dev/null; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo -e "${GREEN}✓${NC} API:        http://localhost:8000"
echo -e "${GREEN}✓${NC} API Docs:   http://localhost:8000/docs"
echo -e "${GREEN}✓${NC} Qdrant UI:  http://localhost:6333/dashboard"
echo -e "${GREEN}✓${NC} PostgreSQL: localhost:5433"
echo ""
echo "Next steps:"
echo "  1. Upload papers: curl -X POST -F 'files=@paper.pdf' http://localhost:8000/api/papers/upload"
echo "  2. Query papers:  curl -X POST 'http://localhost:8000/api/query?question=your_question&top_k=5'"
echo "  3. View logs:     docker-compose logs -f api"
echo ""
echo "To stop: docker-compose down"
echo ""

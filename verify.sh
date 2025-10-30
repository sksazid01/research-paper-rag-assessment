#!/bin/bash

# Quick verification that the setup worked correctly

echo "=========================================="
echo "Verifying Research Paper RAG System Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

FAILED=0

# Check if containers are running
echo -n "Checking API container... "
if docker ps | grep -q rag_api; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} (not running)"
    FAILED=1
fi

echo -n "Checking PostgreSQL container... "
if docker ps | grep -q rag_postgres; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} (not running)"
    FAILED=1
fi

echo -n "Checking Qdrant container... "
if docker ps | grep -q rag_qdrant; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} (not running)"
    FAILED=1
fi

echo ""

# Check if services are responding
echo -n "Checking API endpoint... "
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} (not responding)"
    FAILED=1
fi

echo -n "Checking Qdrant endpoint... "
if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} (not responding)"
    FAILED=1
fi

echo -n "Checking PostgreSQL... "
if docker exec rag_postgres pg_isready -U rag_user > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} (not ready)"
    FAILED=1
fi

echo ""

# Check Ollama
echo -n "Checking Ollama... "
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} (not running - queries will fail)"
fi

echo ""
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "System is ready:"
    echo "  • API:        http://localhost:8000"
    echo "  • API Docs:   http://localhost:8000/docs"
    echo "  • Qdrant UI:  http://localhost:6333/dashboard"
    echo ""
    echo "Quick test:"
    echo "  curl -X POST -F 'files=@sample_papers/paper_1.pdf' http://localhost:8000/api/papers/upload"
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: docker-compose logs"
    echo "  2. Restart: docker-compose down && ./setup.sh"
    exit 1
fi

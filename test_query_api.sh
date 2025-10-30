#!/bin/bash

# Test Query API - Example queries for the RAG system
# Make sure the server is running: uvicorn src.main:app --reload

API_BASE="http://127.0.0.1:8000/api"

echo "=========================================="
echo "Testing Intelligent Query System"
echo "=========================================="
echo ""

# Test 1: Simple query
echo "Test 1: Simple query without filters"
curl -X POST "${API_BASE}/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is blockchain scalability?",
    "top_k": 5
  }' | jq '.'

echo ""
echo "=========================================="
echo ""

# Test 2: Query with paper_ids filter
echo "Test 2: Query filtered to specific papers"
curl -X POST "${API_BASE}/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main challenges discussed?",
    "top_k": 3,
    "paper_ids": [6]
  }' | jq '.'

echo ""
echo "=========================================="
echo ""

# Test 3: Methodology question
echo "Test 3: Methodology question"
curl -X POST "${API_BASE}/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What methodology was used in the research?",
    "top_k": 5
  }' | jq '.'

echo ""
echo "=========================================="
echo "Tests complete!"
echo "=========================================="

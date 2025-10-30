#!/bin/bash

# Test Paper Management API
# Make sure the server is running: uvicorn src.main:app --reload

API_BASE="http://127.0.0.1:8000/api"

echo "=========================================="
echo "Testing Paper Management Endpoints"
echo "=========================================="
echo ""

# Test 1: List all papers
echo "Test 1: List all papers (GET /api/papers)"
echo "------------------------------------------"
curl -s -X GET "${API_BASE}/papers" | jq '.'
echo ""
echo ""

# Test 2: Get specific paper (use ID from list above)
echo "Test 2: Get specific paper (GET /api/papers/6)"
echo "------------------------------------------"
curl -s -X GET "${API_BASE}/papers/6" | jq '.'
echo ""
echo ""

# Test 3: Get paper stats
echo "Test 3: Get paper statistics (GET /api/papers/6/stats)"
echo "------------------------------------------"
curl -s -X GET "${API_BASE}/papers/6/stats" | jq '.'
echo ""
echo ""

# Test 4: Delete paper (commented out to avoid accidental deletion)
# Uncomment to test deletion
# echo "Test 4: Delete paper (DELETE /api/papers/999)"
# echo "------------------------------------------"
# curl -s -X DELETE "${API_BASE}/papers/999" | jq '.'
# echo ""
# echo ""

echo "=========================================="
echo "Paper Management Tests Complete!"
echo "=========================================="
echo ""
echo "To test deletion, uncomment the DELETE test"
echo "and replace 999 with an actual paper ID"

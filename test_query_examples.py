"""
Example usage of the Query API endpoint.
Run this after starting the server and uploading papers.
"""

import requests
import json

API_BASE = "http://127.0.0.1:8000/api"


def test_simple_query():
    """Test basic query without filters."""
    print("\n" + "="*60)
    print("Test 1: Simple Query")
    print("="*60)
    
    response = requests.post(
        f"{API_BASE}/query",
        json={
            "question": "What is blockchain scalability?",
            "top_k": 5
        }
    )
    
    result = response.json()
    print(f"\nQuestion: What is blockchain scalability?")
    print(f"\nAnswer: {result.get('answer')}")
    print(f"\nConfidence: {result.get('confidence')}")
    print(f"\nSources Used: {result.get('sources_used')}")
    print(f"\nCitations:")
    for i, citation in enumerate(result.get('citations', []), 1):
        print(f"  {i}. {citation.get('paper_title')} ({citation.get('section')}, page {citation.get('page')})")
        print(f"     Relevance: {citation.get('relevance_score')}")


def test_filtered_query():
    """Test query with paper_ids filter."""
    print("\n" + "="*60)
    print("Test 2: Query with Paper Filter")
    print("="*60)
    
    response = requests.post(
        f"{API_BASE}/query",
        json={
            "question": "What are the main challenges discussed?",
            "top_k": 3,
            "paper_ids": [6]
        }
    )
    
    result = response.json()
    print(f"\nQuestion: What are the main challenges discussed? (Paper ID: 6)")
    print(f"\nAnswer: {result.get('answer')}")
    print(f"\nConfidence: {result.get('confidence')}")
    print(f"\nSources Used: {result.get('sources_used')}")


def test_methodology_query():
    """Test methodology-focused query."""
    print("\n" + "="*60)
    print("Test 3: Methodology Query")
    print("="*60)
    
    response = requests.post(
        f"{API_BASE}/query",
        json={
            "question": "What methodology was used in the research?",
            "top_k": 5
        }
    )
    
    result = response.json()
    print(f"\nQuestion: What methodology was used in the research?")
    print(f"\nAnswer: {result.get('answer')[:500]}...")  # Truncate for readability
    print(f"\nConfidence: {result.get('confidence')}")
    print(f"\nTotal Citations: {len(result.get('citations', []))}")


def test_comparative_query():
    """Test query comparing multiple papers."""
    print("\n" + "="*60)
    print("Test 4: Comparative Query")
    print("="*60)
    
    response = requests.post(
        f"{API_BASE}/query",
        json={
            "question": "Compare the energy consumption approaches discussed in different papers.",
            "top_k": 10
        }
    )
    
    result = response.json()
    print(f"\nQuestion: Compare the energy consumption approaches...")
    print(f"\nAnswer: {result.get('answer')[:500]}...")
    print(f"\nSources Used: {result.get('sources_used')}")
    print(f"\nConfidence: {result.get('confidence')}")


if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("Testing Intelligent Query System")
        print("="*60)
        print("\nMake sure:")
        print("1. Server is running (uvicorn src.main:app --reload)")
        print("2. Papers have been uploaded via /api/papers/upload")
        print("3. Ollama is running with llama3 model")
        
        test_simple_query()
        test_filtered_query()
        test_methodology_query()
        test_comparative_query()
        
        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server.")
        print("Make sure the server is running: uvicorn src.main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

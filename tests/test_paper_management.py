"""
Test Paper Management API endpoints.
Run this after starting the server and uploading papers.
"""

import requests

API_BASE = "http://127.0.0.1:8000/api"


def test_list_papers():
    """Test GET /api/papers - List all papers."""
    print("\n" + "="*60)
    print("Test 1: List All Papers")
    print("="*60)
    
    response = requests.get(f"{API_BASE}/papers")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Success! Found {result['total']} paper(s)\n")
        
        for paper in result['papers']:
            print(f"ID: {paper['id']}")
            print(f"  Title: {paper['title']}")
            authors = paper.get('authors')
            if authors:
                print(f"  Authors: {authors[:50]}..." if len(authors) > 50 else f"  Authors: {authors}")
            print(f"  Year: {paper['year']}")
            print(f"  Filename: {paper['filename']}")
            print(f"  Pages: {paper['pages']}")
            print(f"  Created: {paper['created_at']}")
            print()
        
        return result['papers']
    else:
        print(f"\n❌ Failed: {response.status_code}")
        print(response.text)
        return []


def test_get_paper(paper_id):
    """Test GET /api/papers/{id} - Get specific paper."""
    print("\n" + "="*60)
    print(f"Test 2: Get Paper Details (ID: {paper_id})")
    print("="*60)
    
    response = requests.get(f"{API_BASE}/papers/{paper_id}")
    
    if response.status_code == 200:
        paper = response.json()
        print(f"\n✅ Success!\n")
        print(f"ID: {paper['id']}")
        print(f"Title: {paper['title']}")
        print(f"Authors: {paper['authors']}")
        print(f"Year: {paper['year']}")
        print(f"Filename: {paper['filename']}")
        print(f"Pages: {paper['pages']}")
        print(f"Created: {paper['created_at']}")
    elif response.status_code == 404:
        print(f"\n⚠️  Paper not found")
    else:
        print(f"\n❌ Failed: {response.status_code}")
        print(response.text)


def test_get_paper_stats(paper_id):
    """Test GET /api/papers/{id}/stats - Get paper statistics."""
    print("\n" + "="*60)
    print(f"Test 3: Get Paper Statistics (ID: {paper_id})")
    print("="*60)
    
    response = requests.get(f"{API_BASE}/papers/{paper_id}/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"\n✅ Success!\n")
        print(f"Paper: {stats['title']}")
        print(f"Filename: {stats['filename']}")
        print(f"Pages: {stats['pages']}")
        print(f"Total Chunks: {stats['total_chunks']}")
        print(f"Avg Chunk Length: {stats['avg_chunk_length']} chars")
        print(f"\nSection Distribution:")
        for section, count in sorted(stats['sections'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {section}: {count} chunks")
    elif response.status_code == 404:
        print(f"\n⚠️  Paper not found")
    else:
        print(f"\n❌ Failed: {response.status_code}")
        print(response.text)


def test_get_nonexistent_paper():
    """Test error handling for non-existent paper."""
    print("\n" + "="*60)
    print("Test 4: Get Non-existent Paper (Error Handling)")
    print("="*60)
    
    response = requests.get(f"{API_BASE}/papers/99999")
    
    if response.status_code == 404:
        print(f"\n✅ Correct! Returns 404 for non-existent paper")
        print(f"Error message: {response.json()['detail']}")
    else:
        print(f"\n❌ Unexpected status: {response.status_code}")


if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("Testing Paper Management API")
        print("="*60)
        print("\nMake sure:")
        print("1. Server is running in Docker (docker-compose up)")
        print("2. Papers have been uploaded via /api/papers/upload")
        
        # Test list papers
        papers = test_list_papers()
        
        if papers:
            first_paper_id = papers[0]['id']
            test_get_paper(first_paper_id)
            test_get_paper_stats(first_paper_id)
            test_get_nonexistent_paper()
        else:
            print("\n⚠️  No papers found. Upload some papers first!")
        
        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server.")
        print("Make sure the server is running in Docker: docker-compose up")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

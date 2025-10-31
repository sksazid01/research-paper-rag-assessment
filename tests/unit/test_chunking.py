"""
Unit tests for chunking service
Tests the sentence-based chunking strategy with section awareness
"""
import pytest
from src.services.chunking import chunk_sentences


def test_chunk_sentences_basic():
    """Test basic chunking with simple sentences"""
    sentences = [
        {"text": "This is sentence one.", "page": 1, "section": "Introduction"},
        {"text": "This is sentence two.", "page": 1, "section": "Introduction"},
        {"text": "This is sentence three.", "page": 2, "section": "Introduction"},
    ]
    
    chunks = chunk_sentences(sentences, max_chars=50, overlap_chars=10)
    
    assert len(chunks) > 0
    assert all("text" in c for c in chunks)
    assert all("section" in c for c in chunks)
    assert all("page_start" in c for c in chunks)
    assert all("page_end" in c for c in chunks)
    assert all("chunk_index" in c for c in chunks)


def test_chunk_sentences_section_boundary():
    """Test that chunks respect section boundaries"""
    sentences = [
        {"text": "Intro sentence one.", "page": 1, "section": "Introduction"},
        {"text": "Intro sentence two.", "page": 1, "section": "Introduction"},
        {"text": "Methods sentence one.", "page": 2, "section": "Methods"},
        {"text": "Methods sentence two.", "page": 2, "section": "Methods"},
    ]
    
    chunks = chunk_sentences(sentences, max_chars=100, overlap_chars=10)
    
    # Check that intro and methods are in separate chunks
    sections = [c["section"] for c in chunks]
    assert "Introduction" in sections
    assert "Methods" in sections
    
    # Verify no chunk mixes both sections
    for chunk in chunks:
        assert chunk["section"] in ["Introduction", "Methods"]


def test_chunk_sentences_overlap():
    """Test that overlap is preserved between chunks"""
    sentences = [
        {"text": "A" * 50, "page": 1, "section": "Test"},  # 50 chars
        {"text": "B" * 50, "page": 1, "section": "Test"},  # 50 chars
        {"text": "C" * 50, "page": 1, "section": "Test"},  # 50 chars
    ]
    
    chunks = chunk_sentences(sentences, max_chars=80, overlap_chars=20)
    
    # Should create multiple chunks due to size constraint
    assert len(chunks) >= 2
    
    # Verify chunk indices are sequential
    indices = [c["chunk_index"] for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunk_sentences_page_tracking():
    """Test that page ranges are correctly tracked"""
    sentences = [
        {"text": "Page 1 text.", "page": 1, "section": "Abstract"},
        {"text": "Page 2 text.", "page": 2, "section": "Abstract"},
        {"text": "Page 3 text.", "page": 3, "section": "Abstract"},
    ]
    
    chunks = chunk_sentences(sentences, max_chars=100, overlap_chars=10)
    
    for chunk in chunks:
        assert chunk["page_start"] <= chunk["page_end"]
        assert chunk["page_start"] >= 1


def test_chunk_sentences_empty_input():
    """Test handling of empty input"""
    chunks = chunk_sentences([])
    assert chunks == []


def test_chunk_sentences_single_sentence():
    """Test single sentence chunking"""
    sentences = [
        {"text": "Single sentence.", "page": 1, "section": "Abstract"}
    ]
    
    chunks = chunk_sentences(sentences, max_chars=1000, overlap_chars=50)
    
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Single sentence."
    assert chunks[0]["page_start"] == 1
    assert chunks[0]["page_end"] == 1


def test_chunk_sentences_long_text():
    """Test chunking of long text that exceeds max_chars"""
    # Create a very long sentence
    long_text = "This is a very long sentence. " * 100  # ~3000 chars
    sentences = [
        {"text": long_text, "page": 1, "section": "Introduction"}
    ]
    
    chunks = chunk_sentences(sentences, max_chars=500, overlap_chars=50)
    
    # Should create multiple chunks
    assert len(chunks) >= 1
    # Each chunk should contain the section
    assert all(c["section"] == "Introduction" for c in chunks)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

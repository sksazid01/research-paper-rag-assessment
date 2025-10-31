"""
Unit tests for RAG pipeline
Tests retrieval, citation extraction, and paper detection
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.services.rag_pipeline import (
    _extract_quoted_titles,
    _guess_candidate_paper_ids,
    extract_citations_from_answer,
    calculate_confidence
)


def test_extract_quoted_titles_single():
    """Test extraction of single quoted title"""
    question = "What is the main goal of paper 'Attention is All You Need'?"
    titles = _extract_quoted_titles(question)
    assert len(titles) == 1
    assert titles[0] == "Attention is All You Need"


def test_extract_quoted_titles_multiple():
    """Test extraction of multiple quoted titles"""
    question = "Compare 'Deep Learning' and 'Neural Networks' papers"
    titles = _extract_quoted_titles(question)
    assert len(titles) == 2
    assert "Deep Learning" in titles
    assert "Neural Networks" in titles


def test_extract_quoted_titles_none():
    """Test when no quoted titles present"""
    question = "What are the benefits of machine learning?"
    titles = _extract_quoted_titles(question)
    assert len(titles) == 0


def test_extract_quoted_titles_double_vs_single():
    """Test extraction with both single and double quotes"""
    question = "Compare \"Paper One\" and 'Paper Two'"
    titles = _extract_quoted_titles(question)
    assert len(titles) == 2
    assert "Paper One" in titles
    assert "Paper Two" in titles


def test_guess_candidate_paper_ids_keyword_match():
    """Test paper detection via keyword matching"""
    mock_session = MagicMock()
    
    # Mock papers with blockchain keywords
    mock_paper1 = Mock()
    mock_paper1.id = 1
    mock_paper1.title = "Blockchain Applications in Healthcare"
    mock_paper1.filename = "paper_1.pdf"
    
    mock_paper2 = Mock()
    mock_paper2.id = 2
    mock_paper2.title = "Machine Learning Basics"
    mock_paper2.filename = "paper_2.pdf"
    
    mock_session.query().all.return_value = [mock_paper1, mock_paper2]
    
    question = "What are the applications of blockchain technology?"
    paper_ids = _guess_candidate_paper_ids(question, mock_session)
    
    assert 1 in paper_ids  # blockchain paper should match


def test_guess_candidate_paper_ids_quoted_title():
    """Test paper detection via quoted title"""
    mock_session = MagicMock()
    
    mock_paper = Mock()
    mock_paper.id = 3
    mock_paper.title = "Attention is All You Need"
    mock_paper.filename = "paper_3.pdf"
    
    mock_session.query().all.return_value = [mock_paper]
    
    question = "What is 'Attention is All You Need' about?"
    paper_ids = _guess_candidate_paper_ids(question, mock_session)
    
    assert 3 in paper_ids


def test_extract_citations_basic():
    """Test basic citation extraction from LLM answer"""
    answer = "The transformer architecture (Source 1) uses attention mechanisms (Source 2)."
    contexts = [
        {
            "paper_id": 1,
            "paper_title": "Attention Paper",
            "paper_filename": "paper_1.pdf",
            "text": "Transformer uses self-attention",
            "section": "Introduction",
            "page_number": 3,
            "score": 0.85
        },
        {
            "paper_id": 2,
            "paper_title": "Attention Mechanisms",
            "paper_filename": "paper_2.pdf",
            "text": "Attention allows model to focus",
            "section": "Methods",
            "page_number": 5,
            "score": 0.78
        }
    ]
    
    citations = extract_citations_from_answer(answer, contexts)
    
    assert len(citations) == 2
    assert citations[0]["paper_id"] == 1
    assert citations[0]["source_index"] == 1
    assert citations[1]["paper_id"] == 2
    assert citations[1]["source_index"] == 2


def test_extract_citations_duplicate_sources():
    """Test that duplicate source numbers are deduplicated"""
    answer = "The paper discusses transformers (Source 1) and attention (Source 1)."
    contexts = [
        {
            "paper_id": 1,
            "paper_title": "Attention Paper",
            "paper_filename": "paper_1.pdf",
            "text": "Transformers and attention",
            "section": "Introduction",
            "page_number": 3,
            "score": 0.85
        }
    ]
    
    citations = extract_citations_from_answer(answer, contexts)
    
    # Should only return one citation despite two references
    assert len(citations) == 1


def test_extract_citations_no_sources():
    """Test when answer has no source citations"""
    answer = "This is a response without citations."
    contexts = [
        {
            "paper_id": 1,
            "paper_title": "Some Paper",
            "paper_filename": "paper_1.pdf",
            "text": "Context text",
            "section": "Introduction",
            "page_number": 1,
            "score": 0.75
        }
    ]
    
    citations = extract_citations_from_answer(answer, contexts)
    
    assert len(citations) == 0


def test_calculate_confidence_high():
    """Test confidence calculation with good citations"""
    citations = [
        {"relevance_score": 0.85},
        {"relevance_score": 0.78}
    ]
    
    confidence = calculate_confidence(citations)
    
    assert confidence >= 0.7
    assert confidence <= 1.0


def test_calculate_confidence_low():
    """Test confidence calculation with weak citations"""
    citations = [
        {"relevance_score": 0.25},
        {"relevance_score": 0.30}
    ]
    
    confidence = calculate_confidence(citations)
    
    assert confidence < 0.5


def test_calculate_confidence_no_citations():
    """Test confidence calculation with no citations"""
    citations = []
    
    confidence = calculate_confidence(citations)
    
    assert confidence == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

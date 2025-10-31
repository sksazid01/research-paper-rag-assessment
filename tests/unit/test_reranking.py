"""
Unit tests for cross-encoder re-ranking
Tests the rerank_contexts function
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


def test_rerank_contexts_basic():
    """Test basic re-ranking functionality"""
    from src.services.rag_pipeline import rerank_contexts
    
    # Mock contexts
    contexts = [
        {"text": "The transformer architecture uses attention mechanisms.", "score": 0.7},
        {"text": "Blockchain technology for sustainability.", "score": 0.8},
        {"text": "Attention is all you need for NLP tasks.", "score": 0.6},
    ]
    
    query = "What is the transformer architecture?"
    
    # Mock cross-encoder
    with patch('src.services.rag_pipeline.get_cross_encoder') as mock_get_ce:
        mock_ce = Mock()
        # Simulate cross-encoder scores (higher = more relevant)
        # Should rank: context[0] > context[2] > context[1]
        mock_ce.predict.return_value = [0.92, 0.45, 0.88]
        mock_get_ce.return_value = mock_ce
        
        reranked = rerank_contexts(query, contexts, top_k=3)
        
        # Check that contexts were re-ordered
        assert len(reranked) == 3
        assert reranked[0]["text"] == "The transformer architecture uses attention mechanisms."
        assert reranked[1]["text"] == "Attention is all you need for NLP tasks."
        assert reranked[2]["text"] == "Blockchain technology for sustainability."
        
        # Check that cross-encoder scores replaced original scores
        assert reranked[0]["score"] == 0.92
        assert reranked[0]["original_score"] == 0.7


def test_rerank_contexts_top_k():
    """Test that top_k parameter limits results"""
    from src.services.rag_pipeline import rerank_contexts
    
    contexts = [
        {"text": "Text 1", "score": 0.7},
        {"text": "Text 2", "score": 0.8},
        {"text": "Text 3", "score": 0.6},
        {"text": "Text 4", "score": 0.5},
    ]
    
    query = "Test query"
    
    with patch('src.services.rag_pipeline.get_cross_encoder') as mock_get_ce:
        mock_ce = Mock()
        mock_ce.predict.return_value = [0.9, 0.8, 0.7, 0.6]
        mock_get_ce.return_value = mock_ce
        
        reranked = rerank_contexts(query, contexts, top_k=2)
        
        # Should only return top 2
        assert len(reranked) == 2
        assert reranked[0]["score"] == 0.9
        assert reranked[1]["score"] == 0.8


def test_rerank_contexts_empty():
    """Test handling of empty contexts"""
    from src.services.rag_pipeline import rerank_contexts
    
    contexts = []
    query = "Test query"
    
    reranked = rerank_contexts(query, contexts)
    
    assert reranked == []


def test_rerank_contexts_disabled():
    """Test that re-ranking can be disabled via env variable"""
    from src.services.rag_pipeline import rerank_contexts
    import os
    
    contexts = [
        {"text": "Text 1", "score": 0.7},
        {"text": "Text 2", "score": 0.8},
    ]
    
    query = "Test query"
    
    with patch.dict(os.environ, {"ENABLE_CROSS_ENCODER_RERANK": "false"}):
        reranked = rerank_contexts(query, contexts)
        
        # Should return original order when disabled
        assert reranked == contexts


def test_rerank_contexts_fallback_on_error():
    """Test graceful fallback when cross-encoder fails"""
    from src.services.rag_pipeline import rerank_contexts
    
    contexts = [
        {"text": "Text 1", "score": 0.7},
        {"text": "Text 2", "score": 0.8},
    ]
    
    query = "Test query"
    
    with patch('src.services.rag_pipeline.get_cross_encoder') as mock_get_ce:
        mock_ce = Mock()
        mock_ce.predict.side_effect = Exception("Model loading failed")
        mock_get_ce.return_value = mock_ce
        
        reranked = rerank_contexts(query, contexts)
        
        # Should return original contexts on error
        assert reranked == contexts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

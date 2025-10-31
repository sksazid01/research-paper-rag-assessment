"""
Unit tests for embedding service
Tests caching behavior and batch processing
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.embedding_service import get_embeddings


@patch('src.services.embedding_service.model')
def test_get_embeddings_single_text(mock_model):
    """Test embedding generation for single text"""
    mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
    
    texts = ["This is a test sentence"]
    embeddings = get_embeddings(texts)
    
    assert len(embeddings) == 1
    assert len(embeddings[0]) == 3
    assert embeddings[0] == [0.1, 0.2, 0.3]
    mock_model.encode.assert_called_once()


@patch('src.services.embedding_service.model')
def test_get_embeddings_multiple_texts(mock_model):
    """Test embedding generation for multiple texts"""
    mock_model.encode.return_value = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9]
    ]
    
    texts = ["First sentence", "Second sentence", "Third sentence"]
    embeddings = get_embeddings(texts)
    
    assert len(embeddings) == 3
    assert embeddings[1] == [0.4, 0.5, 0.6]
    mock_model.encode.assert_called_once()


@patch('src.services.embedding_service.model')
@patch('src.services.embedding_service.embedding_cache')
def test_get_embeddings_cache_hit(mock_cache, mock_model):
    """Test that cached embeddings are returned without model call"""
    cached_embedding = [0.9, 0.8, 0.7]
    mock_cache.get.return_value = cached_embedding
    
    texts = ["Cached text"]
    embeddings = get_embeddings(texts)
    
    assert embeddings[0] == cached_embedding
    mock_model.encode.assert_not_called()


@patch('src.services.embedding_service.model')
@patch('src.services.embedding_service.embedding_cache')
def test_get_embeddings_cache_miss(mock_cache, mock_model):
    """Test that uncached embeddings are generated and cached"""
    mock_cache.get.return_value = None
    new_embedding = [0.1, 0.2, 0.3]
    mock_model.encode.return_value = [new_embedding]
    
    texts = ["Uncached text"]
    embeddings = get_embeddings(texts)
    
    assert embeddings[0] == new_embedding
    mock_model.encode.assert_called_once()
    mock_cache.__setitem__.assert_called_once()


@patch('src.services.embedding_service.model')
@patch('src.services.embedding_service.embedding_cache')
def test_get_embeddings_partial_cache(mock_cache, mock_model):
    """Test mixed cache hits and misses"""
    def cache_get(key):
        if "cached" in key:
            return [0.9, 0.8, 0.7]
        return None
    
    mock_cache.get.side_effect = cache_get
    mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
    
    texts = ["This is cached text", "This is uncached text"]
    embeddings = get_embeddings(texts)
    
    assert len(embeddings) == 2
    assert embeddings[0] == [0.9, 0.8, 0.7]  # from cache
    assert embeddings[1] == [0.1, 0.2, 0.3]  # newly generated


@patch('src.services.embedding_service.model')
def test_get_embeddings_empty_input(mock_model):
    """Test handling of empty input"""
    texts = []
    embeddings = get_embeddings(texts)
    
    assert len(embeddings) == 0
    mock_model.encode.assert_not_called()


@patch('src.services.embedding_service.model')
def test_get_embeddings_batch_size(mock_model):
    """Test that large batches are processed correctly"""
    # Create 100 texts to test batching
    texts = [f"Text number {i}" for i in range(100)]
    mock_embeddings = [[float(i/100)] * 384 for i in range(100)]
    mock_model.encode.return_value = mock_embeddings
    
    embeddings = get_embeddings(texts)
    
    assert len(embeddings) == 100
    assert len(embeddings[0]) == 384


@patch('src.services.embedding_service.model')
def test_get_embeddings_preserves_order(mock_model):
    """Test that embedding order matches input text order"""
    mock_model.encode.return_value = [
        [0.1, 0.1, 0.1],
        [0.2, 0.2, 0.2],
        [0.3, 0.3, 0.3]
    ]
    
    texts = ["First", "Second", "Third"]
    embeddings = get_embeddings(texts)
    
    assert embeddings[0][0] == 0.1
    assert embeddings[1][0] == 0.2
    assert embeddings[2][0] == 0.3


@patch('src.services.embedding_service.model')
def test_get_embeddings_dimension_consistency(mock_model):
    """Test that all embeddings have same dimension"""
    mock_model.encode.return_value = [
        [0.1] * 384,
        [0.2] * 384,
        [0.3] * 384
    ]
    
    texts = ["Text one", "Text two", "Text three"]
    embeddings = get_embeddings(texts)
    
    dimensions = [len(emb) for emb in embeddings]
    assert all(dim == 384 for dim in dimensions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

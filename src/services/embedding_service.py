from typing import List
import hashlib
from functools import lru_cache

from sentence_transformers import SentenceTransformer


_model = SentenceTransformer("all-MiniLM-L6-v2")

# LRU cache for recent query embeddings (saves repeated embedding computation)
_embedding_cache = {}
_cache_max_size = 100


# Return the diamention is 384
def get_model_dim() -> int:
    return _model.get_sentence_embedding_dimension()


def _hash_text(text: str) -> str:
    """Create a hash key for caching."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def get_embeddings(texts: List[str], batch_size: int = 64, use_cache: bool = True) -> List[List[float]]:
    """
    Encode a list of texts into embeddings using a cached model.
    
    Args:
        texts: List of text strings to embed
        batch_size: Batch size for encoding
        use_cache: If True, cache single-text embeddings (useful for queries)
    """
    # If single text and cache enabled, try cache first
    if use_cache and len(texts) == 1:
        text = texts[0]
        cache_key = _hash_text(text)
        
        if cache_key in _embedding_cache:
            return [_embedding_cache[cache_key]]
        
        # Generate embedding
        embedding = _model.encode([text], batch_size=1, convert_to_numpy=False)[0]
        
        # Add to cache (with size limit)
        if len(_embedding_cache) >= _cache_max_size:
            # Remove oldest entry (FIFO-like behavior)
            _embedding_cache.pop(next(iter(_embedding_cache)))
        _embedding_cache[cache_key] = embedding
        
        return [embedding]
    
    # Batch encoding (no cache for document chunks)
    return _model.encode(texts, batch_size=batch_size, convert_to_numpy=False)

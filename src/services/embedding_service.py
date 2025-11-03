from typing import List
import hashlib
from functools import lru_cache

from sentence_transformers import SentenceTransformer


_model = SentenceTransformer("all-MiniLM-L6-v2")

# LRU(Least Recently Used) cache for recent query embeddings (saves repeated embedding computation)  
# sesh a jeta use hoiche, oita remove hbe
_embedding_cache = {}
_cache_max_size = 100


def get_model_dim() -> int:
    """
    Returns the dimensionality (length) of each embedding vector 
    produced by the loaded model. For MiniLM-L6-v2, it’s 384.
    """
    return _model.get_sentence_embedding_dimension()


def _hash_text(text: str) -> str:
    """
    Computes an MD5 hash of the given text.
    Used as a deterministic cache key so the same text always maps 
    to the same entry (without storing raw text).
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def get_embeddings(texts: List[str], batch_size: int = 64, use_cache: bool = True) -> List[List[float]]:
    """
    Convert a list of text strings into dense numeric embeddings using a cached model.

    Args:
        texts: A list of input strings (sentences, paragraphs, etc.)
        batch_size: How many items to process in one batch for efficiency
        use_cache: Whether to cache embeddings of a single text (useful for repeated queries)

    Returns:
        List of lists of floats — the embedding vectors for each input text.
    """
    # If single text and cache enabled, try cache first
    if use_cache and len(texts) == 1:
        text = texts[0]
        cache_key = _hash_text(text)
        
        if cache_key in _embedding_cache:
            return [_embedding_cache[cache_key]] # Return the cached embedding directly if it already exists.
        
        # Generate embedding
        embedding = _model.encode([text], batch_size=1, convert_to_numpy=False)[0]  # false: keeps the output as a PyTorch tensor (or similar object), not a NumPy array.
        
        # Add to cache (with size limit)
        if len(_embedding_cache) >= _cache_max_size:
            # Remove oldest entry (FIFO-like behavior)
            _embedding_cache.pop(next(iter(_embedding_cache)))
        _embedding_cache[cache_key] = embedding
        
        return [embedding]
    
    # Batch encoding (no cache for document chunks)
    return _model.encode(texts, batch_size=batch_size, convert_to_numpy=False)

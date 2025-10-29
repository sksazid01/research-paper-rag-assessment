from typing import List

from sentence_transformers import SentenceTransformer


_model = SentenceTransformer("all-MiniLM-L6-v2")

# Return the diamention is 384
def get_model_dim() -> int:
    return _model.get_sentence_embedding_dimension()


def get_embeddings(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    """Encode a list of texts into embeddings using a cached model."""
    return _model.encode(texts, batch_size=batch_size, convert_to_numpy=False)

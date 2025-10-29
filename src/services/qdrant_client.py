import os
from typing import List, Dict, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models


QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "research_papers")

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def ensure_collection(vector_size: int, distance: str = "COSINE"):
    dist = getattr(models.Distance, distance)
    try:
        client.get_collection(COLLECTION_NAME)
    except Exception:
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=vector_size, distance=dist),
        )


def upsert_vectors(vectors: List[List[float]], payloads: List[Dict], ids: Optional[List[int]] = None):
    if ids is None:
        ids = list(range(len(vectors)))
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=models.Batch(vectors=vectors, payloads=payloads, ids=ids),
    )


def search(vector: List[float], limit: int = 5, query_filter: Optional[models.Filter] = None):
    return client.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=limit,
        query_filter=query_filter,
    )

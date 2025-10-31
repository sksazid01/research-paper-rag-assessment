import os
import uuid
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
        # Use HNSW indexing for faster similarity search
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=vector_size, 
                distance=dist,
                # HNSW parameters for speed optimization
                hnsw_config=models.HnswConfigDiff(
                    m=16,  # Number of edges per node (higher = better accuracy, slower indexing)
                    ef_construct=100,  # Size of dynamic candidate list (higher = better quality)
                    full_scan_threshold=10000,  # Use HNSW index when collection has >10k vectors
                )
            ),
            # Enable payload indexing for faster filtering by paper_id
            optimizers_config=models.OptimizersConfigDiff(
                indexing_threshold=10000,  # Create payload index after 10k points
            ),
        )
        
        # Create index on paper_id field for faster filtering
        try:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="paper_id",
                field_schema=models.PayloadSchemaType.INTEGER,
            )
        except Exception as e:
            print(f"[INFO] Payload index may already exist or creation skipped: {e}")


def upsert_vectors(vectors: List[List[float]], payloads: List[Dict], ids: Optional[List[int]] = None):
    """
    Upsert vectors to Qdrant collection.
    
    Args:
        vectors: List of embedding vectors
        payloads: List of payload dictionaries with metadata
        ids: Optional list of IDs. If None, generates unique UUIDs.
    
    Note: We use UUIDs to avoid race conditions when uploading multiple papers
    concurrently. IDs are not needed for retrieval since we search by vector
    similarity and filter by paper_id in the payload.
    """
    if ids is None:
        # Generate unique UUIDs to avoid ID collisions during concurrent uploads
        # Use uuid4().int to get integer IDs that Qdrant can handle
        ids = [uuid.uuid4().int % (2**63 - 1) for _ in range(len(vectors))]
    
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=models.Batch(vectors=vectors, payloads=payloads, ids=ids),
    )


def search(vector: List[float], limit: int = 5, query_filter: Optional[models.Filter] = None, score_threshold: float = None):
    """
    Search for similar vectors with optional filtering and score threshold.
    
    Args:
        vector: Query vector
        limit: Maximum number of results
        query_filter: Optional filter for paper_ids or other fields
        score_threshold: Minimum similarity score (0.0-1.0). Results below this are filtered out.
    """
    search_params = {
        "collection_name": COLLECTION_NAME,
        "query_vector": vector,
        "limit": limit,
        "query_filter": query_filter,
    }
    
    # Add score threshold if provided (filters out low-quality matches)
    if score_threshold is not None:
        search_params["score_threshold"] = score_threshold
    
    # Use search params to configure HNSW search
    search_params["with_payload"] = True
    search_params["with_vectors"] = False  # Don't return vectors to save bandwidth
    
    return client.search(**search_params)

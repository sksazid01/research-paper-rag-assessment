from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(host="localhost", port=6333)
collection_name = "research_papers"

def init_collection():
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
    )

def add_vectors(vectors, metadata_list):
    client.upsert(
        collection_name=collection_name,
        points=models.Batch(
            vectors=vectors,
            payloads=metadata_list,
            ids=list(range(len(vectors)))
        )
    )
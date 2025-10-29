from sentence_transformers import SentenceTransformer

def generate_embeddings(chunks):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model.encode(chunks)
from fastapi import FastAPI
from typing import Dict

from .models.db import init_db, SessionLocal, Paper
from .services import qdrant_client
from .api.routes import router
from .models.db import init_db

app = FastAPI(title="Research Paper RAG System")
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "RAG System API is running"}


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health() -> Dict:
    """Lightweight readiness endpoint with best-effort checks."""
    status = {
        "status": "ok",
        "db": False,
        "qdrant": False,
    }
    # DB check
    try:
        with SessionLocal() as session:
            session.query(Paper).count()
        status["db"] = True
    except Exception:
        status["db"] = False
    # Qdrant check
    try:
        qdrant_client.client.get_collections()
        status["qdrant"] = True
    except Exception:
        status["qdrant"] = False
    return status
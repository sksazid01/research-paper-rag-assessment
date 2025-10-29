from fastapi import FastAPI
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
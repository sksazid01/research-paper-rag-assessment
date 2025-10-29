from fastapi import FastAPI
from .api.routes import router

app = FastAPI(title="Research Paper RAG System")
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "RAG System API is running"}
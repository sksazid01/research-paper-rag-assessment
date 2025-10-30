import asyncio
import json
import os
from typing import List, Optional

from fastapi import APIRouter, UploadFile, HTTPException, File

from ..services import pdf_processor, embedding_service, qdrant_client
from ..services.chunking import chunk_sentences
from ..models.db import save_paper_meta

router = APIRouter(prefix="/api")

UPLOAD_DIR = "temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/papers/upload")
async def upload_papers(
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),
):
    try:
        # Support either field name: `files` (preferred, array) or `file` (single)
        if files is None and file is not None:
            files = [file]
        if not files:
            raise HTTPException(status_code=422, detail="Field 'files' (array) or 'file' (single) is required")

        # Ensure Qdrant collection is ready based on model dimension(384)
        qdrant_client.ensure_collection(embedding_service.get_model_dim())

        async def process_one(file: UploadFile):
            # file_path = "temp/paper_1.pdf"
            file_path = os.path.join(UPLOAD_DIR, file.filename) 
            # This opens a new file(pdf) for writing in binary mode.
            with open(file_path, "wb") as f:
                # the file is physically saved to my  temp/ folder.
                f.write(await file.read())

            meta, sentences = pdf_processor.extract_sections_and_sentences(file_path)
            # Save paper metadata
            paper_id = save_paper_meta(
                title=meta.get("title"),
                authors=meta.get("authors"),
                year=meta.get("year"),
                filename=file.filename,
                pages=meta.get("pages"), # return the number of pages
            )

            # Chunking
            chunks = chunk_sentences(sentences)
            texts = [c["text"] for c in chunks]
            # print(chunks)

            # Embeddings (batched)
            vectors = embedding_service.get_embeddings(texts)

            # Build payloads with metadata
            payloads = []
            for c in chunks:
                payloads.append(
                    {
                        "paper_id": paper_id,
                        "paper_title": meta.get("title"),
                        "section": c["section"],
                        "page_start": c["page_start"],
                        "page_end": c["page_end"],
                        "chunk_index": c["chunk_index"],
                        "text": c["text"],
                    }
                )

            qdrant_client.upsert_vectors(vectors, payloads)

            # Save chunks to temp as JSON for inspection / offline use
            chunks_out = {
                "paper_id": paper_id,
                "filename": file.filename,
                "metadata": meta,
                "chunks": chunks,
            }
            chunks_file = os.path.join(UPLOAD_DIR, f"{paper_id}_chunks.json")
            with open(chunks_file, "w", encoding="utf-8") as jf:
                json.dump(chunks_out, jf, ensure_ascii=False, indent=2)

            return {
                "filename": file.filename,
                "paper_id": paper_id,
                "metadata": meta,
                "chunks": len(chunks),
                "chunks_file": chunks_file,
            }

        # Limit concurrency to avoid CPU thrash; process up to 3 at a time
        semaphore = asyncio.Semaphore(3)

        async def sem_task(f: UploadFile):
            async with semaphore:
                return await process_one(f)

        results = await asyncio.gather(*[sem_task(f) for f in files])
        return {"processed": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
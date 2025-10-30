import asyncio
import json
import os
from typing import List, Optional, Union

from fastapi import APIRouter, UploadFile, HTTPException, File

from ..services import pdf_processor, embedding_service, qdrant_client
from ..services.chunking import chunk_sentences
from ..models.db import save_paper_meta

router = APIRouter(prefix="/api")

UPLOAD_DIR = "temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/papers/upload")
async def upload_papers(
    files: List[UploadFile] = File(default=[]),
    file: List[UploadFile] = File(default=[]),
):
    try:
        # Support either field name: `files` (preferred, array) or `file` (single or multiple with same key)
        upload_files = []
        
        if files:
            upload_files.extend(files)
        
        if file:
            # Handle both single file and multiple files sent with same "file" key
            if isinstance(file, list):
                upload_files.extend(file)
            else:
                upload_files.append(file)
        
        if not upload_files:
            raise HTTPException(status_code=422, detail="Field 'files' (array) or 'file' (single/multiple) is required")
        
        files = upload_files  # Normalize to files variable for processing
        
        # Log how many files received for debugging
        print(f"[DEBUG] Received {len(files)} file(s): {[f.filename for f in files]}")

        # Ensure temp directory exists (recreate if deleted)
        os.makedirs(UPLOAD_DIR, exist_ok=True)

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
            chunks_file = os.path.join(UPLOAD_DIR, f"{os.path.splitext(file.filename)[0]}_chunks.json")
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


@router.post("/query")
async def query_papers(
    question: str,
    top_k: int = 5,
    paper_ids: Optional[List[int]] = None,
    model: str = "llama3"
):
    """
    Intelligent Query System - Answer questions using RAG pipeline.
    
    Request body:
    {
      "question": "What methodology was used in the transformer paper?",
      "top_k": 5,
      "paper_ids": [1, 3]  // optional: limit to specific papers
      "model": "llama3"     // optional: LLM model to use
    }
    
    Response format matches Task_Instructions.md specification:
    {
      "answer": "The transformer paper uses...",
      "citations": [
        {
          "paper_title": "Attention is All You Need",
          "section": "Methodology",
          "page": "3-4",
          "relevance_score": 0.89
        }
      ],
      "sources_used": ["paper3_nlp_transformers.pdf"],
      "confidence": 0.85
    }
    """
    try:
        if not question or not question.strip():
            raise HTTPException(status_code=422, detail="Field 'question' is required and cannot be empty")
        
        # Validate top_k
        if top_k < 1 or top_k > 50:
            raise HTTPException(status_code=422, detail="Field 'top_k' must be between 1 and 50")
        
        # Import rag_pipeline here to avoid circular imports
        from ..services import rag_pipeline
        
        # Generate answer using RAG pipeline
        result = rag_pipeline.answer(
            query=question,
            model=model,
            top_k=top_k,
            paper_ids=paper_ids
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[ERROR] Query failed: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")
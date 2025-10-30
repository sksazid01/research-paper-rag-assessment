import asyncio
import json
import os
from typing import List, Optional, Union

from fastapi import APIRouter, UploadFile, HTTPException, File, Request
import time

from ..services import pdf_processor, embedding_service, qdrant_client
from ..services.chunking import chunk_sentences
from ..models.db import save_paper_meta, save_query_history, list_recent_queries, get_popular_topics

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

        # Validate file types: PDF only
        invalid = []
        for f in files:
            fname = (f.filename or "").lower()
            ctype = (f.content_type or "").lower()
            if not (fname.endswith(".pdf") or ctype == "application/pdf"):
                invalid.append(f.filename)
        if invalid:
            raise HTTPException(
                status_code=422,
                detail=f"Only PDF files are accepted. Invalid files: {invalid}. Please upload .pdf files only."
            )

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
    request: Request,
    question: Optional[str] = None,
    top_k: int = 5,
    paper_ids: Optional[List[int]] = None,
    model: str = "llama3",
    rating: Optional[int] = None,
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
        # Accept both JSON body and query params
        try:
            body = await request.json()
            if isinstance(body, dict):
                question = body.get("question", question)
                top_k = int(body.get("top_k", top_k))
                paper_ids = body.get("paper_ids", paper_ids)
                model = body.get("model", model)
                rating = body.get("rating", rating)
        except Exception:
            pass

        if not question or not str(question).strip():
            raise HTTPException(status_code=422, detail="Field 'question' is required and cannot be empty")
        
        # Validate top_k
        if top_k < 1 or top_k > 50:
            raise HTTPException(status_code=422, detail="Field 'top_k' must be between 1 and 50")
        
        # Import rag_pipeline here to avoid circular imports
        from ..services import rag_pipeline
        
        # Generate answer using RAG pipeline
        start = time.perf_counter()
        result = rag_pipeline.answer(
            query=question,
            model=model,
            top_k=top_k,
            paper_ids=paper_ids
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # Persist query history (best-effort; do not fail the request if this fails)
        try:
            used_ids = result.get("paper_ids_used") or []
            save_query_history(
                question=question,
                paper_ids=used_ids,
                response_time_ms=elapsed_ms,
                confidence=result.get("confidence"),
                rating=rating,
            )
        except Exception as hist_err:
            print(f"[WARNING] Failed to save query history: {hist_err}")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[ERROR] Query failed: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


# ============================================================================
# Query History & Analytics Endpoints
# ============================================================================

@router.get("/queries/history")
async def get_query_history(limit: int = 20):
    """Return recent queries with referenced papers and metadata."""
    try:
        limit = max(1, min(limit, 100))
        items = list_recent_queries(limit=limit)
        return {"queries": items, "total": len(items)}
    except Exception as e:
        print(f"[ERROR] Get query history failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve query history")


@router.get("/analytics/popular")
async def get_popular_analytics(limit: int = 10):
    """Return most queried topics from recent queries (naive keyword frequency)."""
    try:
        limit = max(1, min(limit, 50))
        topics = get_popular_topics(limit=limit)
        return {"popular_topics": topics}
    except Exception as e:
        print(f"[ERROR] Get analytics popular failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute analytics")


# ============================================================================
# Paper Management Endpoints
# ============================================================================

@router.get("/papers")
async def list_papers():
    """
    List all papers in the database.
    
    Returns:
    {
      "papers": [
        {
          "id": 1,
          "title": "Sustainability in Blockchain",
          "authors": "Hani Alshahrani, ...",
          "year": "2023",
          "filename": "paper_1.pdf",
          "pages": 24,
          "created_at": "2025-10-30T12:00:00"
        }
      ],
      "total": 1
    }
    """
    try:
        from ..models.db import SessionLocal, Paper
        
        with SessionLocal() as session:
            papers = session.query(Paper).order_by(Paper.created_at.desc()).all()
            
            result = []
            for paper in papers:
                result.append({
                    "id": paper.id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "year": paper.year,
                    "filename": paper.filename,
                    "pages": paper.pages,
                    "created_at": paper.created_at.isoformat() if paper.created_at else None
                })
            
            return {"papers": result, "total": len(result)}
    
    except Exception as e:
        import traceback
        print(f"[ERROR] List papers failed: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to list papers: {str(e)}")


@router.get("/papers/{paper_id}")
async def get_paper(paper_id: int):
    """
    Get details of a specific paper by ID.
    
    Returns:
    {
      "id": 1,
      "title": "Sustainability in Blockchain",
      "authors": "Hani Alshahrani, ...",
      "year": "2023",
      "filename": "paper_1.pdf",
      "pages": 24,
      "created_at": "2025-10-30T12:00:00"
    }
    """
    try:
        from ..models.db import SessionLocal, Paper
        
        with SessionLocal() as session:
            paper = session.query(Paper).filter(Paper.id == paper_id).first()
            
            if not paper:
                raise HTTPException(status_code=404, detail=f"Paper with ID {paper_id} not found")
            
            return {
                "id": paper.id,
                "title": paper.title,
                "authors": paper.authors,
                "year": paper.year,
                "filename": paper.filename,
                "pages": paper.pages,
                "created_at": paper.created_at.isoformat() if paper.created_at else None
            }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[ERROR] Get paper failed: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get paper: {str(e)}")


@router.delete("/papers/{paper_id}")
async def delete_paper(paper_id: int):
    """
    Delete a paper from the database and remove its vectors from Qdrant.
    
    Returns:
    {
      "message": "Paper deleted successfully",
      "paper_id": 1,
      "vectors_deleted": 119
    }
    """
    try:
        from ..models.db import SessionLocal, Paper
        from qdrant_client.http import models as qdrant_models
        
        with SessionLocal() as session:
            paper = session.query(Paper).filter(Paper.id == paper_id).first()
            
            if not paper:
                raise HTTPException(status_code=404, detail=f"Paper with ID {paper_id} not found")
            
            paper_title = paper.title or paper.filename
            
            # Delete vectors from Qdrant
            try:
                # Delete all points where paper_id matches
                qdrant_client.client.delete(
                    collection_name=qdrant_client.COLLECTION_NAME,
                    points_selector=qdrant_models.FilterSelector(
                        filter=qdrant_models.Filter(
                            must=[
                                qdrant_models.FieldCondition(
                                    key="paper_id",
                                    match=qdrant_models.MatchValue(value=paper_id)
                                )
                            ]
                        )
                    )
                )
                vectors_deleted = True
            except Exception as e:
                print(f"[WARNING] Failed to delete vectors from Qdrant: {e}")
                vectors_deleted = False
            
            # Delete paper from database
            session.delete(paper)
            session.commit()
            
            return {
                "message": "Paper deleted successfully",
                "paper_id": paper_id,
                "paper_title": paper_title,
                "vectors_deleted": vectors_deleted
            }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[ERROR] Delete paper failed: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to delete paper: {str(e)}")


@router.get("/papers/{paper_id}/stats")
async def get_paper_stats(paper_id: int):
    """
    Get statistics for a specific paper.
    
    Returns:
    {
      "paper_id": 1,
      "title": "Sustainability in Blockchain",
      "filename": "paper_1.pdf",
      "pages": 24,
      "total_chunks": 119,
      "sections": {
        "Abstract": 7,
        "Introduction": 35,
        "Methods": 12,
        "Results": 33,
        "Discussion": 1,
        "Conclusion": 4,
        "References": 27
      },
      "avg_chunk_length": 450,
      "created_at": "2025-10-30T12:00:00"
    }
    """
    try:
        from ..models.db import SessionLocal, Paper
        from collections import Counter
        
        with SessionLocal() as session:
            paper = session.query(Paper).filter(Paper.id == paper_id).first()
            
            if not paper:
                raise HTTPException(status_code=404, detail=f"Paper with ID {paper_id} not found")
            
            # Query Qdrant for all chunks of this paper
            try:
                from qdrant_client.http import models as qdrant_models
                
                # Scroll through all points for this paper
                scroll_result = qdrant_client.client.scroll(
                    collection_name=qdrant_client.COLLECTION_NAME,
                    scroll_filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="paper_id",
                                match=qdrant_models.MatchValue(value=paper_id)
                            )
                        ]
                    ),
                    limit=1000,  # Get up to 1000 chunks
                    with_payload=True,
                    with_vectors=False
                )
                
                chunks = scroll_result[0] if scroll_result else []
                
                # Calculate statistics
                sections = Counter()
                chunk_lengths = []
                
                for point in chunks:
                    payload = point.payload or {}
                    section = payload.get("section", "Unknown")
                    text = payload.get("text", "")
                    
                    sections[section] += 1
                    chunk_lengths.append(len(text))
                
                avg_chunk_length = int(sum(chunk_lengths) / len(chunk_lengths)) if chunk_lengths else 0
                
                return {
                    "paper_id": paper.id,
                    "title": paper.title,
                    "filename": paper.filename,
                    "pages": paper.pages,
                    "total_chunks": len(chunks),
                    "sections": dict(sections),
                    "avg_chunk_length": avg_chunk_length,
                    "created_at": paper.created_at.isoformat() if paper.created_at else None
                }
                
            except Exception as e:
                print(f"[WARNING] Failed to get chunk stats from Qdrant: {e}")
                # Return basic stats without chunk information
                return {
                    "paper_id": paper.id,
                    "title": paper.title,
                    "filename": paper.filename,
                    "pages": paper.pages,
                    "total_chunks": 0,
                    "sections": {},
                    "avg_chunk_length": 0,
                    "created_at": paper.created_at.isoformat() if paper.created_at else None,
                    "note": "Chunk statistics unavailable"
                }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[ERROR] Get paper stats failed: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get paper stats: {str(e)}")
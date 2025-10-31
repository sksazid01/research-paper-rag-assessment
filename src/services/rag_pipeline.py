from typing import List, Dict, Optional
import re

from qdrant_client.http import models

from . import qdrant_client
from .embedding_service import get_embeddings
from .ollama_client import generate_text
from ..models.db import SessionLocal, Paper


def get_paper_info(paper_id: int) -> Optional[Dict]:
	"""Fetch paper metadata from database."""
	with SessionLocal() as session:
		paper = session.query(Paper).filter(Paper.id == paper_id).first()
		if paper:
			return {
				"id": paper.id,
				"title": paper.title,
				"authors": paper.authors,
				"year": paper.year,
				"filename": paper.filename,
				"pages": paper.pages,
			}
	return None


def retrieve_context(query: str, top_k: int = 5, paper_ids: Optional[List[int]] = None) -> List[Dict]:
	"""Embed the query and retrieve top_k chunks from Qdrant with optional paper filtering."""
	vec = get_embeddings([query])[0]
	
	# Build filter if paper_ids provided
	query_filter = None
	if paper_ids:
		# Filter by paper_id using Qdrant's match any
		query_filter = models.Filter(
			should=[
				models.FieldCondition(
					key="paper_id",
					match=models.MatchValue(value=pid)
				)
				for pid in paper_ids
			]
		)
	
	# Use score threshold to filter out irrelevant results (speeds up by reducing processing)
	# Cosine similarity: 0.0-1.0, higher is better. 0.3 filters out very weak matches.
	hits = qdrant_client.search(vec, limit=top_k, query_filter=query_filter, score_threshold=0.3)
	
	# Batch fetch paper metadata to avoid N+1 queries
	unique_paper_ids = list(set(h.payload.get("paper_id") for h in hits if h.payload and h.payload.get("paper_id")))
	paper_info_map = {}
	
	if unique_paper_ids:
		with SessionLocal() as session:
			papers = session.query(Paper).filter(Paper.id.in_(unique_paper_ids)).all()
			paper_info_map = {
				p.id: {
					"id": p.id,
					"title": p.title,
					"authors": p.authors,
					"year": p.year,
					"filename": p.filename,
					"pages": p.pages,
				}
				for p in papers
			}
	
	contexts = []
	for h in hits:
		payload = h.payload or {}
		paper_id = payload.get("paper_id")
		paper_info = paper_info_map.get(paper_id)
		
		contexts.append({
			"text": payload.get("text") or "",
			"section": payload.get("section"),
			"page_start": payload.get("page_start"),
			"page_end": payload.get("page_end"),
			"paper_id": paper_id,
			"paper_title": paper_info.get("title") if paper_info else f"Paper {paper_id}",
			"paper_filename": paper_info.get("filename") if paper_info else None,
			"score": h.score,
		})
	return contexts


def assemble_prompt(query: str, contexts: List[Dict]) -> str:
	"""Build prompt with context and citation instructions."""
	ctx_block = "\n\n".join(
		f"[Source {i+1}: {c.get('paper_title')} | Section: {c.get('section')} | Pages: {c.get('page_start')}-{c.get('page_end')}]\n{c['text']}"
		for i, c in enumerate(contexts)
	)
	prompt = (
		"You are a helpful research assistant. Answer the question based STRICTLY on the provided context.\n"
		"IMPORTANT: Include citations in your answer using the format (Source N) where N is the source number.\n"
		"If the context doesn't contain enough information to answer confidently, say so.\n\n"
		f"Question: {query}\n\n"
		f"Context:\n{ctx_block}\n\n"
		"Answer (include citations):"
	)
	return prompt


def extract_citations_from_answer(answer_text: str, contexts: List[Dict]) -> List[Dict]:
	"""Extract citations from LLM answer and map to context metadata."""
	citations = []
	seen = set()
	
	# Look for patterns like (Source 1), (Source 2), etc.
	pattern = r'\(Source\s+(\d+)\)'
	matches = re.findall(pattern, answer_text, re.IGNORECASE)
	
	for match in matches:
		idx = int(match) - 1  # Convert to 0-based index
		if 0 <= idx < len(contexts) and idx not in seen:
			seen.add(idx)
			c = contexts[idx]
			citations.append({
				"paper_title": c.get("paper_title"),
				"section": c.get("section"),
				"page": f"{c.get('page_start')}-{c.get('page_end')}",
				"relevance_score": round(c.get("score", 0.0), 2)
			})
	
	return citations


def calculate_confidence(contexts: List[Dict], answer_text: str) -> float:
	"""Calculate confidence score based on retrieval scores and answer characteristics."""
	if not contexts:
		return 0.0
	
	# Average of top retrieval scores (weighted toward top results)
	avg_score = sum(c.get("score", 0) * (1.0 / (i + 1)) for i, c in enumerate(contexts[:3])) / 3.0
	
	# Boost if answer contains citations
	has_citations = bool(re.search(r'\(Source\s+\d+\)', answer_text, re.IGNORECASE))
	citation_boost = 0.1 if has_citations else 0.0
	
	# Penalize if answer says "I don't know" or similar
	uncertainty_phrases = ["don't know", "not sure", "cannot answer", "insufficient information"]
	has_uncertainty = any(phrase in answer_text.lower() for phrase in uncertainty_phrases)
	uncertainty_penalty = -0.2 if has_uncertainty else 0.0
	
	confidence = min(1.0, max(0.0, avg_score + citation_boost + uncertainty_penalty))
	return round(confidence, 2)


def answer(query: str, model: str = "llama3", top_k: int = 5, paper_ids: Optional[List[int]] = None) -> Dict:
	"""Generate answer with citations following Task_Instructions.md spec."""
	# Retrieve relevant contexts
	contexts = retrieve_context(query, top_k=top_k, paper_ids=paper_ids)
	
	if not contexts:
		return {
			"answer": "No relevant information found in the database.",
			"citations": [],
			"sources_used": [],
			"confidence": 0.0
		}
	
	# Assemble prompt and generate answer
	prompt = assemble_prompt(query, contexts)
	llm_resp = generate_text(prompt, model=model, max_tokens=512, temperature=0.0)
	
	# Extract answer text from Ollama response
	answer_text = ""
	if llm_resp.get("source") == "http":
		resp_data = llm_resp.get("response", {})
		# Handle different Ollama response formats
		if isinstance(resp_data, dict):
			answer_text = resp_data.get("response") or resp_data.get("text") or resp_data.get("raw", "")
		else:
			answer_text = str(resp_data)
	elif llm_resp.get("source") == "cli":
		resp_data = llm_resp.get("response", {})
		answer_text = resp_data.get("response") or resp_data.get("raw", "")
	else:
		answer_text = str(llm_resp)
	
	# Extract citations from answer
	citations = extract_citations_from_answer(answer_text, contexts)
	
	# Get unique sources used (filenames) and paper ids
	sources_used = list(set(c.get("paper_filename") for c in contexts if c.get("paper_filename")))
	paper_ids_used = list({c.get("paper_id") for c in contexts if c.get("paper_id") is not None})
	
	# Calculate confidence
	confidence = calculate_confidence(contexts, answer_text)
	
	return {
		"answer": answer_text.strip(),
		"citations": citations,
		"sources_used": sources_used,
		"confidence": confidence,
		"paper_ids_used": paper_ids_used
	}


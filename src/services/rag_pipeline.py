from typing import List, Dict, Optional
import re
import os

from qdrant_client.http import models
from sentence_transformers import CrossEncoder

from . import qdrant_client
from .embedding_service import get_embeddings
from .ollama_client import generate_text
from ..models.db import SessionLocal, Paper

# Initialize cross-encoder for re-ranking (lazy loaded)
_cross_encoder = None

def get_cross_encoder():
	"""Lazy load cross-encoder model for re-ranking."""
	global _cross_encoder
	if _cross_encoder is None:
		model_name = os.getenv("CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
		print(f"[INFO] Loading cross-encoder model: {model_name}")
		_cross_encoder = CrossEncoder(model_name)
	return _cross_encoder


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
	
	# Use a modest score threshold to filter out very-weak matches while avoiding
	# dropping useful context for shorter queries. Empirically a lower threshold
	# (e.g. 0.15) works better with sentence-transformer embeddings for short
	# queries; make it easy to tune/debug here.
	# SPECIAL CASE: If filtering to specific papers detected from the question,
	# be even more lenient (0.05) to avoid missing the target paper due to weak title extraction
	import os
	SCORE_THRESHOLD_DEFAULT = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.15"))
	SCORE_THRESHOLD_FILTERED = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD_FILTERED", "0.05"))
	SCORE_THRESHOLD = SCORE_THRESHOLD_FILTERED if paper_ids else SCORE_THRESHOLD_DEFAULT
	hits = qdrant_client.search(vec, limit=top_k, query_filter=query_filter, score_threshold=SCORE_THRESHOLD)

	# Debug output to aid diagnosis when no hits are returned in runtime
	try:
		if not hits:
			print(f"[DEBUG] retrieve_context: no hits returned for query (top_k={top_k}, threshold={SCORE_THRESHOLD})")
		else:
			scores = [round(h.score, 4) for h in hits]
			print(f"[DEBUG] retrieve_context: returned {len(hits)} hits, scores={scores}")
	except Exception:
		# Keep retrieval robust even if debug printing fails
		pass
	
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
	# Lightweight keyword boost to favor matches that contain query terms like
	# "attention" or "transformer" directly in the chunk text. This helps in
	# title-specific questions without relying on exact payload filters.
	import os
	TEXT_BOOST = float(os.getenv("RERANK_TEXT_BOOST", "0.15"))
	TITLE_BOOST = float(os.getenv("RERANK_TITLE_BOOST", "0.30"))
	
	ql = (query or "").lower()
	boost_terms = [t for t in ["attention", "transformer", "transformers", "nlp", "neural network"] if t in ql]
	if boost_terms:
		def boosted(c):
			text = (c.get("text") or "").lower()
			title = (c.get("paper_title") or "").lower()
			# Give bigger boost if terms appear in chunk text (configurable per term)
			# Also boost if terms appear in title (configurable per term) for stronger signal
			bonus = sum(TEXT_BOOST for t in boost_terms if t in text)
			bonus += sum(TITLE_BOOST for t in boost_terms if t in title)
			return c.get("score", 0.0) + bonus
		contexts.sort(key=boosted, reverse=True)
	return contexts


def rerank_contexts(query: str, contexts: List[Dict], top_k: int = None) -> List[Dict]:
	"""
	Re-rank retrieved contexts using a cross-encoder model for better relevance.
	
	Cross-encoders jointly encode query and passage, providing more accurate
	relevance scores than bi-encoders (used for initial retrieval).
	
	Args:
		query: User question
		contexts: List of context dicts from retrieve_context()
		top_k: Return only top_k re-ranked results (defaults to all)
	
	Returns:
		Contexts re-ordered by cross-encoder scores
	"""
	if not contexts:
		return contexts
	
	# Check if re-ranking is enabled
	enable_rerank = os.getenv("ENABLE_CROSS_ENCODER_RERANK", "true").lower() == "true"
	if not enable_rerank:
		return contexts
	
	try:
		cross_encoder = get_cross_encoder()
		
		# Prepare (query, passage) pairs for cross-encoder
		pairs = [(query, ctx.get("text", "")) for ctx in contexts]
		
		# Get relevance scores from cross-encoder
		scores = cross_encoder.predict(pairs)
		
		# Combine scores with contexts and sort
		scored_contexts = list(zip(scores, contexts))
		scored_contexts.sort(key=lambda x: x[0], reverse=True)
		
		# Update original score with cross-encoder score for transparency
		reranked = []
		for ce_score, ctx in scored_contexts:
			ctx_copy = ctx.copy()
			ctx_copy["original_score"] = ctx.get("score", 0.0)
			ctx_copy["score"] = float(ce_score)  # Replace with cross-encoder score
			reranked.append(ctx_copy)
		
		# Return top_k if specified
		if top_k:
			reranked = reranked[:top_k]
		
		print(f"[INFO] Re-ranked {len(contexts)} contexts using cross-encoder")
		return reranked
		
	except Exception as e:
		print(f"[WARNING] Cross-encoder re-ranking failed: {e}. Falling back to original order.")
		return contexts


def _extract_quoted_titles(question: str) -> List[str]:
	"""Return phrases found inside single or double quotes in the question."""
	phrases = re.findall(r"'([^']+)'|\"([^\"]+)\"", question)
	# matches return tuples, pick non-empty parts
	out = []
	for a, b in phrases:
		phrase = a or b
		phrase = phrase.strip()
		if phrase:
			out.append(phrase)
	return out


def _guess_candidate_paper_ids(question: str) -> List[int]:
	"""Heuristic: try to detect which paper(s) the question refers to by
	matching quoted titles or key terms against stored Paper.title/filename.
	This narrows retrieval to the most likely sources when users name a paper.
	
	IMPORTANT: When metadata extraction fails (e.g., "Template EN Multiple authors"),
	we rely on keyword matching in chunk content during retrieval + re-ranking.
	Return empty list to search all papers if no strong title match is found.
	"""
	q_lower = (question or "").lower()
	quoted = [p.lower() for p in _extract_quoted_titles(question)]

	# Keyword hints to map generic questions to likely domains
	# More specific keywords for transformer/attention papers
	transformer_kw = ["attention", "transformer", "transformers", "self-attention", "bert", "gpt"]
	vision_kw = ["convolution", "cnn", "vision", "resnet", "image"]
	rl_kw = ["reinforcement", "rl", "agent", "policy", "reward"]
	ml_kw = ["neural", "network", "machine learning", "deep learning"]
	blockchain_kw = ["blockchain", "sustainability", "bitcoin", "cryptocurrency"]
	
	detected_keywords = []
	if any(k in q_lower for k in transformer_kw):
		detected_keywords.extend(transformer_kw)
	if any(k in q_lower for k in vision_kw):
		detected_keywords.extend(vision_kw)
	if any(k in q_lower for k in rl_kw):
		detected_keywords.extend(rl_kw)
	if any(k in q_lower for k in ml_kw):
		detected_keywords.extend(ml_kw)
	if any(k in q_lower for k in blockchain_kw):
		detected_keywords.extend(blockchain_kw)

	candidate_ids: List[int] = []
	strong_match_found = False
	
	try:
		with SessionLocal() as session:
			papers = session.query(Paper).all()
			for p in papers:
				searchable = f"{p.title or ''} {p.filename or ''}".lower()
				# Strong match: quoted phrase appears in title or filename
				if any(ph in searchable for ph in quoted if len(ph) > 5):
					candidate_ids.append(p.id)
					strong_match_found = True
					continue
				# Medium match: multiple keywords appear in title
				if detected_keywords:
					kw_count = sum(1 for kw in detected_keywords if kw in searchable)
					if kw_count >= 2:  # At least 2 keywords match
						candidate_ids.append(p.id)
	except Exception:
		# Fail open: if DB not available, just return empty to not block queries
		pass

	# If we found strong matches (quoted title), use those
	# If only weak keyword matches or nothing, return empty to search all papers
	# and rely on semantic search + keyword re-ranking
	if not strong_match_found and len(candidate_ids) < 2:
		return []

	# Keep order but unique
	seen = set()
	result = []
	for pid in candidate_ids:
		if pid not in seen:
			seen.add(pid)
			result.append(pid)
	return result


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
				"paper_filename": c.get("paper_filename"),
				"paper_id": c.get("paper_id"),
				# source_index is 1-based and corresponds to the (Source N) label in the LLM answer
				"source_index": idx + 1,
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
	# Guard: detect non-research queries (greetings, small talk, off-topic)
	q_lower = (query or "").lower().strip()
	non_research_patterns = [
		"hi", "hello", "hey", "how are you", "what's up", "whats up",
		"good morning", "good afternoon", "good evening",
		"thanks", "thank you", "bye", "goodbye",
		"who are you", "what are you", "your name"
	]
	
	# Check if query is too short or matches greeting patterns
	if len(q_lower) < 5 or any(pattern == q_lower or q_lower.startswith(pattern + " ") for pattern in non_research_patterns):
		return {
			"answer": "Hello! I'm a research assistant specialized in answering questions about uploaded research papers. Please ask me a specific question about the papers in the database (e.g., 'What methodology was used?' or 'Explain the attention mechanism').",
			"citations": [],
			"sources_used": [],
			"confidence": 0.0
		}
	
	# If user didn't explicitly filter, try to detect target papers from the question
	detected_ids: Optional[List[int]] = None
	if not paper_ids:
		detected_ids = _guess_candidate_paper_ids(query)
		if detected_ids:
			print(f"[DEBUG] Detected candidate papers from question: {detected_ids}")

	# Merge explicit + detected filters if present
	merged_ids = None
	if paper_ids and detected_ids:
		merged_ids = list({*paper_ids, *detected_ids})
	else:
		merged_ids = paper_ids or detected_ids

	# Retrieve relevant contexts (optionally filtered to candidate paper ids)
	# Fetch more candidates than needed for re-ranking
	retrieval_multiplier = int(os.getenv("RERANK_RETRIEVAL_MULTIPLIER", "2"))
	initial_top_k = top_k * retrieval_multiplier
	contexts = retrieve_context(query, top_k=initial_top_k, paper_ids=merged_ids)
	
	# Re-rank contexts using cross-encoder for better relevance
	if contexts:
		contexts = rerank_contexts(query, contexts, top_k=top_k)
	
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


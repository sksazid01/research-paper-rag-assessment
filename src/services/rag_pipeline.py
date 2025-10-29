from typing import List, Dict

from . import qdrant_client
from .embedding_service import get_embeddings
from .ollama_client import generate_text


def retrieve_context(query: str, top_k: int = 5) -> List[Dict]:
	"""Embed the query and retrieve top_k chunks from Qdrant."""
	vec = get_embeddings([query])[0]
	hits = qdrant_client.search(vec, limit=top_k)
	contexts = []
	for h in hits:
		payload = h.payload or {}
		contexts.append({
			"text": payload.get("text") or "",
			"section": payload.get("section"),
			"page_start": payload.get("page_start"),
			"page_end": payload.get("page_end"),
			"paper_id": payload.get("paper_id"),
			"score": h.score,
		})
	return contexts


def assemble_prompt(query: str, contexts: List[Dict]) -> str:
	ctx_block = "\n\n".join(
		f"[Paper {c.get('paper_id')} p.{c.get('page_start')}-{c.get('page_end')} | {c.get('section')}]\n{c['text']}"
		for c in contexts
	)
	prompt = (
		"You are a helpful research assistant. Answer based strictly on the context.\n"
		"Include citations like (paper_id:page).\n\n"
		f"Question: {query}\n\n"
		f"Context:\n{ctx_block}\n\n"
		"Answer:"
	)
	return prompt


def answer(query: str, model: str = "llama3", top_k: int = 5) -> Dict:
	contexts = retrieve_context(query, top_k=top_k)
	prompt = assemble_prompt(query, contexts)
	llm_resp = generate_text(prompt, model=model)
	return {"contexts": contexts, "llm": llm_resp}


"""
Lightweight Ollama client with HTTP and CLI fallback.

This module makes it easy to call a local Ollama instance (if running) or
fall back to the `ollama` CLI if available. It's intentionally small and
non-opinionated: use it for generation (and optionally embeddings if your
Ollama installation provides an embeddings API/model).

Usage examples:
  from services.ollama_client import generate_text
  resp = generate_text("Summarize: ...", model="llama3")

Notes:
- If your Ollama daemon runs at a different host/port, set OLLAMA_BASE_URL.
- The HTTP endpoints used are common guesses (/api/completions or /api/generate).
  Adjust if your Ollama version exposes different paths.
"""
import os
import json
import subprocess
from typing import Optional, Dict

import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def _http_post(path: str, payload: Dict, timeout: int = 120) -> Optional[Dict]:
    url = OLLAMA_BASE_URL.rstrip("/") + path
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        # Try to parse JSON; some Ollama versions stream NDJSON — caller should adapt.
        try:
            return r.json()
        except ValueError:
            return {"raw": r.text}
    except Exception as e:
        # Log error for debugging but don't print in production
        import sys
        print(f"[WARNING] Ollama HTTP request failed: {e}", file=sys.stderr)
        return None


def _cli_generate(prompt: str, model: str = "llama3", max_tokens: int = 512, temperature: float = 0.0) -> Dict:
    # Fallback to calling `ollama generate <model> <prompt>` if available
    try:
        cmd = ["ollama", "generate", model, prompt, "--json", "--max-tokens", str(max_tokens), "--temperature", str(temperature)]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        out = proc.stdout.strip()
        try:
            return json.loads(out)
        except Exception:
            return {"raw": out}
    except Exception as e:
        return {"error": str(e)}


def generate_text(prompt: str, model: str = "llama3", max_tokens: int = 512, temperature: float = 0.0) -> Dict:
    """Generate text using local Ollama.

    Tries HTTP first (daemon), then falls back to CLI. Returns a dict with the
    response (or an error field).
    """
    # Try HTTP with /api/generate endpoint (which returns streaming NDJSON by default)
    # We'll request non-streaming mode by setting "stream": false
    payload = {
        "model": model,
        "prompt": prompt,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature
        },
        "stream": False  # Disable streaming to get a single response
    }
    
    resp = _http_post("/api/generate", payload)
    if resp is not None:
        return {"source": "http", "response": resp}

    # Try /api/completions (less common)
    payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}
    resp = _http_post("/api/completions", payload)
    if resp is not None:
        return {"source": "http", "response": resp}

    # Fallback to CLI
    cli = _cli_generate(prompt, model=model, max_tokens=max_tokens, temperature=temperature)
    return {"source": "cli", "response": cli}


def embeddings_available() -> bool:
    """Return True if Ollama supports an embeddings endpoint (best-effort).

    We do a non-destructive probe. If your installed Ollama provides explicit
    embeddings, adapt get_embeddings() to call the correct endpoint.
    """
    # Try simple probe; many Ollama installations don't provide embeddings endpoint
    resp = _http_post("/api/embeddings", {"model": "", "input": "test"})
    return resp is not None


def get_embeddings(texts, model: str = "text-embedding-3-small"):
    """Attempt to get embeddings from Ollama HTTP; raise NotImplementedError if not available.

    If your Ollama supports embeddings, update this implementation to match its API.
    Otherwise, continue using `sentence-transformers` (recommended).
    """
    if not embeddings_available():
        raise NotImplementedError("Ollama does not expose embeddings in this environment. Use sentence-transformers instead.")

    payload = {"model": model, "input": texts}
    resp = _http_post("/api/embeddings", payload)
    if resp is None:
        raise RuntimeError("Failed to get embeddings from Ollama HTTP API")
    return resp

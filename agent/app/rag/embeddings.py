"""Embedding provider abstraction for the RAG pipeline.

Two backends, selected by ``EMBED_PROVIDER``:

* ``ollama`` (default) — local Ollama model (``nomic-embed-text``), the same
  pattern used by uade-rag. Free, offline, tenant-private.
* ``maas`` — a MaaS embedding model reached through the OpenAI-compatible
  ``/embeddings`` endpoint. Useful when Ollama cannot run in the tenant env.

Both expose :func:`embed_texts` (batch) and :func:`embed_query` (single).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingError(RuntimeError):
    pass


async def _ollama_embed(inputs: list[str]) -> list[list[float]]:
    """Call Ollama's REST embeddings endpoint for a batch of texts."""
    out: list[list[float]] = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for text in inputs:
            resp = await client.post(
                f"{settings.ollama_host.rstrip('/')}/api/embeddings",
                json={"model": settings.embed_model, "prompt": text},
            )
            if resp.status_code != 200:
                raise EmbeddingError(
                    f"ollama embeddings failed ({resp.status_code}): {resp.text[:200]}"
                )
            out.append(resp.json()["embedding"])
    return out


async def _maas_embed(inputs: list[str]) -> list[list[float]]:
    """Call the MaaS OpenAI-compatible embeddings endpoint."""
    if not settings.maas_enabled:
        raise EmbeddingError("MAAS_API_KEY is not set; cannot use maas embeddings")
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.maas_base_url.rstrip('/')}/embeddings",
            headers={"Authorization": f"Bearer {settings.maas_api_key}"},
            json={"model": settings.embed_model, "input": inputs},
        )
        if resp.status_code != 200:
            raise EmbeddingError(
                f"maas embeddings failed ({resp.status_code}): {resp.text[:200]}"
            )
        data = resp.json()
    # OpenAI-style response: data sorted by index.
    return [d["embedding"] for d in sorted(data["data"], key=lambda d: d.get("index", 0))]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    provider = settings.embed_provider.lower()
    if provider == "ollama":
        return await _ollama_embed(texts)
    if provider == "maas":
        return await _maas_embed(texts)
    raise EmbeddingError(f"unknown embed provider: {settings.embed_provider!r}")


async def embed_query(text: str) -> list[float]:
    vectors = await embed_texts([text])
    return vectors[0]


async def health() -> dict[str, Any]:
    """Lightweight reachability check for the configured embedding backend."""
    provider = settings.embed_provider.lower()
    try:
        if provider == "ollama":
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.ollama_host.rstrip('/')}/api/tags")
                ok = resp.status_code == 200
                return {"provider": "ollama", "ok": ok, "host": settings.ollama_host}
        if provider == "maas":
            return {"provider": "maas", "ok": settings.maas_enabled, "model": settings.embed_model}
    except Exception as exc:
        return {"provider": provider, "ok": False, "error": str(exc)}
    return {"provider": provider, "ok": False, "error": "unknown provider"}

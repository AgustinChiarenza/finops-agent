"""ChromaDB persistent vector store.

A thin singleton wrapper around :class:`chromadb.PersistentClient` so the
collection is created once per process and reused by both the ingest pipeline
and the retriever. The store is empty until a tenant runs ingest.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import chromadb

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _client() -> chromadb.api.ClientAPI:
    return chromadb.PersistentClient(path=settings.chroma_dir)


def get_collection():
    """Return (creating if needed) the configured FinOps knowledge collection."""
    return _client().get_or_create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )


def reset_collection():
    """Drop and recreate the collection — used by ingest to avoid duplicates."""
    client = _client()
    try:
        client.delete_collection(settings.chroma_collection)
    except Exception:
        pass
    return client.create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )


def count() -> int:
    try:
        return get_collection().count()
    except Exception:
        return 0

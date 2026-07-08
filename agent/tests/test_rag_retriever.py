"""Tests for the retriever's empty-store and embedding-failure degradation."""

import pytest

import app.rag.store as store
from app.rag import embeddings
from app.rag.retriever import Retriever


@pytest.mark.asyncio
async def test_retrieve_returns_empty_when_store_empty(monkeypatch):
    monkeypatch.setattr(store, "count", lambda: 0)
    hits = await Retriever().retrieve("¿cómo bajo el costo de ECS?")
    assert hits == []


@pytest.mark.asyncio
async def test_retrieve_returns_empty_on_embedding_failure(monkeypatch):
    monkeypatch.setattr(store, "count", lambda: 5)

    async def boom(_text):
        raise embeddings.EmbeddingError("ollama down")

    monkeypatch.setattr(embeddings, "embed_query", boom)
    hits = await Retriever().retrieve("¿cómo bajo el costo de ECS?")
    assert hits == []

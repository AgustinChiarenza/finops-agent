"""Semantic retrieval over the FinOps knowledge base.

Embeds the query with the configured provider, queries the Chroma collection,
and returns ranked chunks with metadata and distance. Supports an optional
metadata ``where`` filter (e.g. only ``pricing`` chunks) and a guard for an
empty store so the agent degrades gracefully when no knowledge has been
ingested yet.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.config import settings
from app.rag import embeddings, store

logger = logging.getLogger(__name__)


@dataclass
class RetrievalHit:
    document: str
    source: str
    tipo: str
    metadata: dict
    score: float  # similarity-ish; 1 - cosine distance

    def as_context_line(self) -> str:
        return f"[{self.source} | {self.tipo}]\n{self.document}"


class Retriever:
    async def retrieve(
        self,
        query: str,
        k: int | None = None,
        where: dict | None = None,
    ) -> list[RetrievalHit]:
        k = k or settings.rag_top_k
        if store.count() == 0:
            logger.info("RAG store empty — returning no context (run ingest first)")
            return []
        try:
            query_vec = await embeddings.embed_query(query)
        except embeddings.EmbeddingError as exc:
            logger.warning("embedding failed, retrieval skipped: %s", exc)
            return []

        collection = store.get_collection()
        query_kwargs = {"query_embeddings": [query_vec], "n_results": k}
        if where:
            query_kwargs["where"] = where
        res = collection.query(**query_kwargs)

        hits: list[RetrievalHit] = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            hits.append(RetrievalHit(
                document=doc,
                source=meta.get("source", "?"),
                tipo=meta.get("tipo", "reference"),
                metadata=dict(meta),
                score=round(1.0 - float(dist), 4),
            ))
        return hits

    async def retrieve_context(
        self,
        query: str,
        k: int | None = None,
        where: dict | None = None,
    ) -> tuple[str, list[RetrievalHit]]:
        """Return (joined_context_string, hits) for prompt building."""
        hits = await self.retrieve(query, k=k, where=where)
        if not hits:
            return "", []
        context = "\n\n---\n\n".join(h.as_context_line() for h in hits)
        return context, hits


retriever = Retriever()

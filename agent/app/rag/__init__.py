"""Retrieval-augmented generation over a FinOps knowledge base.

Structurally similar to the uade-rag project (Chroma + Ollama embeddings +
PDF/DOCX/MD ingest with overlap chunking) but oriented to cloud FinOps
knowledge: pricing guides, Well-Architected guidance, cost-optimization
playbooks, tagging policies, and case studies. The knowledge directory is
shipped empty — tenants ingest their own material via ``python -m app.rag.ingest``.
"""

from app.rag.retriever import Retriever, retriever
from app.rag.store import get_collection

__all__ = ["Retriever", "retriever", "get_collection"]

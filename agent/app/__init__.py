"""FinOps Agent — RAG + LiteLLM orchestrator over Huawei Cloud MaaS.

This package wires three capabilities together:

* ``orchestrator`` — LiteLLM router that fans requests out across multiple
  MaaS models with tier-based selection, fallbacks, and per-call cost tracking.
* ``rag`` — a retrieval-augmented-generation pipeline (Chroma + Ollama/MaaS
  embeddings) over a FinOps knowledge base, structurally similar to the
  uade-rag project but oriented to cloud cost-optimization knowledge.
* ``tools`` — an async HTTP client for the bundled Cloud Ops Dashboard API,
  the live source of costs, inventory, metrics, and idle resources.

The :mod:`agent` module ties retrieval + live data + orchestration into a
single conversational FinOps analyst.
"""

__all__ = ["__version__"]
__version__ = "0.1.0"

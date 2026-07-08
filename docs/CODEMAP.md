# Codemap

A quick orientation map of the agent source tree (`agent/app/`).

## Entry point
- `app/main.py` — FastAPI app, CORS, router registration.
- `app/config.py` — env-driven `Settings` (dashboard, MaaS, embeddings, RAG, orchestrator).

## Orchestrator (`app/orchestrator/`)
- `models.py` — `ModelDef` registry, `TIER_PREFERENCE`, fallback chains, pricing.
- `router.py` — `Orchestrator` wrapping `litellm.Router`: tier resolution, fallback, local pricing, `OrchestrationResult`.
- `cost_tracker.py` — thread-safe `CostTracker` ledger (by day/model/tier) + optional JSONL.

## RAG (`app/rag/`)
- `chunking.py` — `clean_text`, `chunk_text` (overlap), `detect_tipo` (FinOps categories).
- `embeddings.py` — `embed_texts`/`embed_query` over Ollama or MaaS; `health`.
- `store.py` — ChromaDB persistent singleton: `get_collection`, `reset_collection`, `count`.
- `ingest.py` — CLI: read PDF/DOCX/MD/TXT → chunk → embed → upsert. `--dry-run`.
- `retriever.py` — `Retriever.retrieve` / `retrieve_context`; empty-store + embedding-failure safe.

## Tools (`app/tools/`)
- `cloud_ops.py` — async HTTP client for the dashboard API with TTL cache and `finops_snapshot()`.

## Prompts (`app/prompts/`)
- `finops.py` — `SYSTEM_PROMPT` (FinOps persona), `build_user_prompt`, `ANALYZE_INSTRUCTION`.

## Agent (`app/agent/`)
- `finops_agent.py` — `FinOpsAgent.chat` / `.analyze`: gather context → orchestrate → provenance. `_extract_json`.

## Routers (`app/routers/`)
- `health.py` — `/api/health` (dashboard + embeddings + RAG + orchestrator).
- `chat.py` — `/api/agent/chat`.
- `analyze.py` — `/api/agent/analyze`.
- `usage.py` — `/api/orchestrator/usage` (GET/DELETE).

## Data flow
`chat/analyze → FinOpsAgent → (retriever + cloud_ops) → orchestrator → MaaS → CostTracker → response + provenance`.

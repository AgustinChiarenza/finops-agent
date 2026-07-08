# Architecture

The FinOps Agent is a two-layer product fused into one repository:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FinOps Agent (this repo)                     │
│                                                                     │
│  ┌─────────────────────── agent/ ───────────────────────┐           │
│  │  FastAPI  (chat / analyze / usage / health)           │           │
│  │      │                                                │           │
│  │      ▼                                                │           │
│  │  FinOpsAgent ──┬──▶ RAG (Chroma + embeddings)         │           │
│  │                ├──▶ Tools ──HTTP──▶ Dashboard API     │           │
│  │                └──▶ Orchestrator (LiteLLM → MaaS)     │           │
│  │                          │                            │           │
│  │                          └──▶ CostTracker (self-spend)│           │
│  └───────────────────────────────────────────────────────┘           │
│                              │                                      │
│                              │ HTTP /api/*                          │
│                              ▼                                      │
│  ┌─────────────────────── dashboard/ ───────────────────┐           │
│  │  FastAPI backend  ──OBS──▶ Huawei Cloud OBS bucket    │           │
│  │  React frontend   (Vite + Tailwind + Recharts)         │           │
│  └───────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

## Layers

### 1. Dashboard (`dashboard/`) — data & ops layer

The unmodified `cloud-ops-dashboard`. It reads Huawei Cloud operational data
(CTS traces, CloudEye metrics, Cost Center CSV, resource inventory) from an OBS
bucket, aggregates it server-side, and exposes a REST API. It is **read-only**
toward the cloud. This layer is the live source of truth for spend and usage.

### 2. Agent (`agent/`) — reasoning layer

The new FinOps agent. For every user turn it:

1. **Retrieves** FinOps knowledge chunks from a Chroma vector store (RAG).
2. **Pulls** a live FinOps snapshot from the dashboard API (`tools/cloud_ops.py`).
3. **Builds** a prompt with both contexts clearly delimited.
4. **Orchestrates** the LLM call through LiteLLM, which routes to a MaaS model
   based on the requested tier, with fallbacks across models.
5. **Records** the call's token usage and USD cost in a ledger — the agent
   accounts for its own LLM spend (FinOps on FinOps).

### Why two layers?

The dashboard already does excellent deterministic work (anomaly detection,
idle-resource detection, cost aggregation). The agent does not reimplement
that — it calls the dashboard API and reasons *over* its outputs, grounded by
the tenant's FinOps knowledge base. This keeps a clean separation: deterministic
data processing in the dashboard, probabilistic reasoning in the agent, and a
stable HTTP contract between them.

## LiteLLM orchestrator

`agent/app/orchestrator/` wraps `litellm.Router` over a registry of MaaS models
(`models.py`). Each model has a tier (`cheap` / `standard` / `powerful`), a
max-input budget, and per-1M-token prices. `TIER_PREFERENCE` defines, per tier,
the ordered list of models to try — the first is the primary, the rest are the
LiteLLM fallback chain. `Orchestrator.completion()` resolves the tier (with a
token/keyword heuristic for `auto`), calls the router, prices the call locally
(MaaS custom endpoints are not in LiteLLM's price map), and records it in the
`CostTracker`.

## RAG

`agent/app/rag/` mirrors the structure of the `uade-rag` project: ChromaDB
persistent store, Ollama `nomic-embed-text` embeddings (configurable to a MaaS
embedding model), PDF/DOCX/MD/TXT ingest with overlap chunking, and cosine
similarity retrieval. The knowledge directory is shipped **empty**; tenants
ingest their own FinOps material with `python -m app.rag.ingest`. Document
types are classified into FinOps categories (`pricing`, `well_architected`,
`playbook`, `policy`, `case_study`, `best_practice`, `reference`) by filename.

## Data flow for a chat turn

```
POST /api/agent/chat {question}
   │
   ▼
FinOpsAgent.chat
   ├── retriever.retrieve_context(question)   ──▶ Chroma  (knowledge)
   ├── cloud_ops.finops_snapshot()            ──▶ Dashboard API (live)
   └── orchestrator.completion(messages, tier)
          └── litellm.Router ──▶ MaaS (primary, fallbacks)
   │
   ▼
{answer, model, cost_usd, knowledge_sources, dashboard_used}
```

## Failure modes

The agent is designed to degrade gracefully at every boundary:

| Failure | Behaviour |
|---|---|
| Knowledge base empty | Retrieval returns `[]`; the prompt notes the KB is empty and the agent answers from live data only. |
| Embedding backend down | Retrieval returns `[]`; logged as a warning. |
| Dashboard down / one endpoint 5xx | `finops_snapshot` records the failed source as `None`; the agent answers from whatever is available. |
| Primary MaaS model fails | LiteLLM falls through the tier's fallback chain. |
| All MaaS models fail | `OrchestrationError` surfaced to the caller; an unsuccessful attempt is recorded in the ledger. |
| `MAAS_API_KEY` unset | Orchestrator disabled; `/api/health` reports `degraded`; chat/analyze return a clear error. |

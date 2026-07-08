# FinOps Agent

An AI **FinOps agent for Huawei Cloud** that turns operational data into
actionable cost-optimization decisions — grounded in your own FinOps knowledge
base and routed across multiple MaaS models by cost-aware orchestration.

![Python](https://img.shields.io/badge/python-3.12-blue) ![LiteLLM](https://img.shields.io/badge/orchestrator-LiteLLM-green) ![RAG](https://img.shields.io/badge/RAG-ChromaDB-orange) ![License](https://img.shields.io/badge/license-MIT-blue)

## What it is

A sellable FinOps product built from two fused layers:

1. **Cloud Ops Dashboard** (`dashboard/`) — the data & ops layer. Reads Huawei
   Cloud operational data (CTS audit traces, CloudEye metrics, Cost Center CSV,
   resource inventory) from an OBS bucket, aggregates it, and exposes a REST API.
   Deterministic, read-only toward the cloud.
2. **FinOps Agent** (`agent/`) — the reasoning layer. A conversational agent that
   retrieves FinOps knowledge (RAG), pulls live data from the dashboard, and
   reasons over both using an LLM — orchestrated across multiple Huawei Cloud
   MaaS models by **LiteLLM**, with per-call cost tracking so the agent accounts
   for its own model spend.

> The dashboard is the unmodified [`cloud-ops-dashboard`](https://github.com/AgustinChiarenza/cloud-ops-dashboard),
> fused into this repo as the data plane. The agent is the new reasoning plane
> that consumes it.

## Why this combination

- **RAG** grounds recommendations in *your* pricing guides, Well-Architected
  guidance, tagging policies, and past case studies — so the agent doesn't
  hallucinate prices or policies. Structurally the same pattern as `uade-rag`
  (Chroma + Ollama embeddings + overlap chunking), oriented to FinOps knowledge.
- **LiteLLM orchestration** routes each turn to the cheapest model that can
  answer it: a fast `deepseek-v4-flash` for classification, `deepseek-v3` for
  grounded synthesis, `qwen2.5-72b` for deep multi-step analysis — with
  automatic fallbacks when a model is rate-limited or down.
- **Live data** from the dashboard means recommendations reference *your actual
  resources, costs, and idle detections*, not generic advice.
- **Self-spend tracking** — the `/api/orchestrator/usage` ledger reports the
  agent's own LLM cost by model, tier, and day. FinOps on the FinOps agent.

## Repository layout

```
finops-agent/
├── dashboard/              # Cloud Ops Dashboard (data + ops layer, fused in)
│   ├── backend/            # FastAPI — reads OBS, aggregates, serves /api/*
│   └── frontend/           # React SPA (Vite + Tailwind + Recharts)
├── agent/                  # FinOps Agent (reasoning layer)
│   ├── app/
│   │   ├── orchestrator/   # LiteLLM router over MaaS models + cost tracker
│   │   ├── rag/            # Chroma + embeddings + ingest + retriever
│   │   ├── tools/          # async HTTP client for the dashboard API
│   │   ├── prompts/        # FinOps agent persona + structured-analysis prompt
│   │   ├── agent/          # FinOpsAgent: RAG + tools + orchestration
│   │   ├── routers/        # /api/agent/chat, /analyze, /api/orchestrator/usage, /health
│   │   ├── config.py
│   │   └── main.py
│   ├── knowledge/          # EMPTY — drop your FinOps docs here, then ingest
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── docs/                   # ARCHITECTURE, FINOPS_KNOWLEDGE, API
├── scripts/seed_knowledge.sh
├── docker-compose.yml      # dashboard + agent + ollama (definition only)
└── .env.example
```

## Quick start (manual — nothing starts automatically)

```bash
# 1. Configure
cp .env.example agent/.env            # fill MAAS_API_KEY, OBS creds
cp .env.example dashboard/backend/.env

# 2. (Optional) Load FinOps knowledge into the RAG store
cp ~/finops-docs/*.pdf agent/knowledge/
cd agent && python -m app.rag.ingest && cd ..

# 3. Run the stack
docker compose up --build -d
#   dashboard-frontend  → http://localhost:8082
#   dashboard-backend   → http://localhost:8081
#   finops-agent        → http://localhost:8083
#   ollama              → http://localhost:11434  (pull: docker exec finops-ollama ollama pull nomic-embed-text)

# 4. Ask the agent
curl -s localhost:8083/api/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"¿Cómo reduzco mi gasto de ECS este mes?","tier":"auto"}' | jq
```

> The repo ships with an **empty knowledge base** and **no docker started**.
> You ingest your own FinOps documents and start services yourself.

## API (agent)

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Dashboard + embeddings + RAG + orchestrator readiness |
| `POST` | `/api/agent/chat` | Conversational FinOps turn (free-form answer + provenance) |
| `POST` | `/api/agent/analyze` | Structured FinOps analysis (JSON findings + savings estimates) |
| `GET` | `/api/orchestrator/usage` | The agent's own LLM spend ledger |
| `DELETE` | `/api/orchestrator/usage` | Reset the ledger |

See [`docs/API.md`](docs/API.md) for schemas and [`dashboard/README.md`](dashboard/README.md)
for the dashboard's own API surface.

## Configuration

All env-driven (see [`.env.example`](.env.example)). Key knobs:

| Variable | Default | Meaning |
|---|---|---|
| `MAAS_API_KEY` / `MAAS_BASE_URL` | — | Huawei ModelArts Studio credentials (OpenAI-compatible) |
| `DEFAULT_TIER` | `standard` | Routing tier when `tier=auto` doesn't resolve otherwise |
| `EMBED_PROVIDER` | `ollama` | `ollama` (local `nomic-embed-text`) or `maas` |
| `RAG_TOP_K` | `6` | Chunks retrieved per turn |
| `DASHBOARD_API_BASE` | `http://dashboard-backend:8000` | Where the agent finds the dashboard |

## Model routing

Defined in [`agent/app/orchestrator/models.py`](agent/app/orchestrator/models.py).
Replace the placeholder prices with the rates from your MaaS console so the
cost tracker is accurate.

| Tier | Primary | Fallbacks | Use for |
|---|---|---|---|
| `cheap` | `deepseek-v4-flash` | `qwen2.5-7b` → `deepseek-v3` | Classification, short replies |
| `standard` | `deepseek-v3` | `qwen2.5-72b` → `deepseek-v4-flash` | Grounded synthesis (default) |
| `powerful` | `qwen2.5-72b` | `deepseek-v3` → `deepseek-v4-flash` | Deep multi-step analysis |

## Testing

```bash
cd agent && pip install -r requirements-dev.txt && pytest
```

Tests cover chunking/tipo detection, orchestrator tier selection and pricing,
the dashboard client (mocked HTTP, including partial-failure tolerance), and
retriever graceful degradation — all without external services.

## License

MIT — see [LICENSE](LICENSE). The bundled `dashboard/` retains its own MIT notice.

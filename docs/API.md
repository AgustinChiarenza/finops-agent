# FinOps Agent API

Base URL: `http://localhost:8083` (docker compose) or `http://localhost:8001` (direct uvicorn).

## Health

### `GET /api/health`
Aggregate readiness: dashboard connectivity, embedding backend, RAG chunk count,
orchestrator enabled flag.

```json
{
  "status": "ok",
  "dashboard": {"ok": true, "info": {"status": "ok", "obs_connected": true, "maas_enabled": true}},
  "embedding": {"provider": "ollama", "ok": true, "host": "http://ollama:11434"},
  "rag": {"collection": "finops_knowledge", "chunks": 1284},
  "orchestrator": {"enabled": true, "disabled_reason": null, "default_tier": "standard"},
  "maas_enabled": true
}
```

## Agent

### `POST /api/agent/chat`
Conversational FinOps turn. Returns free-form answer plus provenance.

**Request**
```json
{
  "question": "¿Cómo reduzco mi gasto de ECS este mes?",
  "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
  "tier": "auto"
}
```
`tier`: `auto` (default) | `cheap` | `standard` | `powerful`.

**Response**
```json
{
  "answer": "...",
  "model": "finops-deepseek-v3",
  "tier": "standard",
  "cost_usd": 0.00231,
  "latency_ms": 1840.2,
  "knowledge_sources": ["pricing-huawei-ecs-2025.pdf", "finops-playbook-rightsizing.md"],
  "dashboard_used": true,
  "fallback_from": null,
  "structured": null
}
```

### `POST /api/agent/analyze`
Structured FinOps analysis. Returns the same envelope with `structured` populated
as JSON findings (see `prompts/finops.py` for the schema):

```json
{
  "answer": "{...json string...}",
  "structured": {
    "summary": "Resumen ejecutivo del estado FinOps",
    "findings": [
      {
        "severity": "high",
        "title": "ECS sobre-dimensionados en prod",
        "description": "...",
        "affected_resources": ["ecs-xxxx"],
        "evidence": "metrics/idle-resources + pricing-huawei-ecs-2025.pdf",
        "recommendation": "Rightsize a c6.2xlarge",
        "estimated_monthly_savings_usd": 240.0,
        "confidence": 0.82
      }
    ],
    "estimated_total_monthly_savings_usd": 240.0,
    "risks": ["..."],
    "knowledge_sources": ["pricing-huawei-ecs-2025.pdf"]
  },
  "model": "finops-qwen72b",
  "tier": "powerful",
  "cost_usd": 0.0118,
  "knowledge_sources": ["pricing-huawei-ecs-2025.pdf"],
  "dashboard_used": true
}
```

## Orchestrator usage (self-spend)

### `GET /api/orchestrator/usage`
The agent's own LLM spend ledger — FinOps applied to the FinOps agent.

```json
{
  "total": {"calls": 42, "successes": 41, "input_tokens": 510000, "output_tokens": 88000, "cost_usd": 0.41},
  "by_tier": {
    "cheap":    {"calls": 20, "cost_usd": 0.03, ...},
    "standard": {"calls": 18, "cost_usd": 0.28, ...},
    "powerful": {"calls": 4,  "cost_usd": 0.10, ...}
  },
  "by_day_model": {"2026-07-08": {"finops-deepseek-v3": {"calls": 12, "cost_usd": 0.18, ...}}},
  "recent": [{"timestamp": "...", "alias": "finops-deepseek-v3", "tier": "standard", "cost_usd": 0.002, "fallback_from": null, ...}]
}
```

### `DELETE /api/orchestrator/usage`
Reset the in-memory ledger.

## Underlying dashboard API

The dashboard exposes its own API under `/api/*` (inventory, cts, costs, metrics,
insights). See `dashboard/README.md` for the full surface. The agent consumes it
via `tools/cloud_ops.py`; you can also hit it directly at `http://localhost:8081`.

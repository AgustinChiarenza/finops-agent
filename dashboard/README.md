# Cloud Ops Dashboard

Interactive dashboard for Huawei Cloud operations data — CTS audit traces, CloudEye metrics, Cost Center usage, and resource inventory — with AI-powered insights via MaaS.

![Docker](https://img.shields.io/badge/docker-ready-blue) ![Python](https://img.shields.io/badge/python-3.12-blue) ![React](https://img.shields.io/badge/react-18-blue)

## Overview

Cloud Ops Dashboard is a read-only operations console for Huawei Cloud environments. It pulls four operational data sources from an OBS bucket, processes them into summaries/timeseries/anomalies, and presents them through an interactive web UI — with an optional AI analyst layer (ModelArts MaaS) that turns the raw data into narrative security, cost, and operational findings.

**What it does, end to end:**

1. **Reads** cloud ops data already exported to an OBS bucket (CTS traces, CloudEye metrics, Cost Center CSV, resource inventory JSON).
2. **Processes** it server-side: aggregates costs by day/service/owner, computes cost anomalies (7-day rolling mean + 2σ), detects idle resources (low CPU + low network), classifies CTS security events by severity, and builds inventory summaries.
3. **Serves** a REST API (FastAPI) with filtering, pagination, and an in-memory TTL cache so repeated views are fast.
4. **Visualizes** it in a React SPA (Vite + Tailwind + Recharts) with six surfaces: Dashboard, Inventory, CTS Audit, Costs, Metrics, and AI Insights.
5. **Optionally analyzes** the whole dataset with an LLM (MaaS) to produce structured JSON findings with severity, affected resources, recommendations, and risk scores — kept in an in-memory history.

### Key features

- 📊 **Dashboard** — KPI cards (total resources, est. monthly cost, idle count, cost trend %) + breakdowns by service.
- 🗂️ **Inventory** — paginated, filterable resource list (ECS, RDS, ELB, EVS, NAT, VPC) with owner/environment/status filters.
- 🛡️ **CTS Audit** — Cloud Trace Service traces with summary by user/service/hour, failed/delete counts, and a security-events feed (failed auth → high, IAM/policy changes → critical, deletes → medium, external-IP access → low).
- 💰 **Costs** — daily cost trend, cost by service & owner (with %), anomaly detection, and a 7-day linear-regression trend direction.
- 📈 **Metrics** — CloudEye timeseries per resource/metric with avg/min/max/p95 summaries, plus idle-resource detection with estimated savings.
- 🧠 **AI Insights** — on-demand security / cost / operational / comprehensive analyses via MaaS, returned as structured findings. Gracefully disables when `MAAS_API_KEY` is unset.
- 🔎 **Idle-resource detection** — flags resources with avg CPU < threshold AND avg network < threshold, joined with inventory cost data to estimate savings.
- ⚡ **TTL cache** — in-memory cache (default 300s) on every processor to avoid re-reading OBS on each request.
- 🐳 **One-command deploy** — `docker compose up --build -d` builds both services with a reproducible frontend build (`npm ci`) and an nginx reverse proxy with gzip + security headers.

### Architecture

```
Browser ──HTTP──▶ nginx (frontend container, :8082)
                     │  /api/* proxied to backend
                     ▼
                 FastAPI (backend container, :8081)
                     │
                     ├── routers/   (REST endpoints)
                     ├── processors/ (aggregation, anomalies, idle detection)
                     ├── prompts/    (LLM prompt templates)
                     └── obs_client  ──OBS SDK──▶ Huawei Cloud OBS bucket
```

The backend never writes to your cloud — it only **reads** from OBS. The `scripts/export_inventory.py` helper is the one that calls Huawei Cloud APIs (ECS/RDS/ELB/EVS/NAT/VPC SDKs) to produce the inventory JSON and optionally upload it to OBS.

### API surface

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | Liveness + OBS connectivity + MaaS enabled flag |
| GET | `/api/inventory` | Paginated/filterable resource list |
| GET | `/api/inventory/summary` | Counts & cost by service/status/env/owner |
| GET | `/api/cts/traces` | Paginated CTS traces with filters |
| GET | `/api/cts/summary` | Actions by user/service/hour, failed/delete counts |
| GET | `/api/cts/security-events` | Classified security events by severity |
| GET | `/api/costs/daily` · `/by-service` · `/by-owner` · `/summary` · `/anomalies` | Cost aggregations & anomaly detection |
| GET | `/api/metrics/timeseries` · `/summary` · `/idle-resources` | CloudEye metrics + idle detection |
| POST | `/api/insights/security` · `/cost` · `/operational` · `/comprehensive` | AI analyses via MaaS |
| GET | `/api/insights/history` | Recent insight summaries (in-memory) |

### Tech stack

- **Backend:** Python 3.12, FastAPI, Pydantic v2, httpx, esdk-obs-python (Huawei OBS SDK). Settings via `pydantic-settings`.
- **Frontend:** React 18, Vite 6, TypeScript, Tailwind CSS 3, Recharts, TanStack Query, React Router, lucide-react.
- **Infra:** Docker + Docker Compose, nginx (reverse proxy + static host), reproducible builds via lockfile + `npm ci`.
- **AI:** Huawei ModelArts MaaS (OpenAI-compatible `/chat/completions` endpoint).

## Quick Start

```bash
# 1. Clone
git clone <repo-url> cloud-ops-dashboard
cd cloud-ops-dashboard

# 2. Configure credentials
cp .env.example backend/.env
# Edit backend/.env with your Huawei Cloud OBS credentials

# 3. Launch
docker compose up --build -d

# 4. Open in browser
# Frontend → http://localhost:8082
# API     → http://localhost:8081/api/health
```

## Prerequisites

- **Docker** + **Docker Compose** (v2)
- A **Huawei Cloud OBS bucket** with data in the expected format (see [docs/DATA_FORMAT.md](docs/DATA_FORMAT.md))

## Configuration

All configuration lives in `backend/.env`. Start from the template:

```bash
cp .env.example backend/.env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `OBS_AK` | ✅ | Huawei Cloud Access Key ID |
| `OBS_SK` | ✅ | Huawei Cloud Secret Access Key |
| `OBS_REGION` | ✅ | OBS bucket region (e.g. `la-south-2`) |
| `OBS_BUCKET` | ✅ | OBS bucket name |
| `OBS_PREFIX` | ✅ | Path prefix inside the bucket |
| `MAAS_API_KEY` | ❌ | MaaS API key for AI insights (disabled if empty) |
| `MAAS_MODEL` | ❌ | MaaS model name (default: `deepseek-v4-flash`) |
| `MAAS_BASE_URL` | ❌ | MaaS base URL |
| `CACHE_TTL_SECONDS` | ❌ | Cache TTL in seconds (default: `300`) |
| `LOG_LEVEL` | ❌ | Log level (default: `INFO`) |
| `CORS_ORIGINS` | ❌ | Comma-separated allowed origins |

## Ports

| Service | Internal | Exposed | URL |
|---------|----------|---------|-----|
| Frontend (Nginx) | 80 | **8082** | `http://localhost:8082` |
| Backend (FastAPI) | 8000 | **8081** | `http://localhost:8081` |

The frontend Nginx proxies all `/api/` requests to the backend automatically.

## Project Structure

```
cloud-ops-dashboard/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── main.py           # App entrypoint
│   │   ├── config.py         # Settings (pydantic-settings)
│   │   ├── obs_client.py     # OBS data reader
│   │   ├── maas_client.py    # MaaS AI client
│   │   ├── cache.py          # In-memory cache
│   │   ├── routers/          # API endpoints
│   │   ├── processors/       # Data processing logic
│   │   ├── prompts/          # AI prompt templates
│   │   └── schemas/          # Pydantic models
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React + Vite + Tailwind
│   ├── src/
│   │   ├── api/              # API client
│   │   ├── components/       # UI components
│   │   ├── hooks/            # React Query hooks
│   │   ├── pages/            # Route pages
│   │   └── types/            # TypeScript types
│   ├── nginx.conf            # Production reverse proxy
│   ├── Dockerfile
│   └── package.json
├── scripts/                  # Utility scripts
│   └── export_inventory.py   # Export HW Cloud inventory to OBS
├── docs/
│   └── DATA_FORMAT.md        # OBS data format specification
├── docker-compose.yml
├── .env.example              # Configuration template
└── README.md
```

## Data Format

The dashboard reads all data from your OBS bucket. See [docs/DATA_FORMAT.md](docs/DATA_FORMAT.md) for the exact file structure and formats required:

- **CTS Traces** — `CTS/traces_*.json` or `.jsonl.gz`
- **CloudEye Metrics** — `Metrics/CloudEye/cloudeye_metrics.jsonl.gz`
- **Cost Center** — `Costs/CostCenter/cost_usage.csv`
- **Resource Inventory** — `Inventory/resource_inventory.json`

## Exporting Data from Huawei Cloud

Use the included script to export your resource inventory:

```bash
pip install huaweicloudsdkecs huaweicloudsdkrds huaweicloudsdkelb huaweicloudsdkevs huaweicloudsdknat huaweicloudsdkvpc esdk-obs-python
python scripts/export_inventory.py --region la-south-2 --upload
```

## Development

### Backend (local, no Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8081
```

### Frontend (local, no Docker)

```bash
cd frontend
npm install
npm run dev          # Vite dev server on :5173, proxies /api to :8081
```

## Testing

Backend unit tests (pure functions: cache, JSON extraction, cost filtering, insights-disable path):

```bash
cd backend
pip install -r requirements-dev.txt
pytest                  # 15 tests, no OBS connection required
```

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Dashboard empty | Verify OBS bucket has data in the correct structure |
| OBS connection error | Check `OBS_AK`, `OBS_SK`, `OBS_REGION`, `OBS_BUCKET` in `backend/.env` |
| AI insights not working | Verify `MAAS_API_KEY` is set in `backend/.env` |
| Backend won't start | `docker compose logs backend` |

## License

MIT — see [LICENSE](LICENSE).

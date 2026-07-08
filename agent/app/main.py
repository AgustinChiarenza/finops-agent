import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, chat, analyze, usage

logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))

app = FastAPI(
    title="FinOps Agent API",
    description=(
        "Conversational FinOps agent for Huawei Cloud: RAG over a FinOps knowledge "
        "base + live Cloud Ops Dashboard data, orchestrated across multiple MaaS "
        "models via LiteLLM with per-call cost tracking."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api/agent", tags=["agent"])
app.include_router(analyze.router, prefix="/api/agent", tags=["agent"])
app.include_router(usage.router, prefix="/api/orchestrator", tags=["orchestrator"])

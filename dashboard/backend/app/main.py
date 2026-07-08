import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import cts, costs, metrics, inventory, insights, health

logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))

app = FastAPI(
    title="Cloud Ops Dashboard API",
    description="Reads Huawei Cloud OBS data (CTS, Cost Center, Cloud Eye) and generates interactive reports with AI insights",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(cts.router, prefix="/api/cts", tags=["cts"])
app.include_router(costs.router, prefix="/api/costs", tags=["costs"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])

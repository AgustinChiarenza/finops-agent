from fastapi import APIRouter

from app.config import settings
from app.orchestrator import orchestrator
from app.rag import embeddings, store
from app.tools import cloud_ops

router = APIRouter()


@router.get("/health")
async def health_check():
    """Aggregate readiness: dashboard, embedding backend, RAG store, orchestrator."""
    dashboard = await _dashboard_health()
    embedding = await embeddings.health()
    return {
        "status": "ok" if (dashboard["ok"] and orchestrator.enabled) else "degraded",
        "dashboard": dashboard,
        "embedding": embedding,
        "rag": {"collection": settings.chroma_collection, "chunks": store.count()},
        "orchestrator": {
            "enabled": orchestrator.enabled,
            "disabled_reason": orchestrator.disabled_reason,
            "default_tier": settings.default_tier,
        },
        "maas_enabled": settings.maas_enabled,
    }


async def _dashboard_health() -> dict:
    try:
        return {"ok": True, "info": await cloud_ops.health()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

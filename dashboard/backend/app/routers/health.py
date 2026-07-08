import logging

from fastapi import APIRouter

from app.config import settings
from app.obs_client import obs_reader

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    obs_ok, obs_error = obs_reader.is_reachable()
    if not obs_ok:
        logger.warning("OBS health check failed: %s", obs_error)

    return {
        "status": "ok" if obs_ok else "degraded",
        "obs_connected": obs_ok,
        "obs_error": obs_error or None,
        "maas_enabled": settings.maas_enabled,
    }

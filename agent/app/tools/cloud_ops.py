"""Async HTTP client for the bundled Cloud Ops Dashboard API.

The dashboard backend (in ``dashboard/backend``) is the live source of FinOps
data: costs, inventory, CloudEye metrics, CTS audit traces, idle-resource
detection, and anomaly detection. This client wraps the endpoints the agent
actually pulls when answering a cost question, with a small in-memory TTL cache
so a multi-turn conversation doesn't re-fetch the same summary on every turn.

All calls return parsed JSON (dict/list) and raise :class:`DashboardError` on
non-2xx responses so the agent can degrade gracefully.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class DashboardError(RuntimeError):
    pass


class CloudOpsClient:
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base_url = (base_url or settings.dashboard_api_base).rstrip("/")
        self.timeout = timeout or settings.dashboard_timeout_seconds
        self._cache: dict[str, tuple[float, Any]] = {}
        self._ttl = settings.dashboard_timeout_seconds  # reuse as a short cache TTL

    # --- internals ---
    async def _get(self, path: str, params: dict | None = None, cache: bool = True) -> Any:
        cache_key = f"{path}:{sorted((params or {}).items())}"
        if cache:
            entry = self._cache.get(cache_key)
            if entry and time.time() < entry[0]:
                return entry[1]
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params)
        except httpx.HTTPError as exc:
            raise DashboardError(f"dashboard unreachable at {url}: {exc}") from exc
        if resp.status_code >= 400:
            raise DashboardError(f"dashboard {resp.status_code} at {path}: {resp.text[:200]}")
        data = resp.json()
        if cache:
            self._cache[cache_key] = (time.time() + self._ttl, data)
        return data

    async def health(self) -> dict:
        return await self._get("/api/health", cache=False)

    # --- cost ---
    async def cost_summary(self) -> dict:
        return await self._get("/api/costs/summary")

    async def costs_by_service(self) -> list[dict]:
        return await self._get("/api/costs/by-service")

    async def costs_by_owner(self) -> list[dict]:
        return await self._get("/api/costs/by-owner")

    async def daily_costs(self) -> list[dict]:
        return await self._get("/api/costs/daily")

    async def cost_anomalies(self) -> list[dict]:
        return await self._get("/api/costs/anomalies")

    # --- inventory ---
    async def inventory_summary(self) -> dict:
        return await self._get("/api/inventory/summary")

    async def inventory(self, page: int = 1, page_size: int = 100) -> dict:
        return await self._get("/api/inventory", params={"page": page, "page_size": page_size})

    # --- metrics / idle ---
    async def metrics_summary(self) -> Any:
        return await self._get("/api/metrics/summary")

    async def idle_resources(self) -> list[dict]:
        return await self._get("/api/metrics/idle-resources")

    # --- CTS / security ---
    async def cts_summary(self) -> dict:
        return await self._get("/api/cts/summary")

    async def security_events(self) -> list[dict]:
        return await self._get("/api/cts/security-events")

    # --- convenience: the bundle the agent usually wants ---
    async def finops_snapshot(self) -> dict:
        """Pull the compact dataset a FinOps turn typically needs.

        Each member is fetched best-effort: a dashboard failure for one source
        is recorded as ``None`` rather than aborting the whole snapshot, so the
        agent can still answer from whatever is available.
        """
        calls = {
            "cost_summary": self.cost_summary,
            "costs_by_service": self.costs_by_service,
            "cost_anomalies": self.cost_anomalies,
            "inventory_summary": self.inventory_summary,
            "idle_resources": self.idle_resources,
            "cts_summary": self.cts_summary,
        }
        snapshot: dict[str, Any] = {}
        for name, fn in calls.items():
            try:
                snapshot[name] = await fn()
            except DashboardError as exc:
                logger.warning("finops_snapshot: %s unavailable: %s", name, exc)
                snapshot[name] = None
        return snapshot


cloud_ops = CloudOpsClient()

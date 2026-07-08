"""Tests for the Cloud Ops dashboard client with mocked HTTP (respx)."""

import httpx
import pytest
import respx

from app.tools.cloud_ops import CloudOpsClient, DashboardError


@pytest.mark.asyncio
async def test_cost_summary_returns_json_and_caches():
    client = CloudOpsClient(base_url="http://dash.test", timeout=5)
    with respx.mock(base_url="http://dash.test") as mock:
        mock.get("/api/costs/summary").respond(json={"total_cost": 123.4})
        first = await client.cost_summary()
        second = await client.cost_summary()  # should hit cache, no second HTTP call
        assert first == second == {"total_cost": 123.4}
        assert mock["/api/costs/summary"].call_count == 1


@pytest.mark.asyncio
async def test_dashboard_error_on_4xx():
    client = CloudOpsClient(base_url="http://dash.test", timeout=5)
    with respx.mock(base_url="http://dash.test") as mock:
        mock.get("/api/costs/summary").respond(status_code=503, text="upstream down")
        with pytest.raises(DashboardError):
            await client.cost_summary()


@pytest.mark.asyncio
async def test_finops_snapshot_tolerates_partial_failure():
    client = CloudOpsClient(base_url="http://dash.test", timeout=5)
    with respx.mock(base_url="http://dash.test") as mock:
        mock.get("/api/costs/summary").respond(json={"total_cost": 10.0})
        mock.get("/api/costs/by-service").respond(status_code=500, text="x")
        mock.get("/api/costs/anomalies").respond(json=[])
        mock.get("/api/inventory/summary").respond(json={"total": 1})
        mock.get("/api/metrics/idle-resources").respond(json=[])
        mock.get("/api/cts/summary").respond(json={"total": 0})
        snap = await client.finops_snapshot()
        assert snap["cost_summary"] == {"total_cost": 10.0}
        assert snap["costs_by_service"] is None  # failed source → None, not abort
        assert snap["inventory_summary"] == {"total": 1}

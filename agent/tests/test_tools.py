"""Tests for the Cloud Ops dashboard client with httpx.MockTransport (no respx)."""

import json

import httpx
import pytest

from app.tools.cloud_ops import CloudOpsClient, DashboardError

BASE = "http://dash.test"


def _transport(routes: dict[str, tuple[int, object]]) -> httpx.MockTransport:
    """routes: {path: (status, json_body_or_None)} → MockTransport handler."""
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path in routes:
            status, body = routes[path]
            if body is None:
                return httpx.Response(status, text="error")
            return httpx.Response(status, json=body)
        return httpx.Response(404, text=f"no route for {path}")

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_cost_summary_returns_json_and_caches():
    transport = _transport({"/api/costs/summary": (200, {"total_cost": 123.4})})
    client = CloudOpsClient(base_url=BASE, timeout=5, transport=transport)
    first = await client.cost_summary()
    second = await client.cost_summary()  # cache hit → no second HTTP call
    assert first == second == {"total_cost": 123.4}
    # Only one request should have hit the transport (verify via a counter).
    calls = {"n": 0}

    def counting_handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"total_cost": 123.4})

    client2 = CloudOpsClient(base_url=BASE, timeout=5, transport=httpx.MockTransport(counting_handler))
    await client2.cost_summary()
    await client2.cost_summary()
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_dashboard_error_on_4xx():
    transport = _transport({"/api/costs/summary": (503, None)})
    client = CloudOpsClient(base_url=BASE, timeout=5, transport=transport)
    with pytest.raises(DashboardError):
        await client.cost_summary()


@pytest.mark.asyncio
async def test_finops_snapshot_tolerates_partial_failure():
    transport = _transport({
        "/api/costs/summary": (200, {"total_cost": 10.0}),
        "/api/costs/by-service": (500, None),  # failed source
        "/api/costs/anomalies": (200, []),
        "/api/inventory/summary": (200, {"total": 1}),
        "/api/metrics/idle-resources": (200, []),
        "/api/cts/summary": (200, {"total": 0}),
    })
    client = CloudOpsClient(base_url=BASE, timeout=5, transport=transport)
    snap = await client.finops_snapshot()
    assert snap["cost_summary"] == {"total_cost": 10.0}
    assert snap["costs_by_service"] is None  # failed source → None, not abort
    assert snap["inventory_summary"] == {"total": 1}


def test_transport_type_hint_accepts_none():
    # Default construction (no transport) must still work — hits real network only on call.
    client = CloudOpsClient(base_url=BASE, timeout=5)
    assert client._transport is None

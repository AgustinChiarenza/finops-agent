import logging
from collections import defaultdict
from datetime import date, datetime, timedelta

from app.cache import cache
from app.obs_client import obs_reader
from app.schemas.costs import (
    CostAnomaly,
    CostByOwner,
    CostByService,
    CostSummary,
    DailyCostPoint,
)

logger = logging.getLogger(__name__)

OBS_PATH = "Costs/CostCenter/cost_usage.csv"


def _parse_row(raw: dict) -> dict:
    return {
        "period": raw.get("date", raw.get("period", "")),
        "service_type": raw.get("service_type", ""),
        "owner": raw.get("owner", ""),
        "environment": raw.get("environment", ""),
        "resource_id": raw.get("resource_id", ""),
        "resource_name": raw.get("resource_name", ""),
        "billing_mode": raw.get("billing_mode", ""),
        "cost": float(raw.get("daily_cost_usd", raw.get("cost", 0))),
        "usage_amount": float(raw.get("usage_amount", 0)),
    }


async def _get_all_costs() -> list[dict]:
    cache_key = "costs:all"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    rows = obs_reader.get_object_as_csv(OBS_PATH)
    parsed = [_parse_row(r) for r in rows]
    cache.set(cache_key, parsed)
    return parsed


def _filter_costs(
    data: list[dict],
    start_date: date | None = None,
    end_date: date | None = None,
    service_type: str | None = None,
    owner: str | None = None,
    environment: str | None = None,
    billing_mode: str | None = None,
) -> list[dict]:
    filtered = data
    if start_date:
        sd = start_date.isoformat()
        filtered = [r for r in filtered if r["period"] >= sd]
    if end_date:
        ed = end_date.isoformat()
        filtered = [r for r in filtered if r["period"] <= ed]
    if service_type:
        filtered = [r for r in filtered if r["service_type"] == service_type]
    if owner:
        filtered = [r for r in filtered if r["owner"] == owner]
    if environment:
        filtered = [r for r in filtered if r["environment"] == environment]
    if billing_mode:
        filtered = [r for r in filtered if r["billing_mode"] == billing_mode]
    return filtered


async def get_daily_costs(
    start_date: date | None = None,
    end_date: date | None = None,
    service_type: str | None = None,
    owner: str | None = None,
    environment: str | None = None,
) -> list[dict]:
    data = await _get_all_costs()
    filtered = _filter_costs(data, start_date, end_date, service_type, owner, environment)

    daily: dict[str, float] = defaultdict(float)
    for r in filtered:
        daily[r["period"]] += r["cost"]

    return [
        DailyCostPoint(date=d, cost=round(c, 2)).model_dump()
        for d, c in sorted(daily.items())
    ]


async def get_costs_by_service(
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    data = await _get_all_costs()
    filtered = _filter_costs(data, start_date, end_date)

    by_service: dict[str, float] = defaultdict(float)
    for r in filtered:
        by_service[r["service_type"]] += r["cost"]

    total = sum(by_service.values()) or 1
    return [
        CostByService(
            service_type=s, total_cost=round(c, 2), percentage=round(c / total * 100, 1),
        ).model_dump()
        for s, c in sorted(by_service.items(), key=lambda x: -x[1])
    ]


async def get_costs_by_owner(
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    data = await _get_all_costs()
    filtered = _filter_costs(data, start_date, end_date)

    by_owner: dict[str, float] = defaultdict(float)
    for r in filtered:
        by_owner[r["owner"]] += r["cost"]

    total = sum(by_owner.values()) or 1
    return [
        CostByOwner(
            owner=o, total_cost=round(c, 2), percentage=round(c / total * 100, 1),
        ).model_dump()
        for o, c in sorted(by_owner.items(), key=lambda x: -x[1])
    ]


async def get_cost_anomalies(
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    data = await _get_all_costs()
    filtered = _filter_costs(data, start_date, end_date)

    daily: dict[str, float] = defaultdict(float)
    for r in filtered:
        daily[r["period"]] += r["cost"]

    sorted_days = sorted(daily.items())
    if len(sorted_days) < 7:
        return []

    anomalies = []
    window = 7
    for i in range(window, len(sorted_days)):
        recent = [sorted_days[j][1] for j in range(i - window, i)]
        mean = sum(recent) / window
        variance = sum((x - mean) ** 2 for x in recent) / window
        sigma = variance ** 0.5
        threshold = mean + 2 * sigma

        day, cost = sorted_days[i]
        if cost > threshold and sigma > 0:
            anomalies.append(CostAnomaly(
                date=day,
                actual_cost=round(cost, 2),
                expected_cost=round(mean, 2),
                deviation_pct=round((cost - mean) / mean * 100, 1) if mean else 0,
            ).model_dump())

    return anomalies


async def get_cost_summary(
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    data = await _get_all_costs()
    filtered = _filter_costs(data, start_date, end_date)

    daily: dict[str, float] = defaultdict(float)
    for r in filtered:
        daily[r["period"]] += r["cost"]

    sorted_days = sorted(daily.items())
    if not sorted_days:
        return CostSummary(
            total_cost=0, average_daily=0, trend_direction="flat", trend_pct=0, anomaly_count=0,
        ).model_dump()

    total = sum(v for _, v in sorted_days)
    avg = total / len(sorted_days)

    # Trend: linear regression on last 7 days
    recent = sorted_days[-7:]
    n = len(recent)
    if n >= 2:
        xs = list(range(n))
        ys = [v for _, v in recent]
        x_mean = (n - 1) / 2
        y_mean = sum(ys) / n
        slope_num = sum((xs[i] - x_mean) * (ys[i] - y_mean) for i in range(n))
        slope_den = sum((xs[i] - x_mean) ** 2 for i in range(n))
        slope = slope_num / slope_den if slope_den else 0
        trend_pct = round(slope / y_mean * 100, 1) if y_mean else 0
        trend_direction = "up" if trend_pct > 2 else "down" if trend_pct < -2 else "flat"
    else:
        trend_pct = 0
        trend_direction = "flat"

    anomalies = await get_cost_anomalies(start_date, end_date)

    return CostSummary(
        total_cost=round(total, 2),
        average_daily=round(avg, 2),
        trend_direction=trend_direction,
        trend_pct=trend_pct,
        anomaly_count=len(anomalies),
    ).model_dump()

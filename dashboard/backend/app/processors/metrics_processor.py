import logging
from collections import defaultdict
from datetime import date

from app.cache import cache
from app.obs_client import obs_reader
from app.schemas.metrics import IdleResource, MetricDatapoint, MetricSummaryItem, MetricTimeseries

logger = logging.getLogger(__name__)

OBS_PATH = "Metrics/CloudEye/cloudeye_metrics.jsonl.gz"


async def _stream_metrics(
    resource_id: str | None = None,
    metric_name: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    """Stream all matching metric records from OBS and return as list."""
    cache_key = f"metrics:raw:{resource_id or 'all'}:{metric_name or 'all'}:{start_date}:{end_date}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    records = []
    async for record in obs_reader.stream_jsonl_gz(OBS_PATH):
        rid = record.get("resource_id", "")
        mname = record.get("metric_name", "")
        ts = record.get("timestamp", "")

        if resource_id and rid != resource_id:
            continue
        if metric_name and mname != metric_name:
            continue
        if start_date and ts < start_date.isoformat():
            continue
        if end_date and ts > end_date.isoformat() + "T23:59:59":
            continue

        records.append(record)

    cache.set(cache_key, records)
    return records


def _group_by_resource_metric(records: list[dict]) -> dict[str, dict[str, list[tuple[str, float]]]]:
    """Group records into {resource_id: {metric_name: [(timestamp, value)]}}."""
    acc: dict[str, dict[str, list[tuple[str, float]]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        rid = r["resource_id"]
        mname = r["metric_name"]
        ts = r.get("timestamp", "")
        val = float(r.get("value", 0))
        acc[rid][mname].append((ts, val))
    return acc


async def get_timeseries(
    resource_id: str,
    metric_name: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    records = await _stream_metrics(resource_id, metric_name, start_date, end_date)
    grouped = _group_by_resource_metric(records)

    if resource_id not in grouped:
        return []

    results = []
    for mname, points in grouped[resource_id].items():
        datapoints = [
            MetricDatapoint(timestamp=ts, value=round(val, 2)).model_dump()
            for ts, val in sorted(points)
        ]
        # Get resource_name and unit from the first matching record
        rname = resource_id
        unit = ""
        for r in records:
            if r.get("resource_id") == resource_id and r.get("metric_name") == mname:
                rname = r.get("resource_name", resource_id)
                unit = r.get("unit", "")
                break
        results.append(MetricTimeseries(
            resource_id=resource_id,
            resource_name=rname,
            metric_name=mname,
            unit=unit,
            datapoints=datapoints,
        ).model_dump())

    return results


async def get_metrics_summary(
    resource_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    records = await _stream_metrics(resource_id, None, start_date, end_date)
    grouped = _group_by_resource_metric(records)

    results = []
    for rid, metrics in grouped.items():
        for mname, points in metrics.items():
            values = [v for _, v in points]
            if not values:
                continue
            values_sorted = sorted(values)
            n = len(values_sorted)
            p95_idx = min(int(n * 0.95), n - 1)
            # Get resource_name from records
            rname = rid
            unit = ""
            for r in records:
                if r.get("resource_id") == rid and r.get("metric_name") == mname:
                    rname = r.get("resource_name", rid)
                    unit = r.get("unit", "")
                    break
            results.append(MetricSummaryItem(
                resource_id=rid,
                resource_name=rname,
                metric_name=mname,
                avg=round(sum(values) / n, 2),
                max=round(max(values), 2),
                min=round(min(values), 2),
                p95=round(values_sorted[p95_idx], 2),
                unit=unit,
            ).model_dump())

    return results


async def get_idle_resources(
    cpu_threshold: float = 5.0,
    network_threshold: float = 1.0,
) -> list[dict]:
    cache_key = "metrics:idle"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Get inventory for cost data (fetch ALL resources, not just the first page)
    from app.processors.inventory_processor import get_inventory
    inv_data = await get_inventory(page_size=100000)
    inv_by_id = {r["resource_id"]: r for r in inv_data["items"]}

    # Stream all metrics
    records = await _stream_metrics()
    grouped = _group_by_resource_metric(records)

    idle = []
    for rid, metrics in grouped.items():
        avgs: dict[str, float] = {}
        for mname, points in metrics.items():
            values = [v for _, v in points]
            if values:
                avgs[mname] = sum(values) / len(values)

        cpu = avgs.get("cpu_util", avgs.get("cpu_utilization", avgs.get("CPUUtilization", 100)))
        net_in = avgs.get("network_in_mbps", avgs.get("network_in_bytes", avgs.get("NetworkIn", 0)))
        net_out = avgs.get("network_out_mbps", avgs.get("network_out_bytes", avgs.get("NetworkOut", 0)))
        total_net = net_in + net_out

        is_idle = cpu < cpu_threshold and total_net < network_threshold
        if is_idle:
            inv = inv_by_id.get(rid, {})
            idle.append(IdleResource(
                resource_id=rid,
                resource_name=inv.get("resource_name", rid),
                service_type=inv.get("service_type", ""),
                monthly_cost=inv.get("monthly_cost", 0),
                avg_cpu=round(cpu, 2),
                avg_network_in=round(net_in, 2),
                avg_network_out=round(net_out, 2),
                reason=f"CPU avg {cpu:.1f}% < {cpu_threshold}%, network avg {total_net:.1f} < {network_threshold}",
            ).model_dump())

    cache.set(cache_key, idle)
    return idle

from datetime import date

from fastapi import APIRouter, Query

from app.processors.metrics_processor import get_idle_resources, get_metrics_summary, get_timeseries

router = APIRouter()


@router.get("/timeseries")
async def timeseries(
    resource_id: str = Query(...),
    metric_name: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return await get_timeseries(resource_id, metric_name, start_date, end_date)


@router.get("/summary")
async def metrics_summary(
    resource_id: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return await get_metrics_summary(resource_id, start_date, end_date)


@router.get("/idle-resources")
async def idle_resources(
    cpu_threshold: float = Query(5.0),
    network_threshold: float = Query(100.0),
):
    return await get_idle_resources(cpu_threshold, network_threshold)

from datetime import date

from fastapi import APIRouter, Query

from app.processors.cost_processor import (
    get_cost_anomalies,
    get_cost_summary,
    get_costs_by_owner,
    get_costs_by_service,
    get_daily_costs,
)

router = APIRouter()


@router.get("/daily")
async def daily_costs(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    service_type: str | None = Query(None),
    owner: str | None = Query(None),
    environment: str | None = Query(None),
):
    return await get_daily_costs(start_date, end_date, service_type, owner, environment)


@router.get("/by-service")
async def costs_by_service(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return await get_costs_by_service(start_date, end_date)


@router.get("/by-owner")
async def costs_by_owner(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return await get_costs_by_owner(start_date, end_date)


@router.get("/anomalies")
async def cost_anomalies(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return await get_cost_anomalies(start_date, end_date)


@router.get("/summary")
async def cost_summary(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    return await get_cost_summary(start_date, end_date)

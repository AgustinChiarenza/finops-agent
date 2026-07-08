from datetime import date

from fastapi import APIRouter, Query

from app.processors.cts_processor import get_cts_summary, get_security_events, get_traces

router = APIRouter()


@router.get("/traces")
async def list_traces(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    user: str | None = Query(None),
    resource_type: str | None = Query(None),
    api_name: str | None = Query(None),
    severity: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    return await get_traces(start_date, end_date, user, resource_type, api_name, severity, page, page_size)


@router.get("/summary")
async def cts_summary():
    return await get_cts_summary()


@router.get("/security-events")
async def security_events():
    return await get_security_events()

from datetime import date

from fastapi import APIRouter, Query

from app.processors.inventory_processor import get_inventory, get_inventory_summary

router = APIRouter()


@router.get("")
async def list_inventory(
    service_type: str | None = Query(None),
    environment: str | None = Query(None),
    owner: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    return await get_inventory(service_type, environment, owner, status, page, page_size)


@router.get("/summary")
async def inventory_summary():
    return await get_inventory_summary()

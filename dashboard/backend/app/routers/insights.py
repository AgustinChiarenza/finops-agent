from fastapi import APIRouter

from app.processors.insights_processor import (
    analyze_comprehensive,
    analyze_cost,
    analyze_operational,
    analyze_security,
    get_insights_history,
)

router = APIRouter()


@router.post("/security")
async def security_insight():
    return await analyze_security()


@router.post("/cost")
async def cost_insight():
    return await analyze_cost()


@router.post("/operational")
async def operational_insight():
    return await analyze_operational()


@router.post("/comprehensive")
async def comprehensive_insight():
    return await analyze_comprehensive()


@router.get("/history")
async def insights_history():
    return await get_insights_history()

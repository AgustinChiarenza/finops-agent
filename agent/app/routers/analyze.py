from fastapi import APIRouter
from pydantic import BaseModel

from app.agent import finops_agent

router = APIRouter()


class AnalyzeRequest(BaseModel):
    question: str
    tier: str = "powerful"


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """Structured FinOps analysis — returns parsed JSON findings + provenance."""
    resp = await finops_agent.analyze(req.question, tier=req.tier)
    return resp.as_dict()

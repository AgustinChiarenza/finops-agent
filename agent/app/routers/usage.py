from fastapi import APIRouter

from app.orchestrator import cost_tracker

router = APIRouter()


@router.get("/usage")
async def orchestrator_usage():
    """LLM spend ledger — the FinOps agent accounting for its own model usage."""
    return cost_tracker.summary()


@router.delete("/usage")
async def reset_usage():
    cost_tracker.reset()
    return {"ok": True}

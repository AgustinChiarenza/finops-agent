from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agent import finops_agent

router = APIRouter()


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = Field(default_factory=list)
    tier: str = "auto"  # auto | cheap | standard | powerful


@router.post("/chat")
async def chat(req: ChatRequest):
    """Conversational FinOps turn — returns free-form answer + provenance."""
    history = [{"role": m.role, "content": m.content} for m in req.history]
    resp = await finops_agent.chat(req.question, history=history, tier=req.tier)
    return resp.as_dict()

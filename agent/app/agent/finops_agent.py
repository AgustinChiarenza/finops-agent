"""Core FinOps agent flow.

For every user turn the agent:

1. Retrieves relevant FinOps knowledge chunks from the RAG store.
2. Pulls a live FinOps snapshot from the Cloud Ops Dashboard.
3. Builds a prompt with both contexts clearly delimited.
4. Orchestrates the LLM call through LiteLLM (tier-based model selection,
   fallbacks, cost tracking).
5. Returns the answer plus provenance: KB sources, dashboard endpoints used,
   the model that answered, and the USD cost of the turn.

Two entry points:

* :meth:`FinOpsAgent.chat`  — conversational, returns free-form text.
* :meth:`FinOpsAgent.analyze` — structured, returns parsed JSON findings.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.prompts import finops as prompts_finops
from app.orchestrator import orchestrator, OrchestrationError
from app.rag import retriever
from app.tools import cloud_ops

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    answer: str
    model: str
    tier: str
    cost_usd: float
    latency_ms: float
    knowledge_sources: list[str] = field(default_factory=list)
    dashboard_used: bool = False
    fallback_from: str | None = None
    structured: dict | None = None

    def as_dict(self) -> dict:
        return {
            "answer": self.answer,
            "model": self.model,
            "tier": self.tier,
            "cost_usd": round(self.cost_usd, 6),
            "latency_ms": round(self.latency_ms, 2),
            "knowledge_sources": self.knowledge_sources,
            "dashboard_used": self.dashboard_used,
            "fallback_from": self.fallback_from,
            "structured": self.structured,
        }


def _extract_json(text: str) -> dict | None:
    """Best-effort extraction of a JSON object from an LLM response."""
    for pattern in (
        r"```(?:json)?\s*\n(.*?)\n```",
        r"```(?:json)?\s*(.*?)\s*```",
    ):
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


class FinOpsAgent:
    async def _gather_context(self, question: str) -> tuple[str, list[str], str, bool]:
        knowledge_context, hits = await retriever.retrieve_context(question)
        sources = []
        seen = set()
        for h in hits:
            if h.source not in seen:
                seen.add(h.source)
                sources.append(h.source)
        try:
            snapshot = await cloud_ops.finops_snapshot()
            live_context = json.dumps(snapshot, indent=2, default=str)
            dashboard_used = any(v is not None for v in snapshot.values())
        except Exception as exc:
            logger.warning("dashboard snapshot failed: %s", exc)
            live_context = ""
            dashboard_used = False
        return knowledge_context, sources, live_context, dashboard_used

    async def chat(
        self,
        question: str,
        history: list[dict] | None = None,
        tier: str = "auto",
    ) -> AgentResponse:
        knowledge_context, sources, live_context, dashboard_used = await self._gather_context(question)
        user_prompt = prompts_finops.build_user_prompt(question, knowledge_context, live_context)
        messages = [{"role": "system", "content": prompts_finops.SYSTEM_PROMPT}]
        messages.extend(history or [])
        messages.append({"role": "user", "content": user_prompt})

        result = await orchestrator.completion(messages, tier=tier)
        return AgentResponse(
            answer=result.content,
            model=result.alias,
            tier=result.tier,
            cost_usd=result.cost_usd,
            latency_ms=result.latency_ms,
            knowledge_sources=sources,
            dashboard_used=dashboard_used,
            fallback_from=result.fallback_from,
        )

    async def analyze(
        self,
        question: str,
        tier: str = "powerful",
    ) -> AgentResponse:
        """Structured FinOps analysis — returns parsed JSON findings."""
        knowledge_context, sources, live_context, dashboard_used = await self._gather_context(question)
        user_prompt = prompts_finops.build_user_prompt(question, knowledge_context, live_context)
        user_prompt = f"{user_prompt}\n\n{prompts_finops.ANALYZE_INSTRUCTION}"
        messages = [
            {"role": "system", "content": prompts_finops.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        result = await orchestrator.completion(
            messages, tier=tier, response_format={"type": "json_object"}
        )
        structured = _extract_json(result.content)
        return AgentResponse(
            answer=result.content,
            model=result.alias,
            tier=result.tier,
            cost_usd=result.cost_usd,
            latency_ms=result.latency_ms,
            knowledge_sources=sources,
            dashboard_used=dashboard_used,
            fallback_from=result.fallback_from,
            structured=structured,
        )


finops_agent = FinOpsAgent()

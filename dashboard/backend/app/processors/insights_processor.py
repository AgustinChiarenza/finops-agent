import json
import logging
from datetime import datetime, timezone

from app.cache import cache
from app.config import settings
from app.maas_client import MaasDisabledError, chat_completion_json
from app.prompts import cost_analysis, ops_analysis, security_analysis
from app.processors.inventory_processor import get_inventory_summary
from app.processors.cost_processor import get_cost_summary, get_costs_by_service, get_daily_costs
from app.processors.metrics_processor import get_metrics_summary, get_idle_resources
from app.processors.cts_processor import get_cts_summary, get_security_events

logger = logging.getLogger(__name__)

INSIGHTS_HISTORY_KEY = "insights:history"


def _disabled_response(insight_type: str) -> dict:
    """Standard response returned when MaaS is not configured."""
    return {
        "summary": "AI insights are disabled — MAAS_API_KEY is not configured.",
        "findings": [],
        "risks": [],
        "risk_score": 0,
        "type": insight_type,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disabled": True,
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _build_data_context() -> dict:
    """Collect compact summaries from all data sources for MaaS prompts."""
    inventory = await get_inventory_summary()
    cost = await get_cost_summary()
    cost_by_service = await get_costs_by_service()
    idle = await get_idle_resources()
    cts = await get_cts_summary()
    metrics = await get_metrics_summary()

    # Compact: only top items to stay within token limits
    top_cost_services = cost_by_service[:10]
    top_idle = idle[:10]
    top_metrics = metrics[:20]

    return {
        "inventory": inventory,
        "cost_summary": cost,
        "cost_by_service_top10": top_cost_services,
        "idle_resources_top10": top_idle,
        "cts_summary": cts,
        "metrics_summary_top20": top_metrics,
    }


async def analyze_security() -> dict:
    if not settings.maas_enabled:
        return _disabled_response("security")
    data = await _build_data_context()
    cts_events = await get_security_events()

    user_prompt = f"""Analyze the following cloud operations data for security risks:

CTS Summary: {json.dumps(data['cts_summary'], indent=2)}

Recent Security Events: {json.dumps(cts_events[:20], indent=2)}

Inventory Summary: {json.dumps(data['inventory'], indent=2)}

Idle Resources: {json.dumps(data['idle_resources_top10'], indent=2)}"""

    result = await chat_completion_json([
        {"role": "system", "content": security_analysis.SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])

    result["generated_at"] = _now_iso()
    result["type"] = "security"
    _save_to_history(result)
    return result


async def analyze_cost() -> dict:
    if not settings.maas_enabled:
        return _disabled_response("cost")
    data = await _build_data_context()

    user_prompt = f"""Analyze the following cloud operations data for cost optimization:

Cost Summary: {json.dumps(data['cost_summary'], indent=2)}

Cost by Service (Top 10): {json.dumps(data['cost_by_service_top10'], indent=2)}

Inventory Summary: {json.dumps(data['inventory'], indent=2)}

Idle Resources: {json.dumps(data['idle_resources_top10'], indent=2)}"""

    result = await chat_completion_json([
        {"role": "system", "content": cost_analysis.SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])

    result["generated_at"] = _now_iso()
    result["type"] = "cost"
    _save_to_history(result)
    return result


async def analyze_operational() -> dict:
    if not settings.maas_enabled:
        return _disabled_response("operational")
    data = await _build_data_context()

    user_prompt = f"""Analyze the following cloud operations data for operational risks:

Metrics Summary (Top 20): {json.dumps(data['metrics_summary_top20'], indent=2)}

Inventory Summary: {json.dumps(data['inventory'], indent=2)}

Idle Resources: {json.dumps(data['idle_resources_top10'], indent=2)}

CTS Summary: {json.dumps(data['cts_summary'], indent=2)}"""

    result = await chat_completion_json([
        {"role": "system", "content": ops_analysis.SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])

    result["generated_at"] = _now_iso()
    result["type"] = "operational"
    _save_to_history(result)
    return result


async def analyze_comprehensive() -> dict:
    if not settings.maas_enabled:
        return _disabled_response("comprehensive")
    data = await _build_data_context()
    cts_events = await get_security_events()

    user_prompt = f"""Perform a comprehensive analysis of the following cloud operations data:

INVENTORY: {json.dumps(data['inventory'], indent=2)}

COST: {json.dumps(data['cost_summary'], indent=2)}
Cost by Service: {json.dumps(data['cost_by_service_top10'], indent=2)}

METRICS: {json.dumps(data['metrics_summary_top20'], indent=2)}

CTS: {json.dumps(data['cts_summary'], indent=2)}
Security Events: {json.dumps(cts_events[:10], indent=2)}

IDLE RESOURCES: {json.dumps(data['idle_resources_top10'], indent=2)}"""

    system_prompt = """You are a cloud operations analyst. Perform a comprehensive analysis covering security, cost, and operational aspects.

Return a single JSON object with this exact structure:
{
  "security": {
    "summary": "...",
    "findings": [{"severity": "critical|high|medium|low", "title": "...", "description": "...", "affected_resources": ["..."], "recommendation": "...", "confidence": 0.9}],
    "risk_score": 75
  },
  "cost": {
    "summary": "...",
    "findings": [{"severity": "...", "title": "...", "description": "...", "affected_resources": ["..."], "recommendation": "...", "confidence": 0.9}],
    "risk_score": 50,
    "estimated_monthly_savings_usd": 500
  },
  "operational": {
    "summary": "...",
    "findings": [{"severity": "...", "title": "...", "description": "...", "affected_resources": ["..."], "recommendation": "...", "confidence": 0.9}],
    "risk_score": 40
  }
}

Be specific. Reference actual resource IDs from the data. Rate risk_score 0-100."""

    result = await chat_completion_json([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    now = _now_iso()
    sec = result.get("security", {"summary": "No security analysis", "findings": [], "risk_score": 0})
    sec["generated_at"] = now
    sec["type"] = "security"
    cost = result.get("cost", {"summary": "No cost analysis", "findings": [], "risk_score": 0})
    cost["generated_at"] = now
    cost["type"] = "cost"
    ops = result.get("operational", {"summary": "No operational analysis", "findings": [], "risk_score": 0})
    ops["generated_at"] = now
    ops["type"] = "operational"

    comprehensive = {
        "security": sec,
        "cost": cost,
        "operational": ops,
        "generated_at": now,
        "type": "comprehensive",
    }
    _save_to_history(comprehensive)
    return comprehensive


def _save_to_history(insight: dict) -> None:
    history = cache.get(INSIGHTS_HISTORY_KEY) or []
    history.insert(0, {
        "type": insight.get("type", "unknown"),
        "generated_at": insight.get("generated_at", ""),
        "summary": insight.get("summary", ""),
    })
    cache.set(INSIGHTS_HISTORY_KEY, history[:20])


async def get_insights_history() -> list[dict]:
    return cache.get(INSIGHTS_HISTORY_KEY) or []

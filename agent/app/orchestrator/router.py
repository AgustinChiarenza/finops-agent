"""LiteLLM router wrapper — the orchestration core.

Builds a :class:`litellm.Router` over the MaaS model registry and exposes a
single :meth:`Orchestrator.completion` entry point that:

1. Selects a primary model alias from the requested tier (``cheap`` /
   ``standard`` / ``powerful`` / ``auto``).
2. Calls LiteLLM with a per-tier fallback chain so a failing or rate-limited
   MaaS model transparently falls through to the next.
3. Computes USD cost from token usage and the registry's price rates (MaaS
   custom endpoints are not in LiteLLM's price map, so we price locally).
4. Records every attempt in the :mod:`cost_tracker` ledger.

``auto`` tier uses a lightweight heuristic on the prompt size and keywords to
pick a tier without spending an extra LLM call — good enough for a FinOps agent
where the caller usually knows the task weight, and ``auto`` is just a convenience.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import litellm
from litellm import Router

from app.config import settings
from app.orchestrator import cost_tracker
from app.orchestrator.cost_tracker import CallRecord, now_iso
from app.orchestrator.models import (
    MODEL_REGISTRY,
    TIER_FALLBACK,
    TIER_PREFERENCE,
    TIERS,
    by_alias,
)

logger = logging.getLogger(__name__)

# Silence LiteLLM's chatty default logging unless we're debugging.
litellm.suppress_debug_logging = True


@dataclass
class OrchestrationResult:
    """The outcome of one orchestrated completion call."""

    content: str
    alias: str  # model alias that actually answered
    tier: str
    usage: dict[str, int]
    cost_usd: float
    latency_ms: float
    fallback_from: str | None  # alias of the primary that failed, if any
    raw: Any = None  # underlying LiteLLM response (for streaming/inspection)


class OrchestrationError(RuntimeError):
    """Raised when every model in the fallback chain fails."""


def _build_model_list() -> list[dict]:
    """Translate the registry into LiteLLM Router ``model_list`` entries."""
    if not settings.maas_enabled:
        return []
    entries = []
    for m in MODEL_REGISTRY:
        entries.append({
            "model_name": m.alias,
            "litellm_params": {
                "model": f"openai/{m.maas_model}",
                "api_base": settings.maas_base_url,
                "api_key": settings.maas_api_key,
            },
            "model_info": {
                "tier": m.tier,
                "max_input_tokens": m.max_input_tokens,
                "cost_input_per_1m": m.cost_input_per_1m,
                "cost_output_per_1m": m.cost_output_per_1m,
            },
        })
    return entries


def _build_fallbacks() -> list[dict]:
    """Per-primary fallback chains derived from tier preference."""
    fallbacks = []
    for aliases in TIER_PREFERENCE.values():
        if len(aliases) < 2:
            continue
        primary, *rest = aliases
        fallbacks.append({primary: rest})
    return fallbacks


def _price_call(alias: str, usage: dict[str, int]) -> float:
    """Compute USD cost from token usage and registry rates."""
    m = by_alias(alias)
    inp = usage.get("prompt_tokens", usage.get("input_tokens", 0))
    out = usage.get("completion_tokens", usage.get("output_tokens", 0))
    return (inp / 1_000_000.0) * m.cost_input_per_1m + (out / 1_000_000.0) * m.cost_output_per_1m


def _usage_dict(resp: Any) -> dict[str, int]:
    usage = getattr(resp, "usage", None) or {}
    if hasattr(usage, "model_dump"):
        usage = usage.model_dump()
    return {k: int(v) for k, v in dict(usage).items() if isinstance(v, (int, float))}


def _content_str(resp: Any) -> str:
    try:
        return resp.choices[0].message.content or ""
    except (AttributeError, IndexError, KeyError):
        # Some providers/fallbacks return dict-like responses.
        try:
            return resp["choices"][0]["message"]["content"] or ""
        except Exception:
            return ""


def resolve_alias(resp_or_alias: Any) -> str:
    """Best-effort recovery of the alias that actually served a response."""
    if isinstance(resp_or_alias, str):
        return resp_or_alias
    # LiteLLM tags the routed model name on the response.
    for attr in ("_hidden_params",):
        hp = getattr(resp_or_alias, attr, None)
        if hp and isinstance(hp, dict) and hp.get("model"):
            return str(hp["model"])
    model = getattr(resp_or_alias, "model", None)
    if isinstance(model, str) and model.startswith("finops-"):
        return model
    # Fall back to the litellm openai/<maas_model> form → map back.
    if isinstance(model, str) and model.startswith("openai/"):
        maas_model = model[len("openai/"):]
        for m in MODEL_REGISTRY:
            if m.maas_model == maas_model:
                return m.alias
    raise OrchestrationError("could not determine which model served the response")


class Orchestrator:
    """Wraps :class:`litellm.Router` with tier routing + cost accounting."""

    def __init__(self) -> None:
        self._router: Router | None = None
        self._init_error: str | None = None
        self._configure()

    def _configure(self) -> None:
        model_list = _build_model_list()
        if not model_list:
            self._router = None
            self._init_error = "MAAS_API_KEY is not set — orchestrator disabled"
            logger.warning(self._init_error)
            return
        try:
            self._router = Router(
                model_list=model_list,
                fallbacks=_build_fallbacks(),
                num_retries=2,
                retry_after=2,
                timeout=settings.orchestrator_timeout_seconds,
                allowed_fails=3,
                cooldown_time=60,
            )
            self._init_error = None
        except Exception as exc:  # pragma: no cover — defensive
            self._router = None
            self._init_error = f"failed to initialise LiteLLM router: {exc}"
            logger.error(self._init_error)

    @property
    def enabled(self) -> bool:
        return self._router is not None

    @property
    def disabled_reason(self) -> str | None:
        return self._init_error

    def pick_tier(self, messages: list[dict], tier: str = "auto") -> str:
        """Resolve ``auto`` to a concrete tier via a token+keyword heuristic."""
        if tier != "auto":
            return tier if tier in TIERS else settings.default_tier
        text = " ".join(m.get("content", "") for m in messages).lower()
        approx_tokens = len(text) // 4
        deep_signals = ("plan", "estrategia", "strategy", "comprehensive",
                        "arquitectura", "architecture", "detallado", "deep",
                        "compara", "compare", "migra", "migrate")
        if approx_tokens > 12_000 or any(s in text for s in deep_signals):
            return "powerful"
        if approx_tokens < 1_500 and "?" in text and text.count(" ") < 40:
            return "cheap"
        return settings.default_tier

    def _primary_alias(self, tier: str) -> str:
        aliases = TIER_PREFERENCE.get(tier) or TIER_PREFERENCE[settings.default_tier]
        return aliases[0]

    async def completion(
        self,
        messages: list[dict],
        tier: str = "auto",
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        if not self.enabled:
            raise OrchestrationError(self._init_error or "orchestrator disabled")

        resolved_tier = self.pick_tier(messages, tier)
        primary = self._primary_alias(resolved_tier)
        call_kwargs = {
            "messages": messages,
            "temperature": settings.temperature if temperature is None else temperature,
            "max_tokens": settings.max_tokens if max_tokens is None else max_tokens,
        }
        if response_format:
            call_kwargs["response_format"] = response_format
        call_kwargs.update(kwargs)

        start = time.perf_counter()
        try:
            resp = await self._router.acompletion(model=primary, **call_kwargs)
        except Exception as exc:
            # Router should apply fallbacks internally, but if everything failed
            # surface it and record an unsuccessful attempt against the primary.
            latency = (time.perf_counter() - start) * 1000.0
            cost_tracker.record(CallRecord(
                timestamp=now_iso(), alias=primary, tier=resolved_tier,
                input_tokens=0, output_tokens=0, cost_usd=0.0,
                success=False, latency_ms=latency,
            ))
            raise OrchestrationError(
                f"all models failed for tier {resolved_tier!r} (primary {primary!r}): {exc}"
            ) from exc

        latency = (time.perf_counter() - start) * 1000.0
        try:
            answered = resolve_alias(resp)
        except OrchestrationError:
            answered = primary
        usage = _usage_dict(resp)
        cost = _price_call(answered, usage)
        fallback_from = primary if answered != primary else None
        cost_tracker.record(CallRecord(
            timestamp=now_iso(), alias=answered, tier=resolved_tier,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            cost_usd=cost, success=True, latency_ms=latency,
            fallback_from=fallback_from,
        ))
        return OrchestrationResult(
            content=_content_str(resp),
            alias=answered,
            tier=resolved_tier,
            usage=usage,
            cost_usd=cost,
            latency_ms=latency,
            fallback_from=fallback_from,
            raw=resp,
        )

    async def stream(self, messages: list[dict], tier: str = "auto", **kwargs: Any):
        """Async generator yielding content deltas. Cost is tracked on close."""
        if not self.enabled:
            raise OrchestrationError(self._init_error or "orchestrator disabled")
        resolved_tier = self.pick_tier(messages, tier)
        primary = self._primary_alias(resolved_tier)
        async for chunk in await self._router.acompletion(
            model=primary, messages=messages, stream=True, **kwargs
        ):
            try:
                delta = chunk.choices[0].delta.content
            except (AttributeError, IndexError, KeyError):
                delta = None
            if delta:
                yield delta


orchestrator = Orchestrator()

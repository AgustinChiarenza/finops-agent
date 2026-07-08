"""MaaS model registry and tier routing policy.

Each entry describes one Huawei Cloud ModelArts Studio (MaaS) deployment the
orchestrator can target. MaaS is OpenAI-compatible, so LiteLLM addresses it as
``openai/<maas_model>`` with a custom ``api_base``. Prices are stated per
**1 million tokens** in USD and are used by the cost tracker when LiteLLM cannot
resolve a price for a custom OpenAI-compatible endpoint (which is the common
case for MaaS).

Tiers are an opinionated routing abstraction:

* ``cheap``      — fast, low-cost models for classification, routing, short replies.
* ``standard``   — the workhorse for grounded synthesis and most agent turns.
* ``powerful``   — deep reasoning for multi-step FinOps analysis over large contexts.

``TIER_PREFERENCE`` lists, per tier, the model aliases in priority order. The
first healthy model is used; the rest become the LiteLLM fallback chain.
"""

from __future__ import annotations

from dataclasses import dataclass

TIERS = ("cheap", "standard", "powerful")


@dataclass(frozen=True)
class ModelDef:
    """One MaaS deployment the orchestrator can route to."""

    alias: str  # internal name used in LiteLLM calls, e.g. "finops-deepseek-flash"
    maas_model: str  # model name as known to MaaS, e.g. "deepseek-v4-flash"
    tier: str  # cheap | standard | powerful
    max_input_tokens: int
    cost_input_per_1m: float  # USD per 1M input tokens
    cost_output_per_1m: float  # USD per 1M output tokens
    description: str


# Catalogue of MaaS models available through Huawei ModelArts Studio.
# Prices are conservative placeholders — replace with the rates published in
# your MaaS console so the cost tracker reports accurate spend.
MODEL_REGISTRY: tuple[ModelDef, ...] = (
    ModelDef(
        alias="finops-deepseek-flash",
        maas_model="deepseek-v4-flash",
        tier="cheap",
        max_input_tokens=64_000,
        cost_input_per_1m=0.14,
        cost_output_per_1m=0.28,
        description="Fast, cheap DeepSeek variant for classification and short replies.",
    ),
    ModelDef(
        alias="finops-qwen7b",
        maas_model="qwen2.5-7b-instruct",
        tier="cheap",
        max_input_tokens=32_000,
        cost_input_per_1m=0.10,
        cost_output_per_1m=0.30,
        description="Lightweight Qwen for routing and summarisation.",
    ),
    ModelDef(
        alias="finops-deepseek-v3",
        maas_model="deepseek-v3",
        tier="standard",
        max_input_tokens=64_000,
        cost_input_per_1m=0.27,
        cost_output_per_1m=1.10,
        description="Balanced DeepSeek for grounded synthesis over retrieved context.",
    ),
    ModelDef(
        alias="finops-qwen72b",
        maas_model="qwen2.5-72b-instruct",
        tier="powerful",
        max_input_tokens=32_000,
        cost_input_per_1m=0.50,
        cost_output_per_1m=1.50,
        description="Large Qwen for deep, multi-step FinOps analysis.",
    ),
)

# Ordered preference per tier. Order also defines the fallback chain.
TIER_PREFERENCE: dict[str, list[str]] = {
    "cheap": ["finops-deepseek-flash", "finops-qwen7b", "finops-deepseek-v3"],
    "standard": ["finops-deepseek-v3", "finops-qwen72b", "finops-deepseek-flash"],
    "powerful": ["finops-qwen72b", "finops-deepseek-v3", "finops-deepseek-flash"],
}

# Cross-tier fallback used when an entire tier is exhausted/unavailable.
TIER_FALLBACK: dict[str, str] = {
    "cheap": "standard",
    "standard": "powerful",
    "powerful": "standard",
}


def by_alias(alias: str) -> ModelDef:
    for m in MODEL_REGISTRY:
        if m.alias == alias:
            return m
    raise KeyError(f"unknown model alias: {alias!r}")


def tier_of(alias: str) -> str:
    return by_alias(alias).tier

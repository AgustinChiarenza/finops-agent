"""Tests for orchestrator tier selection and cost pricing (no network)."""

from app.orchestrator.models import TIER_PREFERENCE, by_alias
from app.orchestrator.router import Orchestrator, _price_call


def test_tier_preference_has_fallback_chain_for_every_tier():
    for tier, aliases in TIER_PREFERENCE.items():
        assert len(aliases) >= 2, f"tier {tier} lacks a fallback chain"
        for alias in aliases:
            by_alias(alias)  # resolves


def test_price_call_uses_registry_rates():
    # 1M input + 1M output on deepseek-v4-flash (0.14 / 0.28 per 1M)
    cost = _price_call("finops-deepseek-flash", {"prompt_tokens": 1_000_000, "completion_tokens": 1_000_000})
    assert abs(cost - (0.14 + 0.28)) < 1e-9


def test_price_call_zero_usage_is_zero():
    assert _price_call("finops-qwen72b", {}) == 0.0


def test_pick_tier_auto_short_question_is_cheap():
    orch = Orchestrator()
    tier = orch.pick_tier([{"role": "user", "content": "¿Qué es un ECS?"}], tier="auto")
    assert tier == "cheap"


def test_pick_tier_auto_large_context_is_powerful():
    orch = Orchestrator()
    big = "x " * 20_000  # ~10k tokens, plus a deep signal
    tier = orch.pick_tier([{"role": "user", "content": big + " plan estratégico"}], tier="auto")
    assert tier == "powerful"


def test_pick_tier_explicit_is_respected():
    orch = Orchestrator()
    assert orch.pick_tier([{"role": "user", "content": "hola"}], tier="standard") == "standard"
    # unknown tier falls back to default
    assert orch.pick_tier([{"role": "user", "content": "hola"}], tier="bogus") == "standard"

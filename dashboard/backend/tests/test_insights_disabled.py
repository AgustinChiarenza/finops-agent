import asyncio

from app.config import settings
from app.processors.insights_processor import (
    analyze_comprehensive,
    analyze_cost,
    analyze_operational,
    analyze_security,
)


def test_maas_disabled_by_default_in_tests():
    assert settings.maas_enabled is False


def test_security_insight_returns_disabled_response():
    result = asyncio.run(analyze_security())
    assert result["disabled"] is True
    assert "MAAS_API_KEY" in result["summary"]
    assert result["findings"] == []


def test_all_insights_disabled_without_key():
    for fn in (analyze_cost, analyze_operational, analyze_comprehensive):
        result = asyncio.run(fn())
        assert result.get("disabled") is True

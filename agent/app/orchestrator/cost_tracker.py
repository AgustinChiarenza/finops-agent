"""Per-call cost tracking for the orchestrator.

A FinOps agent should account for its own LLM spend — this module is that
self-accounting. It keeps an in-memory ledger keyed by day → model → tier with
input/output token totals and USD cost, and can optionally append every call to
a JSONL file for durable, tenant-level chargeback.

The ledger is intentionally simple (no persistence beyond optional JSONL) so it
works in a single-process deployment; for multi-worker setups point
``cost_log_path`` at a shared volume and aggregate offline.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CallRecord:
    timestamp: str
    alias: str
    tier: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    success: bool
    latency_ms: float
    fallback_from: str | None = None


@dataclass
class _Bucket:
    calls: int = 0
    successes: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class CostTracker:
    """Thread-safe in-memory ledger with optional JSONL append."""

    def __init__(self, cost_log_path: str | os.PathLike | None = None):
        self._lock = threading.Lock()
        self._by_day_model: dict[str, dict[str, _Bucket]] = defaultdict(lambda: defaultdict(_Bucket))
        self._by_tier: dict[str, _Bucket] = defaultdict(_Bucket)
        self._total = _Bucket()
        self._recent: list[CallRecord] = []
        self._cost_log_path = Path(cost_log_path) if cost_log_path else None

    def record(self, rec: CallRecord) -> None:
        day = rec.timestamp[:10]  # YYYY-MM-DD from ISO timestamp
        with self._lock:
            bucket = self._by_day_model[day][rec.alias]
            self._accumulate(bucket, rec)
            self._accumulate(self._by_tier[rec.tier], rec)
            self._accumulate(self._total, rec)
            self._recent.insert(0, rec)
            del self._recent[50:]
        self._append_jsonl(rec)

    @staticmethod
    def _accumulate(bucket: _Bucket, rec: CallRecord) -> None:
        bucket.calls += 1
        bucket.successes += int(rec.success)
        bucket.input_tokens += rec.input_tokens
        bucket.output_tokens += rec.output_tokens
        bucket.cost_usd += rec.cost_usd

    def _append_jsonl(self, rec: CallRecord) -> None:
        if not self._cost_log_path:
            return
        try:
            self._cost_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._cost_log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(self._serialize_record(rec)) + "\n")
        except OSError as exc:
            logger.warning("cost log write failed: %s", exc)

    def summary(self) -> dict[str, Any]:
        with self._lock:
            by_day_model = {
                day: {
                    model: self._serialize_bucket(b)
                    for model, b in models.items()
                }
                for day, models in self._by_day_model.items()
            }
            by_tier = {tier: self._serialize_bucket(b) for tier, b in self._by_tier.items()}
            recent = [self._serialize_record(r) for r in self._recent]
            return {
                "total": self._serialize_bucket(self._total),
                "by_tier": by_tier,
                "by_day_model": by_day_model,
                "recent": recent,
            }

    def reset(self) -> None:
        with self._lock:
            self._by_day_model.clear()
            self._by_tier.clear()
            self._total = _Bucket()
            self._recent.clear()

    @staticmethod
    def _serialize_bucket(b: _Bucket) -> dict[str, Any]:
        return {
            "calls": b.calls,
            "successes": b.successes,
            "input_tokens": b.input_tokens,
            "output_tokens": b.output_tokens,
            "cost_usd": round(b.cost_usd, 6),
        }

    @staticmethod
    def _serialize_record(r: CallRecord) -> dict[str, Any]:
        return {
            "timestamp": r.timestamp,
            "alias": r.alias,
            "tier": r.tier,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "cost_usd": round(r.cost_usd, 6),
            "success": r.success,
            "latency_ms": round(r.latency_ms, 2),
            "fallback_from": r.fallback_from,
        }


def _default_log_path() -> str | None:
    return os.environ.get("ORCHESTRATOR_COST_LOG") or None


cost_tracker = CostTracker(cost_log_path=_default_log_path())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

import json
import logging
from collections import defaultdict
from datetime import date

from app.cache import cache
from app.obs_client import obs_reader
from app.schemas.cts import CtsSecurityEvent, CtsSummary, CtsTrace

logger = logging.getLogger(__name__)

CTS_PREFIX = "CTS/traces/"


async def _get_all_traces() -> list[dict]:
    cache_key = "cts:all"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Try to find CTS data in the bucket
    objects = obs_reader.list_objects(CTS_PREFIX)
    if not objects:
        logger.info("No CTS data found in OBS bucket")
        cache.set(cache_key, [])
        return []

    all_traces = []
    for obj in objects:
        key = obj["key"]
        if key.endswith(".json"):
            data = obs_reader.get_object_as_text(key)
            if data:
                try:
                    parsed = json.loads(data)
                    if isinstance(parsed, list):
                        all_traces.extend(parsed)
                    else:
                        all_traces.append(parsed)
                except json.JSONDecodeError:
                    continue
        elif key.endswith(".jsonl.gz"):
            async for record in obs_reader.stream_jsonl_gz(key.replace(obs_reader.prefix + "/", "")):
                all_traces.append(record)

    cache.set(cache_key, all_traces)
    return all_traces


def _parse_trace(raw: dict) -> CtsTrace:
    return CtsTrace(
        trace_id=raw.get("trace_id", ""),
        time=raw.get("time", raw.get("timestamp", "")),
        user=raw.get("user", raw.get("caller", "")),
        resource_type=raw.get("resource_type", ""),
        resource_id=raw.get("resource_id", ""),
        api_name=raw.get("api_name", raw.get("operation", "")),
        request_method=raw.get("request", {}).get("method", "") if isinstance(raw.get("request"), dict) else "",
        request_url=raw.get("request", {}).get("url", "") if isinstance(raw.get("request"), dict) else "",
        response_status=raw.get("response", {}).get("status_code", 200) if isinstance(raw.get("response"), dict) else raw.get("response_status", 200),
        source_ip=raw.get("source_ip", ""),
        trace_status=raw.get("trace_status", "normal"),
    )


async def get_traces(
    start_date: date | None = None,
    end_date: date | None = None,
    user: str | None = None,
    resource_type: str | None = None,
    api_name: str | None = None,
    severity: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    all_traces = await _get_all_traces()
    if not all_traces:
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0, "note": "No CTS data available in OBS bucket"}

    parsed = [_parse_trace(t) for t in all_traces]

    filtered = parsed
    if start_date:
        sd = start_date.isoformat()
        filtered = [t for t in filtered if t.time >= sd]
    if end_date:
        ed = end_date.isoformat()
        filtered = [t for t in filtered if t.time <= ed + "T23:59:59"]
    if user:
        filtered = [t for t in filtered if t.user == user]
    if resource_type:
        filtered = [t for t in filtered if t.resource_type == resource_type]
    if api_name:
        filtered = [t for t in filtered if api_name.lower() in t.api_name.lower()]
    if severity == "error":
        filtered = [t for t in filtered if t.response_status >= 400]
    elif severity == "warning":
        filtered = [t for t in filtered if t.response_status >= 300]

    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    items = filtered[start : start + page_size]

    return {
        "items": [i.model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


async def get_cts_summary() -> dict:
    cache_key = "cts:summary"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    all_traces = await _get_all_traces()
    if not all_traces:
        return CtsSummary(total_traces=0, actions_by_user={}, actions_by_service={}, actions_by_hour={}, failed_count=0, delete_count=0).model_dump()

    parsed = [_parse_trace(t) for t in all_traces]

    by_user: dict[str, int] = defaultdict(int)
    by_service: dict[str, int] = defaultdict(int)
    by_hour: dict[str, int] = defaultdict(int)
    failed = 0
    deletes = 0

    for t in parsed:
        by_user[t.user] += 1
        by_service[t.resource_type] += 1
        hour = t.time[11:13] if len(t.time) > 13 else "00"
        by_hour[hour] += 1
        if t.response_status >= 400:
            failed += 1
        if "delete" in t.api_name.lower():
            deletes += 1

    summary = CtsSummary(
        total_traces=len(parsed),
        actions_by_user=dict(by_user),
        actions_by_service=dict(by_service),
        actions_by_hour=dict(by_hour),
        failed_count=failed,
        delete_count=deletes,
    ).model_dump()
    cache.set(cache_key, summary)
    return summary


async def get_security_events() -> list[dict]:
    all_traces = await _get_all_traces()
    if not all_traces:
        return []

    parsed = [_parse_trace(t) for t in all_traces]
    events = []

    for t in parsed:
        severity = None
        desc = ""

        # Failed authentication
        if t.response_status in (401, 403):
            severity = "high"
            desc = f"Failed auth attempt by {t.user} from {t.source_ip}"
        # IAM changes
        elif "iam" in t.api_name.lower() or "policy" in t.api_name.lower():
            severity = "critical"
            desc = f"IAM policy change by {t.user}: {t.api_name}"
        # Delete operations
        elif "delete" in t.api_name.lower():
            severity = "medium"
            desc = f"Delete operation by {t.user} on {t.resource_type}/{t.resource_id}"
        # Cross-region (simplified check)
        elif t.source_ip and not t.source_ip.startswith(("10.", "192.168.", "172.")):
            severity = "low"
            desc = f"External IP access by {t.user} from {t.source_ip}"

        if severity:
            events.append(CtsSecurityEvent(
                trace_id=t.trace_id,
                time=t.time,
                user=t.user,
                api_name=t.api_name,
                resource_type=t.resource_type,
                resource_id=t.resource_id,
                source_ip=t.source_ip,
                severity=severity,
                description=desc,
            ).model_dump())

    return sorted(events, key=lambda e: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(e["severity"], 4))

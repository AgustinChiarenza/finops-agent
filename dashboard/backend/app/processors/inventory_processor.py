import logging
from datetime import date

from app.cache import cache
from app.obs_client import obs_reader
from app.schemas.inventory import InventorySummary, ResourceItem

logger = logging.getLogger(__name__)

OBS_PATH = "Inventory/resource_inventory.json"


def _parse_resource(raw: dict) -> ResourceItem:
    return ResourceItem(
        resource_id=raw.get("resource_id", ""),
        resource_name=raw.get("resource_name", ""),
        service_type=raw.get("service_type", ""),
        environment=raw.get("environment", ""),
        owner=raw.get("owner", ""),
        status=raw.get("status", ""),
        region=raw.get("region", ""),
        monthly_cost=float(raw.get("monthly_cost_usd", raw.get("monthly_cost", 0))),
        usage_profile=raw.get("usage_profile", ""),
        created_date=raw.get("created_at", raw.get("created_date", "")),
        tags=raw.get("tags", {}),
    )


async def get_inventory(
    service_type: str | None = None,
    environment: str | None = None,
    owner: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    cache_key = "inventory:all"
    all_resources = cache.get(cache_key)

    if all_resources is None:
        raw = obs_reader.get_object_as_json(OBS_PATH)
        if raw is None:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
        data = raw if isinstance(raw, list) else raw.get("resources", [])
        all_resources = [_parse_resource(r) for r in data]
        cache.set(cache_key, all_resources)

    filtered = all_resources
    if service_type:
        filtered = [r for r in filtered if r.service_type == service_type]
    if environment:
        filtered = [r for r in filtered if r.environment == environment]
    if owner:
        filtered = [r for r in filtered if r.owner == owner]
    if status:
        filtered = [r for r in filtered if r.status == status]

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


async def get_inventory_summary() -> dict:
    cache_key = "inventory:summary"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    all_resources = cache.get("inventory:all")
    if all_resources is None:
        raw = obs_reader.get_object_as_json(OBS_PATH)
        if raw is None:
            return InventorySummary(
                total_resources=0, by_service_type={}, by_status={},
                by_environment={}, by_owner={}, total_monthly_cost=0,
                cost_by_service_type={},
            ).model_dump()
        data = raw if isinstance(raw, list) else raw.get("resources", [])
        all_resources = [_parse_resource(r) for r in data]
        cache.set("inventory:all", all_resources)

    by_service: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_env: dict[str, int] = {}
    by_owner: dict[str, int] = {}
    cost_by_service: dict[str, float] = {}
    total_cost = 0.0

    for r in all_resources:
        by_service[r.service_type] = by_service.get(r.service_type, 0) + 1
        by_status[r.status] = by_status.get(r.status, 0) + 1
        by_env[r.environment] = by_env.get(r.environment, 0) + 1
        by_owner[r.owner] = by_owner.get(r.owner, 0) + 1
        cost_by_service[r.service_type] = cost_by_service.get(r.service_type, 0.0) + r.monthly_cost
        total_cost += r.monthly_cost

    summary = InventorySummary(
        total_resources=len(all_resources),
        by_service_type=by_service,
        by_status=by_status,
        by_environment=by_env,
        by_owner=by_owner,
        total_monthly_cost=round(total_cost, 2),
        cost_by_service_type={k: round(v, 2) for k, v in cost_by_service.items()},
    ).model_dump()
    cache.set(cache_key, summary)
    return summary

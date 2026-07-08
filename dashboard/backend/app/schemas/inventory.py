from pydantic import BaseModel


class ResourceItem(BaseModel):
    resource_id: str
    resource_name: str
    service_type: str
    environment: str
    owner: str
    status: str
    region: str
    monthly_cost: float
    usage_profile: str
    created_date: str
    tags: dict = {}


class InventorySummary(BaseModel):
    total_resources: int
    by_service_type: dict[str, int]
    by_status: dict[str, int]
    by_environment: dict[str, int]
    by_owner: dict[str, int]
    total_monthly_cost: float
    cost_by_service_type: dict[str, float]

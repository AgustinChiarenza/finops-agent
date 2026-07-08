from pydantic import BaseModel


class DailyCostPoint(BaseModel):
    date: str
    cost: float
    service_type: str = ""


class CostByService(BaseModel):
    service_type: str
    total_cost: float
    percentage: float


class CostByOwner(BaseModel):
    owner: str
    total_cost: float
    percentage: float


class CostAnomaly(BaseModel):
    date: str
    actual_cost: float
    expected_cost: float
    deviation_pct: float
    service_type: str = ""


class CostSummary(BaseModel):
    total_cost: float
    average_daily: float
    trend_direction: str
    trend_pct: float
    anomaly_count: int

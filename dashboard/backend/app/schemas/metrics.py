from pydantic import BaseModel


class MetricDatapoint(BaseModel):
    timestamp: str
    value: float


class MetricTimeseries(BaseModel):
    resource_id: str
    resource_name: str
    metric_name: str
    unit: str
    datapoints: list[MetricDatapoint]


class MetricSummaryItem(BaseModel):
    resource_id: str
    resource_name: str
    metric_name: str
    avg: float
    max: float
    min: float
    p95: float
    unit: str


class IdleResource(BaseModel):
    resource_id: str
    resource_name: str
    service_type: str
    monthly_cost: float
    avg_cpu: float
    avg_network_in: float
    avg_network_out: float
    reason: str

from pydantic import BaseModel


class SecurityFinding(BaseModel):
    severity: str
    title: str
    description: str
    affected_resources: list[str]
    recommendation: str
    confidence: float


class SecurityInsight(BaseModel):
    summary: str
    findings: list[SecurityFinding]
    risk_score: float


class CostAnomalyFinding(BaseModel):
    resource_id: str
    resource_name: str
    service_type: str
    expected_cost: float
    actual_cost: float
    deviation_pct: float
    recommendation: str


class CostInsight(BaseModel):
    summary: str
    anomalies: list[CostAnomalyFinding]
    optimization_candidates: list[dict]
    estimated_monthly_savings_usd: float


class OpsRisk(BaseModel):
    severity: str
    title: str
    description: str
    affected_resources: list[str]
    recommendation: str


class OpsInsight(BaseModel):
    summary: str
    risks: list[OpsRisk]
    recommendations: list[str]


class ComprehensiveInsight(BaseModel):
    security: SecurityInsight | None = None
    cost: CostInsight | None = None
    operational: OpsInsight | None = None

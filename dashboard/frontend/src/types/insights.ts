export interface SecurityFinding {
  severity: string
  title: string
  description: string
  affected_resources: string[]
  recommendation: string
  confidence: number
}

export interface CostAnomalyFinding {
  resource_id: string
  resource_name: string
  service_type: string
  expected_cost: number
  actual_cost: number
  deviation_pct: number
  recommendation: string
}

export interface OpsRisk {
  severity: string
  title: string
  description: string
  affected_resources: string[]
  recommendation: string
}

export interface InsightResult {
  summary: string
  findings?: SecurityFinding[]
  anomalies?: CostAnomalyFinding[]
  risks?: OpsRisk[]
  recommendations?: string[]
  risk_score?: number
  estimated_monthly_savings_usd?: number
  optimization_candidates?: Record<string, unknown>[]
  generated_at: string
  type: string
}

export interface ComprehensiveInsight {
  security: InsightResult | null
  cost: InsightResult | null
  operational: InsightResult | null
  generated_at: string
  type: string
}

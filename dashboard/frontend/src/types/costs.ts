export interface DailyCostPoint {
  date: string
  cost: number
}

export interface CostByService {
  service_type: string
  total_cost: number
  percentage: number
}

export interface CostByOwner {
  owner: string
  total_cost: number
  percentage: number
}

export interface CostAnomaly {
  date: string
  actual_cost: number
  expected_cost: number
  deviation_pct: number
}

export interface CostSummary {
  total_cost: number
  average_daily: number
  trend_direction: string
  trend_pct: number
  anomaly_count: number
}

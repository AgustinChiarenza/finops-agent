export interface MetricDatapoint {
  timestamp: string
  value: number
}

export interface MetricTimeseries {
  resource_id: string
  resource_name: string
  metric_name: string
  unit: string
  datapoints: MetricDatapoint[]
}

export interface MetricSummaryItem {
  resource_id: string
  resource_name: string
  metric_name: string
  avg: number
  max: number
  min: number
  p95: number
  unit: string
}

export interface IdleResource {
  resource_id: string
  resource_name: string
  service_type: string
  monthly_cost: number
  avg_cpu: number
  avg_network_in: number
  avg_network_out: number
  reason: string
}

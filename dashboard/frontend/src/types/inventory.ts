export interface ResourceItem {
  resource_id: string
  resource_name: string
  service_type: string
  environment: string
  owner: string
  status: string
  region: string
  monthly_cost: number
  usage_profile: string
  created_date: string
  tags: Record<string, string>
}

export interface InventorySummary {
  total_resources: number
  by_service_type: Record<string, number>
  by_status: Record<string, number>
  by_environment: Record<string, number>
  by_owner: Record<string, number>
  total_monthly_cost: number
  cost_by_service_type: Record<string, number>
}

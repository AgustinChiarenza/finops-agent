import { useQuery } from '@tanstack/react-query'
import { inventoryApi } from '../api/inventory'

export function useInventorySummary() {
  return useQuery({
    queryKey: ['inventory', 'summary'],
    queryFn: inventoryApi.summary,
  })
}

export function useInventory(params?: Record<string, string | number>) {
  return useQuery({
    queryKey: ['inventory', 'list', params],
    queryFn: () => inventoryApi.list(params),
  })
}

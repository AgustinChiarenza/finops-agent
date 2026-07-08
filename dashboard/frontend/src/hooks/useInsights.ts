import { useMutation, useQuery } from '@tanstack/react-query'
import { insightsApi } from '../api/insights'

export function useSecurityInsight() {
  return useMutation({
    mutationFn: insightsApi.security,
  })
}

export function useCostInsight() {
  return useMutation({
    mutationFn: insightsApi.cost,
  })
}

export function useOperationalInsight() {
  return useMutation({
    mutationFn: insightsApi.operational,
  })
}

export function useComprehensiveInsight() {
  return useMutation({
    mutationFn: insightsApi.comprehensive,
  })
}

export function useInsightsHistory() {
  return useQuery({
    queryKey: ['insights', 'history'],
    queryFn: insightsApi.history,
  })
}

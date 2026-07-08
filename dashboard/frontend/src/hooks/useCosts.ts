import { useQuery } from '@tanstack/react-query'
import { costsApi } from '../api/costs'

export function useCostSummary(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['costs', 'summary', params],
    queryFn: () => costsApi.summary(params),
  })
}

export function useDailyCosts(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['costs', 'daily', params],
    queryFn: () => costsApi.daily(params),
  })
}

export function useCostsByService(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['costs', 'by-service', params],
    queryFn: () => costsApi.byService(params),
  })
}

export function useCostsByOwner(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['costs', 'by-owner', params],
    queryFn: () => costsApi.byOwner(params),
  })
}

export function useCostAnomalies(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['costs', 'anomalies', params],
    queryFn: () => costsApi.anomalies(params),
  })
}

import { useQuery } from '@tanstack/react-query'
import { metricsApi } from '../api/metrics'

export function useMetricsSummary(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['metrics', 'summary', params],
    queryFn: () => metricsApi.summary(params),
  })
}

export function useMetricsTimeseries(params: Record<string, string | number>) {
  return useQuery({
    queryKey: ['metrics', 'timeseries', params],
    queryFn: () => metricsApi.timeseries(params),
    enabled: !!params.resource_id,
  })
}

export function useIdleResources() {
  return useQuery({
    queryKey: ['metrics', 'idle'],
    queryFn: () => metricsApi.idleResources(),
  })
}

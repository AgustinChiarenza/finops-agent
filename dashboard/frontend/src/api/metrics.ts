import { api } from './client'

export const metricsApi = {
  timeseries: (params: Record<string, string | number>) =>
    api.get('/metrics/timeseries', { params }).then(r => r.data),

  summary: (params?: Record<string, string>) =>
    api.get('/metrics/summary', { params }).then(r => r.data),

  idleResources: (params?: Record<string, number>) =>
    api.get('/metrics/idle-resources', { params }).then(r => r.data),
}

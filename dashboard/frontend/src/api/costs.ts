import { api } from './client'

export const costsApi = {
  daily: (params?: Record<string, string>) =>
    api.get('/costs/daily', { params }).then(r => r.data),

  byService: (params?: Record<string, string>) =>
    api.get('/costs/by-service', { params }).then(r => r.data),

  byOwner: (params?: Record<string, string>) =>
    api.get('/costs/by-owner', { params }).then(r => r.data),

  anomalies: (params?: Record<string, string>) =>
    api.get('/costs/anomalies', { params }).then(r => r.data),

  summary: (params?: Record<string, string>) =>
    api.get('/costs/summary', { params }).then(r => r.data),
}

import { api } from './client'

export const ctsApi = {
  traces: (params?: Record<string, string | number>) =>
    api.get('/cts/traces', { params }).then(r => r.data),

  summary: () =>
    api.get('/cts/summary').then(r => r.data),

  securityEvents: () =>
    api.get('/cts/security-events').then(r => r.data),
}

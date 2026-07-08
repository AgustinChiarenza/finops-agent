import { api } from './client'

export const insightsApi = {
  security: () =>
    api.post('/insights/security').then(r => r.data),

  cost: () =>
    api.post('/insights/cost').then(r => r.data),

  operational: () =>
    api.post('/insights/operational').then(r => r.data),

  comprehensive: () =>
    api.post('/insights/comprehensive').then(r => r.data),

  history: () =>
    api.get('/insights/history').then(r => r.data),
}

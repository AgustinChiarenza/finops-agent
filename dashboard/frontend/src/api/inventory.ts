import { api } from './client'

export const inventoryApi = {
  list: (params?: Record<string, string | number>) =>
    api.get('/inventory', { params }).then(r => r.data),

  summary: () =>
    api.get('/inventory/summary').then(r => r.data),
}

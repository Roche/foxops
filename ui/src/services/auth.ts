import { api } from './api'

export const auth = {
  checkToken: () => api.get('/auth/test', { apiPrefix: '', format: 'text' })
}

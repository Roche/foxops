import { api } from './api'

export const auth = {
  checkToken: () => api.get('/auth/test', { isApi: false, format: 'text' })
}

import { api } from './api'

export const auth = {
  checkToken: () => api.get('/auth/test', { apiPrefix: '', format: 'text' }),
  fetchToken: (code: string, state: string) => api.get<undefined, string>(`/auth/token?code=${code}&state=${state}`, { apiPrefix: '', format: 'json', authorized: false })
}

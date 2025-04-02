import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { STORAGE_KEYS } from '../services/storage'
import { AuthorizationToken } from 'interfaces/authz.types'

interface AuthStore {
  token: null | AuthorizationToken,
  setToken: (token: null | AuthorizationToken) => void,
}

export const useAuthStore = create<AuthStore>()(
  persist(
    set => ({
      token: null,
      setToken: (token: null | AuthorizationToken) => set(() => ({ token }))
    }),
    {
      name: STORAGE_KEYS.AUTH,
      partialize: state => ({ token: state.token })
    }
  )
)

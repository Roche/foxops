import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { STORAGE_KEYS } from '../services/storage'
import { AuthorizationToken } from 'interfaces/authz.types'
import { UserWithGroups } from 'interfaces/user.types'

interface AuthStore {
  token: null | AuthorizationToken,
  user: null | UserWithGroups,
  setToken: (token: null | AuthorizationToken) => void,
  setUser: (user: null | UserWithGroups) => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    set => ({
      token: null,
      user: null,
      setToken: (token: null | AuthorizationToken) => set(() => ({ token })),
      setUser: (user: null | UserWithGroups) => set(() => ({ user }))
    }),
    {
      name: STORAGE_KEYS.AUTH,
      partialize: state => ({ token: state.token, user: state.user })
    }
  )
)

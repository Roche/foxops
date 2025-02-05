import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { STORAGE_KEYS } from '../services/storage'

interface AuthStore {
  token: null | string,
  setToken: (token: null | string) => void,
}

export const useAuthStore = create<AuthStore>()(
  persist(
    set => ({
      token: null,
      setToken: (token: null | string) => set(() => ({ token }))
    }),
    {
      name: STORAGE_KEYS.AUTH,
      partialize: state => ({ token: state.token })
    }
  )
)

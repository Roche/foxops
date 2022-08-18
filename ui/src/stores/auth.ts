import create from 'zustand'
import { persist } from 'zustand/middleware'
import { createStorageKey, STORAGE_KEYS } from '../services/storage'

interface AuthStore {
  token: null | string,
  setToken: (token: string) => void,
}

export const useAuthStore = create<AuthStore>()(
  persist(
    set => ({
      token: null,
      setToken: (token: string) => set(() => ({ token }))
    }),
    {
      name: STORAGE_KEYS.AUTH,
      getStorage: () => sessionStorage,
      partialize: state => ({ token: state.token })
    }
  )
)

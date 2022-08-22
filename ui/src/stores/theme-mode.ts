import create from 'zustand'
import { persist, devtools } from 'zustand/middleware'
import { STORAGE_KEYS } from '../services/storage'
import { ThemeMode } from '../shared/types'

const defaultMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'

interface ThemeStore {
  mode: ThemeMode,
  setMode: (mode: ThemeMode) => void,
  toggleMode: () => void
}

export const useThemeModeStore = create<ThemeStore>()(
  devtools(
    persist(
      set => ({
        mode: defaultMode,
        setMode: (mode: ThemeMode) => set(() => ({ mode })),
        toggleMode: () => set(state => ({ mode: state.mode === 'light' ? 'dark' : 'light' }))
      }),
      {
        name: STORAGE_KEYS.THEME,
        getStorage: () => localStorage,
        partialize: state => ({ mode: state.mode })
      }
    )
  )
)

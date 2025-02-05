import { create } from 'zustand'

interface ToolbarSearchStore {
  search: string,
  setSearch: (search: string) => void
}

export const useToolbarSearchStore = create<ToolbarSearchStore>()(set => ({
  search: '',
  setSearch: (search: string) => set(() => ({ search }))
}))

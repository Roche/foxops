import { create } from 'zustand'

interface IncarnationsSortStore {
  sort: string,
  asc: boolean,
  setSort: (sort: string, asc: boolean) => void,
}

export const useIncarnationsSortStore = create<IncarnationsSortStore>()(set => ({
  sort: 'incarnationRepository',
  asc: true,
  setSort: (sort, asc) => set({ sort, asc })
}))

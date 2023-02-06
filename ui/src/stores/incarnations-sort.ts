import create from 'zustand'
import { IncarnationsSortBy } from '../interfaces/incarnations.type'

interface IncarnationsSortStore {
  sort: IncarnationsSortBy,
  asc: boolean,
  setSort: (sort: IncarnationsSortBy, asc: boolean) => void,
}

export const useIncarnationsSortStore = create<IncarnationsSortStore>()(set => ({
  sort: 'incarnationRepository',
  asc: true,
  setSort: (sort, asc) => set({ sort, asc })
}))

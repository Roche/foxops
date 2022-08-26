import create from 'zustand'

interface RequestProcessingStore {
  pending: boolean,
  setPending: (pending: boolean) => void
}

export const useRequestProcessingStore = create<RequestProcessingStore>()(set => ({
  pending: false,
  setPending: (pending: boolean) => set(() => ({ pending }))
}))

import { ApiErrorResponse } from 'services/api'
import { create } from 'zustand'

interface ErrorStore {
  error: ApiErrorResponse | null,
  setError: (error: ApiErrorResponse) => void,
  clearError: () => void
}

export const useErrorStore = create<ErrorStore>()(set => ({
  error: null,
  setError: (error: ApiErrorResponse) => set(() => ({ error })),
  clearError: () => set(() => ({ error: null }))
})
)

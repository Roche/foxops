import create from 'zustand'
import { Incarnation } from '../services/incarnations'

interface IncarnationsOperationsStore {
  selectedIncarnations: Incarnation[]
  select: (incarnation: Incarnation) => void
  deselect: (incarnation: Incarnation) => void
  clearSelection: () => void
  clearAll: () => void
  updatingIds: number[]
  updatedIds: number[]
  failedUpdatedIds: number[]
  startUpdate: (ids: number[]) => void
  updateSucceed: (id: number) => void
  updateFailed: (id: number) => void
}

export const useIncarnationsOperations = create<IncarnationsOperationsStore>(set => ({
  selectedIncarnations: [],
  select: incarnation => {
    set(state => ({
      selectedIncarnations: [...state.selectedIncarnations, incarnation]
    }))
  },
  deselect: incarnation => {
    set(state => ({
      selectedIncarnations: state.selectedIncarnations.filter(x => x.id !== incarnation.id)
    }))
  },
  clearSelection: () => {
    set(() => ({
      selectedIncarnations: []
    }))
  },
  clearAll: () => {
    set(() => ({
      selectedIncarnations: [],
      updatingIds: [],
      updatedIds: [],
      failedUpdatedIds: []
    }))
  },
  updatingIds: [],
  updatedIds: [],
  failedUpdatedIds: [],
  startUpdate: ids => {
    set(() => ({
      updatingIds: ids,
      failedUpdatedIds: [],
      updatedIds: []
    }))
  },
  updateSucceed: id => {
    set(state => ({
      updatedIds: [...state.updatedIds, id]
    }))
  },
  updateFailed: id => {
    set(state => ({
      failedUpdatedIds: [...state.failedUpdatedIds, id]
    }))
  }
}))

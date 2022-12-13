import create from 'zustand'
import { Incarnation } from '../services/incarnations'

interface SelectedIncarnationsStore {
  selectedIncarnations: Incarnation[]
  add: (incarnation: Incarnation) => void
  remove: (incarnation: Incarnation) => void
}

export const useSelectedIncarnationsStore = create<SelectedIncarnationsStore>(set => ({
  selectedIncarnations: [],
  add: incarnation => {
    set(state => ({
      selectedIncarnations: [...state.selectedIncarnations, incarnation]
    }))
  },
  remove: incarnation => {
    set(state => ({
      selectedIncarnations: state.selectedIncarnations.filter(x => x.id !== incarnation.id)
    }))
  }
}))

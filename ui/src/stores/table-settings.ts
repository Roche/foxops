import create from 'zustand'
import { INCARNATION_TABLE_COLUMNS } from '../constants/incarnations.consts'
import { IncarnationBase } from '../interfaces/incarnations.types'

interface TableSettingsStore {
  visibleColumns: (keyof IncarnationBase)[],
  tableDensity: 'compact' | 'comfortable',
  actionsSimplified: boolean,
  setVisibleColumns: (visibleColumns: (keyof IncarnationBase)[]) => void
}
export const useTableSettingsStore = create<TableSettingsStore>()(set => (
  {
    visibleColumns: INCARNATION_TABLE_COLUMNS.map(x => x.id),
    tableDensity: 'comfortable',
    actionsSimplified: false,
    setVisibleColumns: (visibleColumns: (keyof IncarnationBase)[]) => set(() => ({ visibleColumns }))
  }
))

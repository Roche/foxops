import create from 'zustand'
import { INCARNATION_TABLE_COLUMNS } from '../constants/incarnations.consts'
import { IncarnationBase } from '../interfaces/incarnations.types'

type TableDensity = 'comfortable' | 'compact'
interface TableSettingsStore {
  visibleColumns: (keyof IncarnationBase)[],
  tableDensity: TableDensity,
  actionsSimplified: boolean,
  withPagination: boolean,
  setVisibleColumns: (visibleColumns: (keyof IncarnationBase)[]) => void
  setDensity: (tableDensity: TableDensity) => void
  setActionsSimplified: (actionsSimplified: boolean) => void,
  setWithPagination: (withPagination: boolean) => void
}
export const useTableSettingsStore = create<TableSettingsStore>()(set => (
  {
    visibleColumns: INCARNATION_TABLE_COLUMNS.map(x => x.id),
    tableDensity: 'comfortable',
    actionsSimplified: false,
    withPagination: true,
    setVisibleColumns: (visibleColumns: (keyof IncarnationBase)[]) => set(() => ({ visibleColumns })),
    setDensity: (tableDensity: TableDensity) => set(() => ({ tableDensity })),
    setActionsSimplified: (actionsSimplified: boolean) => set(() => ({ actionsSimplified })),
    setWithPagination: (withPagination: boolean) => set(() => ({ withPagination }))
  }
))

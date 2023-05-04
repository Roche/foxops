import create from 'zustand'
import { persist } from 'zustand/middleware'
import { INCARNATION_TABLE_COLUMNS, IncarnationTableColumn } from '../constants/incarnations.consts'
import { IncarnationBase } from '../interfaces/incarnations.types'
import { OnChangeFn, PaginationState, SortingState } from '@tanstack/react-table'
import { STORAGE_KEYS } from '../services/storage'

const DEFAULT_COLUMNS_IDS: (keyof IncarnationBase)[] = [
  'incarnationRepository',
  'targetDirectory',
  'templateRepository',
  'requestedVersion',
  'revision'
]

const DEFAULT_COLUMNS = INCARNATION_TABLE_COLUMNS.filter(
  x => DEFAULT_COLUMNS_IDS.includes(x.id)
)

type TableDensity = 'comfortable' | 'compact'
interface TableSettingsStore {
  visibleColumns: IncarnationTableColumn[],
  tableDensity: TableDensity,
  actionsSimplified: boolean,
  withPagination: boolean,
  pagination: PaginationState
  sorting: SortingState
  setVisibleColumns: (visibleColumns: (keyof IncarnationBase)[]) => void
  setDensity: (tableDensity: TableDensity) => void
  setActionsSimplified: (actionsSimplified: boolean) => void,
  setWithPagination: (withPagination: boolean) => void,
  setColumnsSize: (columns: {id: string, width: number}[]) => void
  setPagination: (pagination: PaginationState) => void,
  setSorting: OnChangeFn<SortingState>
}
export const useTableSettingsStore = create<TableSettingsStore>()(
  persist(
    set => (
      {
        visibleColumns: DEFAULT_COLUMNS,
        tableDensity: 'comfortable',
        actionsSimplified: false,
        withPagination: true,
        sorting: [],
        pagination: {
          pageIndex: 0,
          pageSize: 50
        },
        setVisibleColumns: (visibleColumns: (keyof IncarnationBase)[]) => set(() => ({
          visibleColumns: INCARNATION_TABLE_COLUMNS.filter(x => visibleColumns.includes(x.id))
        })),
        setDensity: (tableDensity: TableDensity) => set(() => ({ tableDensity })),
        setActionsSimplified: (actionsSimplified: boolean) => set(() => ({ actionsSimplified })),
        setWithPagination: (withPagination: boolean) => set(() => ({ withPagination })),
        setColumnsSize: columns => set(state => {
          const visibleColumns = state.visibleColumns.map(x => {
            const column = columns.find(y => y.id === x.id)
            if (column) {
              return { ...x, size: column.width }
            }
            return x
          })
          return { visibleColumns }
        }),
        setPagination: pagination => set(() => ({ pagination })),
        setSorting: updater => set(state => {
          if (typeof updater === 'function') {
            const sorting = updater(state.sorting)
            return {
              sorting
            }
          }
          return {
            sorting: updater
          }
        })
      }
    ),
    {
      name: STORAGE_KEYS.TABLE
    }
  )
)

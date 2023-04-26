import { useMemo, useState } from 'react'
import { useTableSettingsStore } from '../../../stores/table-settings'
import { IncarnationBase } from '../../../interfaces/incarnations.types'
import { SortingState, createColumnHelper, getCoreRowModel, getPaginationRowModel, getSortedRowModel, useReactTable, TableOptions } from '@tanstack/react-table'
import { useIncarnationsData } from '../../../hooks/use-incarnations-data'
import { useCanShowVersionStore } from '../../../stores/show-version'
import { INCARNATION_TABLE_COLUMNS } from '../../../constants/incarnations.consts'
import { Link } from 'react-router-dom'
import { sortByTemplateVersion } from '../../../utils/search-incarnations'
import { IncarnationLinks } from '../parts/IncarnationLinks'

const columnHelper = createColumnHelper<IncarnationBase>()

const defineColumns = INCARNATION_TABLE_COLUMNS
  .filter(x => x.id !== 'templateVersion')
  .map(x => {
    switch (x.id) {
      case 'id':
        return columnHelper.display({
          ...x,
          cell: x => x.row.original.id
        })
      case 'incarnationRepository':
        return columnHelper.accessor('incarnationRepository', {
          ...x,
          cell: x => <Link to={`${x.row.original.id}`}>{x.row.original.incarnationRepository}</Link>
        })
      case 'createdAt':
        return columnHelper.accessor('createdAt', {
          ...x,
          cell: x => new Date(x.row.original.createdAt).toLocaleString()
        })
    }
    return columnHelper.accessor(x.id, x)
  })

const templateVersion = columnHelper.accessor(
  'templateVersion',
  {
    ...INCARNATION_TABLE_COLUMNS.find(x => x.id === 'templateVersion'),
    sortingFn: (a, b) => sortByTemplateVersion(a.original, b.original)
  }
)

export const useIncarnationsTable = (withPagination: boolean) => {
  const [sorting, setSorting] = useState<SortingState>([])
  const { canShow: templateVersionIsShown } = useCanShowVersionStore()

  const _actions = useMemo(() => columnHelper.display({
    id: 'actions',
    header: 'Actions',
    size: templateVersionIsShown ? 250 : 140,
    cell: x => {
      const incarnation = x.row.original
      return <IncarnationLinks
        id={incarnation.id}
        commitUrl={incarnation.commitUrl}
        mergeRequestUrl={incarnation.mergeRequestUrl} />
    }
  }), [templateVersionIsShown])

  const availableColumns = useMemo(
    () => templateVersionIsShown
      ? [...defineColumns, templateVersion]
      : [...defineColumns],
    [templateVersionIsShown]
  )

  const tableSettings = useTableSettingsStore()

  const columns = useMemo(
    () => [
      ...availableColumns.filter(x => {
        if (!x.id) return false // type narrowing
        return tableSettings.visibleColumns.includes(x.id as keyof IncarnationBase)
      }),
      _actions
    ],
    [availableColumns, tableSettings.visibleColumns]
  )

  const data = useIncarnationsData()

  const tableConfig: TableOptions<IncarnationBase> = {
    data,
    columns,
    state: {
      sorting
    },
    onSortingChange: setSorting,
    columnResizeMode: 'onChange',
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel()
  }
  if (withPagination) {
    tableConfig.getPaginationRowModel = getPaginationRowModel()
  }

  const table = useReactTable(tableConfig)
  return { table, data }
}

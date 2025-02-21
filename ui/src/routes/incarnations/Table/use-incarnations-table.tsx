import { useEffect, useMemo } from 'react'
import { useTableSettingsStore } from '../../../stores/table-settings'
import { IncarnationBase } from '../../../interfaces/incarnations.types'
import { createColumnHelper, getCoreRowModel, getPaginationRowModel, getSortedRowModel, useReactTable, TableOptions } from '@tanstack/react-table'
import { useIncarnationsData } from '../../../hooks/use-incarnations-data'
import { INCARNATION_TABLE_COLUMNS } from '../../../constants/incarnations.consts'
import { Link } from 'react-router-dom'
import { makeSortBySemVer } from '../../../utils/search-incarnations'
import { IncarnationLinks } from '../parts/IncarnationLinks'
import { useToolbarSearchStore } from '../../../stores/toolbar-search'
import { useColResizeBodyCursor } from '../../../hooks/use-col-resize-body-cursor'
import { useEventListener } from 'usehooks-ts'

const sortBySemVer = makeSortBySemVer('requestedVersion')

const columnHelper = createColumnHelper<IncarnationBase>()

const defineColumns = INCARNATION_TABLE_COLUMNS
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
      case 'requestedVersion':
        return columnHelper.accessor('requestedVersion', {
          ...x,
          sortingFn: (a, b) => sortBySemVer(a.original, b.original)
        })
    }
    return columnHelper.accessor(x.id, x)
  })

export const useIncarnationsTable = (withPagination: boolean) => {
  const _actions = useMemo(() => columnHelper.display({
    id: 'actions',
    header: 'Actions',
    size: 280,
    cell: x => {
      const incarnation = x.row.original
      return <IncarnationLinks
        id={incarnation.id}

        commitUrl={incarnation.commitUrl}
        mergeRequestUrl={incarnation.mergeRequestUrl} />
    }
  }), [])

  const {
    setColumnsSize,
    visibleColumns,
    pagination,
    setPagination,
    sorting,
    setSorting
  } = useTableSettingsStore()
  const visibleColumnsMap = useMemo(() => new Map(visibleColumns.map(x => [x.id, x])), [visibleColumns])

  const columns = useMemo(
    () => [
      ...defineColumns
        .filter(x => {
          if (!x.id) return false // type narrowing
          return visibleColumnsMap.has(x.id as keyof IncarnationBase)
        })
        .map(x => ({
          ...x,
          size: visibleColumnsMap.get(x.id as keyof IncarnationBase)?.size
        })),
      _actions
    ],
    [visibleColumns, _actions]
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
    getSortedRowModel: getSortedRowModel(),
    enableMultiSort: true,
    getRowId: x => `${x.id}`,
    defaultColumn: {
      size: 250,
      maxSize: 500
    }
  }
  if (withPagination) {
    tableConfig.getPaginationRowModel = getPaginationRowModel()
    tableConfig.autoResetPageIndex = false
    tableConfig.initialState = {
      pagination
    }
  }
  const table = useReactTable(tableConfig)
  useEffect(() => {
    setPagination(table.getState().pagination)
  }, [table.getState().pagination.pageSize, table.getState().pagination.pageIndex])
  const { search } = useToolbarSearchStore()
  useEffect(() => {
    if (withPagination && search) {
      table.resetPageIndex(true)
    }
  }, [search, withPagination, table.resetPageIndex])

  useColResizeBodyCursor()
  const handleBodyMouseup = () => {
    const columnsWidth = table.getAllColumns().map(x => ({
      id: x.id,
      width: x.getSize()
    }))
    setColumnsSize(columnsWidth)
  }
  useEventListener('mouseup', handleBodyMouseup)
  return { table, data }
}

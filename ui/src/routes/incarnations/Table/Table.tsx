import { useMemo, useRef, useState } from 'react'
import { createColumnHelper, useReactTable, getCoreRowModel, flexRender, SortingState, getSortedRowModel, Row } from '@tanstack/react-table'
import styled from '@emotion/styled'
import clsx from 'clsx'
import { Hug } from '../../../components/common/Hug/Hug'
import { IconButton } from '../../../components/common/IconButton/IconButton'
import { SortUp } from '../../../components/common/Icons/SortUp'
import { SortDown } from '../../../components/common/Icons/SortDown'
import { Sort } from '../../../components/common/Icons/Sort'
import { useCanShowVersionStore } from '../../../stores/show-version'
import { Link } from 'react-router-dom'
import { IncarnationLinks } from '../parts/IncarnationLinks'
import { sortByTemplateVersion } from '../../../utils/search-incarnations'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Resizer } from './parts/Resizer'
import { useColResizeBodyCursor } from '../../../hooks/use-col-resize-body-cursor'
import { useWindowSize } from 'usehooks-ts'
import { INCARNATION_TABLE_COLUMNS } from '../../../constants/incarnations.consts'
import { useTableSettingsStore } from '../../../stores/table-settings'
import { useIncarnationsData } from '../../../hooks/use-incarnations-data'
import { IncarnationBase } from '../../../interfaces/incarnations.types'

const OFFSET = 100

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

export const IncarnationsTable = () => {
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

  const tableSettingsStore = useTableSettingsStore()

  const columns = useMemo(
    () => [
      ...availableColumns.filter(x => {
        if (!x.id) return false // type narrowing
        return tableSettingsStore.visibleColumns.includes(x.id as keyof IncarnationBase)
      }),
      _actions
    ],
    [availableColumns, tableSettingsStore.visibleColumns]
  )

  const data = useIncarnationsData()

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting
    },
    onSortingChange: setSorting,
    columnResizeMode: 'onChange',
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel()
  })

  const tbodyElementRef = useRef<HTMLTableSectionElement>(null)

  const rowVirtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => tbodyElementRef.current,
    estimateSize: () => 48,
    overscan: 10
  })

  const { rows } = table.getRowModel()

  const { height: windowHeight } = useWindowSize()
  const height = useMemo(() => windowHeight - OFFSET, [windowHeight])
  useColResizeBodyCursor()
  return (
    <TableContainer>
      <div className="table">
        <div
          style={{
            height
          }}
          ref={tbodyElementRef}
          className="tbody-scroll-box">
          <div className="thead">
            {table.getHeaderGroups().map(headerGroup => (
              <div className="tr" key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <div
                    key={header.id}
                    style={makeColumnStyles(header.getSize())}
                    className={clsx(
                      'th',
                      header.column.getCanSort() && 'sortable',
                      `column-${header.column.id}`
                    )}>
                    <Hug flex={[
                      'aic',
                      header.column.getCanSort() ? 'jcfs' : 'jcfe'
                    ]}>
                      {header.isPlaceholder
                        ? null
                        : (
                          <>
                            <Hug
                              className="th-text"
                              mr={header.column.getCanSort() ? 4 : 0}
                              pr={header.column.id === 'actions' ? 20 : 0}>
                              <span>
                                {flexRender(header.column.columnDef.header, header.getContext())}
                              </span>
                            </Hug>
                            {header.column.getCanSort() && !header.column.getIsResizing() && (
                              <IconButton
                                onClick={header.column.getToggleSortingHandler()}
                                className={clsx('sort-icon', header.column.getIsSorted() && 'sorted')}
                                size="small"
                                flying>
                                {{
                                  asc: <SortUp />,
                                  desc: <SortDown />
                                }[header.column.getIsSorted() as string] ?? <Sort />}
                              </IconButton>
                            )}
                          </>
                        )
                      }
                    </Hug>
                    {header.column.getCanSort() && (
                      <Resizer
                        onMouseDown={header.getResizeHandler()}
                        onTouchStart={header.getResizeHandler()}
                        isResizing={header.column.getIsResizing()} />
                    )}
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div
            className="tbody"
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`
            }}>
            {rowVirtualizer.getVirtualItems().map(virtualRow => {
              const row = rows[virtualRow.index] as Row<IncarnationBase>
              return (
                <div
                  key={row.id}
                  className="tr"
                  style={{
                    height: `${virtualRow.size}px`,
                    transform: `translateY(${virtualRow.start + 40}px)`
                  }}>
                  {row.getVisibleCells().map(cell => (
                    <div
                      key={cell.id}
                      style={makeColumnStyles(cell.column.getSize())}
                      className={clsx(
                        'td',
                        ['id', 'actions'].some(x => x === cell.column.id) && 'text-right',
                        `column-${cell.column.id}`
                      )}>
                      <span>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </span>
                    </div>
                  ))}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </TableContainer>
  )
}

const makeColumnStyles = (width: number) => ({
  width,
  minWidth: width,
  maxWidth: width
})

const TableContainer = styled.div`
  position: relative;
  width: 100%;
  overflow: hidden;
  .table {
    display: block;
  }
  .sort-icon:not(.sorted) {
    opacity: 0;
  }
  .thead {
    position: sticky;
    top: 0;
    z-index: 1;
    height: 40px;
  }
  .tbody-scroll-box {
    position: relative;
    overflow: scroll;
  }
  .tbody {
    display: flex;
    flex-direction: column;
  }
  .tr {
    display: flex;
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
  }
  .th {
    position: relative;
    padding: 8px 16px;
    line-height: 24px;
    white-space: nowrap;
    user-select: none;
    text-align: left;
    background-color: var(--base-bg);
    width: 300px;
    font-weight: 500;
    overflow: hidden;
    &:hover .sort-icon {
      opacity: 1;
    }
  }
  .th-text {
    width: calc(100% - 32px);
    flex-shrink: 1;
    overflow: hidden;
    span {
      vertical-align: middle;
      display: inline-block;
      width: 100%;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
  .td {
    border-bottom: 1px solid ${x => x.theme.colors.grey};
    font-size: 14px;
    padding: 8px 16px;
    background-color: var(--base-bg);
    display: flex;
    align-items: center;
    height: 48px;
    span {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    &.column-actions {
      box-shadow: var(--actions-column-shadow);
    }
  }
  .text-right {
    text-align: right;
    justify-content: flex-end;
  }
  .column-actions {
    position: sticky;
    right: 0;
    .th-text {
      width: fit-content;
    }
  }
  .column-id {
    .th-text {
      width: fit-content;
    }
  }
`

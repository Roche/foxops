import { useEffect, useMemo, useRef } from 'react'
import { flexRender, Row } from '@tanstack/react-table'
import styled from '@emotion/styled'
import clsx from 'clsx'
import { Hug } from '../../../components/common/Hug/Hug'
import { IconButton } from '../../../components/common/IconButton/IconButton'
import { SortUp } from '../../../components/common/Icons/SortUp'
import { SortDown } from '../../../components/common/Icons/SortDown'
import { Sort } from '../../../components/common/Icons/Sort'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Resizer } from './parts/Resizer'
import { useColResizeBodyCursor } from '../../../hooks/use-col-resize-body-cursor'
import { useWindowSize } from 'usehooks-ts'
import { IncarnationBase } from '../../../interfaces/incarnations.types'
import { useIncarnationsTable } from './use-incarnations-table'
import { useTableSettingsStore } from '../../../stores/table-settings'

const OFFSET_DEFAULT = 100
const OFFSET_WITH_PAGINATION = 150

export const IncarnationsTable = () => {
  const { withPagination } = useTableSettingsStore()
  return withPagination
    ? <Table key="1" withPagination />
    : <Table key="2" withPagination={false} /> // added `key` for forcing rerender
}

export const Table = ({
  withPagination
}: { withPagination: boolean }) => {
  const { tableDensity } = useTableSettingsStore()
  const {
    table,
    data
  } = useIncarnationsTable(withPagination)

  const tbodyElementRef = useRef<HTMLTableSectionElement>(null)

  const isCompact = tableDensity === 'compact'

  const rowVirtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => tbodyElementRef.current,
    estimateSize: () => isCompact ? 36 : 48,
    overscan: 10
  })

  useEffect(() => {
    rowVirtualizer.measure()
  }, [tableDensity])

  const { rows } = table.getRowModel()

  const { height: windowHeight } = useWindowSize()
  const height = useMemo(() => windowHeight - (withPagination ? OFFSET_WITH_PAGINATION : OFFSET_DEFAULT), [windowHeight])
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
                      isCompact && 'compact',
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
          {
            withPagination
              ? (
                <div
                  className="tbody">
                  {table.getRowModel().rows.map(row => (
                    <div
                      key={row.id}
                      className="tr">
                      {row.getVisibleCells().map(cell => (
                        <div
                          key={cell.id}
                          style={makeColumnStyles(cell.column.getSize())}
                          className={clsx(
                            'td',
                            isCompact && 'compact',
                            ['id', 'actions'].some(x => x === cell.column.id) && 'text-right',
                            `column-${cell.column.id}`
                          )}>
                          {cell.column.id === 'actions'
                            ? flexRender(cell.column.columnDef.cell, cell.getContext())
                            : <span>{flexRender(cell.column.columnDef.cell, cell.getContext())}</span>}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              )
              : (
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
                        className="tr virtual"
                        style={{
                          height: `${virtualRow.size}px`,
                          transform: `translateY(${virtualRow.start + 48}px)`
                        }}>
                        {row.getVisibleCells().map(cell => (
                          <div
                            key={cell.id}
                            style={makeColumnStyles(cell.column.getSize())}
                            className={clsx(
                              'td',
                              isCompact && 'compact',
                              ['id', 'actions'].some(x => x === cell.column.id) && 'text-right',
                              `column-${cell.column.id}`
                            )}>
                            {cell.column.id === 'actions'
                              ? flexRender(cell.column.columnDef.cell, cell.getContext())
                              : <span>{flexRender(cell.column.columnDef.cell, cell.getContext())}</span>}
                          </div>
                        ))}
                      </div>
                    )
                  })}
                </div>
              )
          }
        </div>
        {withPagination && (
          <Hug flex my={8}>
            <Hug ml="auto" flex={['aic']} gap={8}>
              <Hug style={{ color: 'var(--grey-600)' }}>Per page</Hug>
              {[5, 10, 25, 50].map(x => {
                const perPage = table.getState().pagination.pageSize
                return (
                  <IconButton
                    key={x}
                    active={x === perPage}
                    onClick={() => table.setPageSize(x)}>
                    <span>{x}</span>
                  </IconButton>
                )
              })}
              <Hug ml={8} flex={['jcfe']} miw={150} style={{ color: 'var(--grey-600)' }}>
              Page {table.getState().pagination.pageIndex + 1} of{' '}
                {table.getPageCount()}</Hug>
              <IconButton
                onClick={() => table.setPageIndex(0)}
                disabled={!table.getCanPreviousPage()}>{'<<'}</IconButton>
              <IconButton
                onClick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}>{'<'}</IconButton>
              <IconButton
                onClick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}>{'>'}</IconButton>
              <IconButton
                onClick={() => table.setPageIndex(table.getPageCount() - 1)}
                disabled={!table.getCanNextPage()}
              >{'>>'}</IconButton>
            </Hug>
          </Hug>
        )}
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
    width: 100%;
    &.virtual {
      position: absolute;
      top: 0;
      left: 0;
    }
  }
  .th {
    position: relative;
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
    background-color: var(--base-bg);
    display: flex;
    align-items: center;
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
  .td, .th {
    padding: 8px 16px;
    height: 48px;
    &.compact {
      padding: 2px 8px;
      height: 36px;
    }
  }
`

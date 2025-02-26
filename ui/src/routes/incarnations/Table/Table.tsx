import { useEffect, useRef } from 'react'
import { flexRender, Row } from '@tanstack/react-table'
import clsx from 'clsx'
import { Hug } from '../../../components/common/Hug/Hug'
import { IconButton } from '../../../components/common/IconButton/IconButton'
import { SortUp } from '../../../components/common/Icons/SortUp'
import { SortDown } from '../../../components/common/Icons/SortDown'
import { Sort } from '../../../components/common/Icons/Sort'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Resizer } from './parts/Resizer'
import { IncarnationBase } from '../../../interfaces/incarnations.types'
import { useIncarnationsTable } from './use-incarnations-table'
import { useTableSettingsStore } from '../../../stores/table-settings'
import { TableContainer } from './parts/TableContainer'
import { Search } from '../parts/Search'
import { Settings } from '../parts/Settings'

export const IncarnationsTable = () => {
  const { withPagination } = useTableSettingsStore()
  return withPagination ? (
    <Table key="1" withPagination />
  ) : (
    <Table key="2" withPagination={false} />
  ) // added `key` for forcing rerender
}

export const Table = ({ withPagination }: { withPagination: boolean }) => {
  const { tableDensity } = useTableSettingsStore()
  const { table, data } = useIncarnationsTable(withPagination)

  const tbodyElementRef = useRef<HTMLTableSectionElement>(null)

  const isCompact = tableDensity === 'compact'

  const rowVirtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => tbodyElementRef.current,
    estimateSize: () => (isCompact ? 36 : 48),
    overscan: 10
  })

  useEffect(() => {
    if (!withPagination) rowVirtualizer.measure()
  }, [tableDensity])

  const { rows } = table.getRowModel()

  return (
    <TableContainer>
      <Hug h="4rem" flex={['aic', 'jcfe']} gap={8} pr={4}>
        <Search></Search>
        <Settings></Settings>
      </Hug>
      <div className="table">
        <div
          ref={tbodyElementRef}
          className="tbody-scroll-box"
        >
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
                    )}
                  >
                    <Hug
                      flex={[
                        'aic',
                        header.column.getCanSort() ? 'jcfs' : 'jcfe'
                      ]}
                    >
                      {header.isPlaceholder ? null : (
                        <>
                          <Hug
                            className="th-text"
                            mr={header.column.getCanSort() ? 4 : 0}
                            pr={header.column.id === 'actions' ? 20 : 0}
                          >
                            <span>
                              {flexRender(
                                header.column.columnDef.header,
                                header.getContext()
                              )}
                            </span>
                          </Hug>
                          {header.column.getCanSort()
                            && !header.column.getIsResizing() && (
                            <IconButton
                              onClick={header.column.getToggleSortingHandler()}
                              className={clsx(
                                'sort-icon',
                                header.column.getIsSorted() && 'sorted'
                              )}
                              size="small"
                              flying
                            >
                              {{
                                asc: <SortUp />,
                                desc: <SortDown />
                              }[header.column.getIsSorted() as string] ?? (
                                <Sort />
                              )}
                            </IconButton>
                          )}
                        </>
                      )}
                    </Hug>
                    {header.column.getCanSort() && (
                      <Resizer
                        onMouseDown={header.getResizeHandler()}
                        onTouchStart={header.getResizeHandler()}
                        isResizing={header.column.getIsResizing()}
                      />
                    )}
                  </div>
                ))}
              </div>
            ))}
          </div>
          {withPagination ? (
            <div className="tbody">
              {table.getRowModel().rows.map(row => (
                <div key={row.id} className="tr">
                  {row.getVisibleCells().map(cell => (
                    <div
                      key={cell.id}
                      style={makeColumnStyles(cell.column.getSize())}
                      className={clsx(
                        'td',
                        isCompact && 'compact',
                        ['id', 'actions'].some(x => x === cell.column.id)
                          && 'text-right',
                        `column-${cell.column.id}`
                      )}
                    >
                      {cell.column.id === 'actions' ? (
                        flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )
                      ) : (
                        <span>
                          {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext()
                          )}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ) : (
            <div
              className="tbody"
              style={{
                height: `${rowVirtualizer.getTotalSize()}px`
              }}
            >
              {rowVirtualizer.getVirtualItems().map(virtualRow => {
                const row = rows[virtualRow.index] as Row<IncarnationBase>
                return (
                  <div
                    key={row.id}
                    className="tr virtual"
                    style={{
                      height: `${virtualRow.size}px`
                    }}
                  >
                    {row.getVisibleCells().map(cell => (
                      <div
                        key={cell.id}
                        style={makeColumnStyles(cell.column.getSize())}
                        className={clsx(
                          'td',
                          isCompact && 'compact',
                          ['id', 'actions'].some(x => x === cell.column.id)
                            && 'text-right',
                          `column-${cell.column.id}`
                        )}
                      >
                        {cell.column.id === 'actions' ? (
                          flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext()
                          )
                        ) : (
                          <span>
                            {flexRender(
                              cell.column.columnDef.cell,
                              cell.getContext()
                            )}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )
              })}
            </div>
          )}
        </div>
        {withPagination && (
          <Hug flex my={8} mb="4rem">
            <Hug ml="auto" flex={['aic']} gap={8}>
              <Hug style={{ color: 'var(--grey-600)' }}>Per page</Hug>
              {[5, 10, 25, 50].map(x => {
                const perPage = table.getState().pagination.pageSize
                return (
                  <IconButton
                    key={x}
                    active={x === perPage}
                    onClick={() => table.setPageSize(x)}
                  >
                    <span>{x}</span>
                  </IconButton>
                )
              })}
              <Hug
                ml={8}
                flex={['jcfe']}
                miw={150}
                style={{ color: 'var(--grey-600)' }}
              >
                Page {table.getState().pagination.pageIndex + 1} of{' '}
                {table.getPageCount()}
              </Hug>
              <IconButton
                onClick={() => table.setPageIndex(0)}
                disabled={!table.getCanPreviousPage()}
              >
                {'<<'}
              </IconButton>
              <IconButton
                onClick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}
              >
                {'<'}
              </IconButton>
              <IconButton
                onClick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}
              >
                {'>'}
              </IconButton>
              <IconButton
                onClick={() => table.setPageIndex(table.getPageCount() - 1)}
                disabled={!table.getCanNextPage()}
              >
                {'>>'}
              </IconButton>
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

import styled from '@emotion/styled'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/common/Button/Button'
import { Hug } from '../../components/common/Hug/Hug'
import { IconButton } from '../../components/common/IconButton/IconButton'
import { Loader } from '../../components/common/Loader/Loader'
import { Incarnation, IncarnationBase, incarnations } from '../../services/incarnations'
import { useToolbarSearchStore } from '../../stores/toolbar-search'
import { Section } from './parts'
import { SortDown } from '../../components/common/Icons/SortDown'
import { SortUp } from '../../components/common/Icons/SortUp'
import { Sort } from '../../components/common/Icons/Sort'
import { IncarnationItem } from './Item'
import clsx from 'clsx'
import { CSSProperties, useEffect, useState } from 'react'
import { FixedSizeList } from 'react-window'
import { useCanShowVersionStore } from '../../stores/show-version'
import { useIncarnationsSortStore } from '../../stores/incarnations-sort'
import { searchSortIncarnations } from '../../utils/search-sort-incarnations'
import { IncarnationsSortBy } from '../../interfaces/incarnations.type'

const TableLike = styled(Hug)(({ theme }) => ({
  fontSize: 14,
  '.heading': {
    padding: 8,
    borderBottom: `1px solid ${theme.colors.grey}`,
    whiteSpace: 'nowrap',
    fontWeight: 700,
    textAlign: 'left',
    position: 'sticky',
    background: theme.colors.baseBg,
    zIndex: 4,
    fontSize: 16,
    top: theme.sizes.toolbar
  },
  '.heading:not(:hover) .sort-icon': {
    opacity: 0
  },
  '.heading.sorted .sort-icon': {
    opacity: 1
  }
}))

const NoResults = () => (
  <Hug p={8}>No incarnations found</Hug>
)

const OFFSET = 210

const getSingleIncarnations = (queryClient: ReturnType<typeof useQueryClient>) => {
  const singleIncarnationsMap = new Map<number, Incarnation>()
  queryClient
    .getQueriesData({
      predicate: query => query.queryKey[0] === 'incarnations' && query.queryKey.length === 2
    }).forEach(([, x]) => {
      const _x = x as Incarnation | undefined
      if (!_x) return
      singleIncarnationsMap.set(_x.id, _x)
    })
  return singleIncarnationsMap
}

export const IncarnationsList = () => {
  const { search } = useToolbarSearchStore()
  const queryClient = useQueryClient()
  const singleIncarnationsMap = getSingleIncarnations(queryClient)

  const { isLoading, isError, data, isSuccess } = useQuery(
    ['incarnations'],
    incarnations.get
  )
  let _data: IncarnationBase[] = (data || [] as IncarnationBase[])
    .map(x => singleIncarnationsMap.has(x.id)
      ? {
        ...x,
        templateVersion: singleIncarnationsMap.get(x.id)?.templateRepositoryVersion || ''
      } as IncarnationBase
      : x
    )

  const navigate = useNavigate()
  const pendingMessage = isLoading
    ? 'Loading...'
    : isError
      ? 'Error loading incarnations 😔'
      : null
  const { sort, asc, setSort } = useIncarnationsSortStore()

  _data = searchSortIncarnations(_data || [], { search, sort, asc })
  const onSort = (_sort: IncarnationsSortBy) => () => {
    if (sort === _sort) {
      setSort(_sort, !asc)
    } else {
      setSort(_sort, true)
    }
  }
  const anyStatusReceived = false

  const [height, setHeight] = useState(window.innerHeight - OFFSET)
  useEffect(() => {
    const onResize = () => {
      setHeight(window.innerHeight - OFFSET)
    }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const { canShow } = useCanShowVersionStore()

  const table = isSuccess && (
    <TableLike>
      <Hug flex={['ais']}>
        <Hug className="heading" flex={['aic', 'jcc']} allw={50}>Id</Hug>
        <Hug
          allw={`calc(100% - 50px - 280px - 218px${canShow ? ' - 200px' : ''})`}
          className={clsx('heading', sort === 'incarnationRepository' && 'sorted')}
          flex={['aic']}>
          <Hug mr={4}>Repository</Hug>
          <IconButton onClick={onSort('incarnationRepository')} className="sort-icon" size="small" flying>
            {sort === 'incarnationRepository' ? asc ? <SortDown /> : <SortUp /> : <Sort />}
          </IconButton>
        </Hug>
        <Hug allw={280} className={clsx('heading', sort === 'targetDirectory' && 'sorted')} flex={['aic']}>
          <Hug mr={4}>Target directory</Hug>
          <IconButton onClick={onSort('targetDirectory')} className="sort-icon" size="small" flying>
            {sort === 'targetDirectory' ? asc ? <SortDown /> : <SortUp /> : <Sort />}
          </IconButton>
        </Hug>
        {canShow && (
          <Hug allw={200} className="heading" flex={['aic']}>
            <Hug mr={4}>Template version</Hug>
            <IconButton onClick={onSort('templateVersion')} className="sort-icon" size="small" flying>
              {sort === 'templateVersion' ? asc ? <SortDown /> : <SortUp /> : <Sort />}
            </IconButton>
          </Hug>
        )}
        <Hug className="heading" allw={218}>
          {anyStatusReceived && 'Version'}
        </Hug>
      </Hug>
      <Hug>
        {_data.length
          ? (
            <FixedSizeList
              height={height}
              itemCount={_data.length}
              itemSize={41}
              itemData={_data}
              useIsScrolling
              itemKey={index => _data[index].id}
              width="100%">
              {Row}
            </FixedSizeList>
          )
          : <NoResults />}
      </Hug>
    </TableLike>
  )
  const onCreate = () => navigate('create')
  return (
    <Section>
      <Hug flex={['aic', 'jcsb']} pl={8}>
        <h3>Incarnations</h3>
        <Button onClick={onCreate}>Create</Button>
      </Hug>
      <Hug flex pl={8}>
        <Hug mr={4}>{pendingMessage}</Hug>
        {isLoading && <Loader />}
      </Hug>
      {table}
    </Section>
  )
}

interface RowProps {
  index: number
  style: CSSProperties
  data: IncarnationBase[],
  isScrolling?: boolean
}

const Row = ({ index, style, data, isScrolling }: RowProps) => (
  <div style={style}>
    <IncarnationItem incarnation={data[index]} isScrolling={!!isScrolling} />
  </div>
)

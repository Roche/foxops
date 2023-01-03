import styled from '@emotion/styled'
import { useQuery } from '@tanstack/react-query'
import create from 'zustand'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/common/Button/Button'
import { Hug } from '../../components/common/Hug/Hug'
import { IconButton } from '../../components/common/IconButton/IconButton'
import { Loader } from '../../components/common/Loader/Loader'
import { IncarnationBase, incarnations } from '../../services/incarnations'
import { useToolbarSearchStore } from '../../stores/toolbar-search'
import { searchBy } from '../../utils'
import { Section } from './parts'
import { SortDown } from '../../components/common/Icons/SortDown'
import { SortUp } from '../../components/common/Icons/SortUp'
import { Sort } from '../../components/common/Icons/Sort'
import { IncarnationItem } from './Item'
import clsx from 'clsx'
import { CSSProperties, useEffect, useState } from 'react'
import { FixedSizeList } from 'react-window'
import { useCanShowVersionStore } from '../../stores/show-version'

type SortBy = 'incarnationRepository' | 'targetDirectory'
interface SortStore {
  sort: SortBy,
  asc: boolean,
  setSort: (sort: SortBy, asc: boolean) => void,
}

const useSort = create<SortStore>()(set => ({
  sort: 'incarnationRepository',
  asc: true,
  setSort: (sort, asc) => set({ sort, asc })
}))

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

export const IncarnationsList = () => {
  const { search } = useToolbarSearchStore()
  const { isLoading, isError, data, isSuccess } = useQuery(['incarnations'], incarnations.get) // TODO: wrap it to useIncarnationsQuery
  const navigate = useNavigate()
  const pendingMessage = isLoading
    ? 'Loading...'
    : isError
      ? 'Error loading incarnations 😔'
      : null
  const { sort, asc, setSort } = useSort()
  const _data = Array.isArray(data)
    ? data.filter(searchBy<Partial<IncarnationBase>>(search, ['id', 'incarnationRepository', 'targetDirectory']))
      .sort((a, b) => {
        if (asc) {
          return a[sort].localeCompare(b[sort])
        }
        return b[sort].localeCompare(a[sort])
      })
    : []
  const onSort = (_sort: SortBy) => () => {
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
          <Hug allw={200} className="heading">
            Template version
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
              width="100%">
              {Row}
            </FixedSizeList>
          )
          : <NoResults />}
        {/* <FixedSizeList>
          {_data.length ? virtualRows.getVirtualItems().map(x => (
            <IncarnationItem key={x.key} incarnation={_data[x.index]} />
          )) : <NoResults />}
        </FixedSizeList> */}
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

const Row = ({ index, style, data }: { index: number, style: CSSProperties, data: IncarnationBase[] }) => (
  <div style={style}>
    <IncarnationItem incarnation={data[index]} />
  </div>
)

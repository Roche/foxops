import styled from '@emotion/styled'
import { useQuery } from '@tanstack/react-query'
import create from 'zustand'
import { useNavigate } from 'react-router-dom'
import { Button, ButtonLink } from '../../components/common/Button/Button'
import { FloatingActionButton } from '../../components/common/FloatingActionButton/FloatingActionButton'
import { Hug } from '../../components/common/Hug/Hug'
import { IconButton } from '../../components/common/IconButton/IconButton'
import { Commit } from '../../components/common/Icons/Commit'
import { MergeRequest } from '../../components/common/Icons/MergeRequest'
import { Loader } from '../../components/common/Loader/Loader'
import { Incarnation, incarnations } from '../../services/incarnations'
import { useToolbarSearchStore } from '../../stores/toolbar-search'
import { searchBy } from '../../utils'
import { Section } from './parts'
import { SortDown } from '../../components/common/Icons/SortDown'
import { SortUp } from '../../components/common/Icons/SortUp'
import { Sort } from '../../components/common/Icons/Sort'
import { Tooltip } from '../../components/common/Tooltip/Tooltip'

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

const Table = styled.table(({ theme }) => ({
  width: '100%',
  borderCollapse: 'collapse',
  tableLayout: 'fixed',
  fontSize: 14,
  'td, th': {
    padding: 8,
    borderBottom: `1px solid ${theme.colors.grey}`,
    whiteSpace: 'nowrap'
  },
  td: {
    padding: '4px 8px'
  },
  th: {
    fontWeight: 700,
    textAlign: 'left',
    position: 'sticky',
    background: theme.colors.baseBg,
    zIndex: 3,
    fontSize: 16,
    top: -16 // padding of Content component
  },
  'tr:last-child td': {
    borderBottom: 'none'
  },
  'th:not(:hover) .sort-icon': {
    opacity: 0
  },
  'th.sorted .sort-icon': {
    opacity: 1
  }
}))

const CellText = styled.div({
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  maxWidth: '100%'
})

const NoResults = () => (
  <tr><td colSpan={4}>No incarnations found</td></tr>
)

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
    ? data.filter(searchBy<Partial<Incarnation>>(search, ['incarnationRepository', 'targetDirectory']))
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
  const table = isSuccess && (
    <Table>
      <thead>
        <tr>
          <th style={{ width: 40 }}>Id</th>
          <th style={{ width: 'calc(50% - 40px - 218px)' }} className={sort === 'incarnationRepository' ? 'sorted' : ''}>
            Repository{' '}
            <IconButton onClick={onSort('incarnationRepository')} className="sort-icon" size="small" flying>
              {sort === 'incarnationRepository' ? asc ? <SortDown /> : <SortUp /> : <Sort />}
            </IconButton>
          </th>
          <th style={{ width: 'calc(50% - 40px - 218px)' }} className={sort === 'targetDirectory' ? 'sorted' : ''}>
            Target directory{' '}
            <IconButton onClick={onSort('targetDirectory')} className="sort-icon" size="small" flying>
              {sort === 'targetDirectory' ? asc ? <SortDown /> : <SortUp /> : <Sort />}
            </IconButton>
          </th>
          <th style={{ width: 218 }} />
        </tr>
      </thead>
      <tbody>
        {_data.length ? _data.map(x => (
          <tr key={x.id}>
            <td>{x.id}</td>
            <td>
              <Tooltip title={x.incarnationRepository}>
                <CellText>{x.incarnationRepository}</CellText>
              </Tooltip>
            </td>
            <td>
              <Tooltip title={x.targetDirectory}>
                <CellText>{x.targetDirectory}</CellText>
              </Tooltip>
            </td>
            <td>
              <Hug flex>
                <ButtonLink size="small" target="_blank" disabled={!x.commitUrl} href={x.commitUrl} title={x.commitUrl}>
                  <Hug as="span" mr={4}>Commit</Hug>
                  <Commit />
                </ButtonLink>
                <Hug ml={4}>
                  <ButtonLink size="small" target="_blank" disabled={!x.mergeRequestUrl} href={x.mergeRequestUrl ?? undefined} title={x.mergeRequestUrl ?? undefined}>
                    <Hug as="span" flex={['aic', 'jcsb']}>
                      <Hug as="span" mr={4}>Merge request</Hug>
                      <MergeRequest />
                    </Hug>
                  </ButtonLink>
                </Hug>
              </Hug>
            </td>
          </tr>
        )) : <NoResults />}
      </tbody>
    </Table>
  )
  const onCreate = () => navigate('create')
  return (
    <Section>
      <Hug flex={['aic', 'jcsb']}>
        <h3>Incarnations</h3>
        <Button onClick={onCreate}>Create</Button>
      </Hug>
      <Hug flex>
        <Hug mr={4}>{pendingMessage}</Hug>
        {isLoading && <Loader />}
      </Hug>
      {table}
      <FloatingActionButton onClick={onCreate} title="Create new incarnation" />
    </Section>
  )
}

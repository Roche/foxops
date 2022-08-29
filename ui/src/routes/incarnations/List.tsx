import styled from '@emotion/styled'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Button, ButtonLink } from '../../components/common/Button/Button'
import { FloatingActionButton } from '../../components/common/FloatingActionButton/FloatingActionButton'
import { Hug } from '../../components/common/Hug/Hug'
import { Commit } from '../../components/common/Icons/Commit'
import { MergeRequest } from '../../components/common/Icons/MergeRequest'
import { Loader } from '../../components/common/Loader/Loader'
import { incarnations } from '../../services/incarnations'
import { useToolbarSearchStore } from '../../stores/toolbar-search'
import { Section } from './parts'

const Table = styled.table(({ theme }) => ({
  width: '100%',
  borderCollapse: 'collapse',
  tableLayout: 'fixed',
  'td, th': {
    padding: 8,
    borderBottom: `1px solid ${theme.colors.grey}`,
    whiteSpace: 'nowrap'
  },
  th: {
    fontWeight: 700,
    textAlign: 'left',
    position: 'sticky',
    background: theme.colors.baseBg,
    zIndex: 3,
    top: -16 // padding of Content component
  },
  'tr:last-child td': {
    borderBottom: 'none'
  },
  'thead tr': {

  }
}))

const CellText = styled.div({
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  maxWidth: '100%'
})

export const IncarnationsList = () => {
  const { search } = useToolbarSearchStore()
  const { isLoading, isError, data, isSuccess } = useQuery(['incarnations'], incarnations.get) // TODO: wrap it to useIncarnationsQuery
  const navigate = useNavigate()
  const pendingMessage = isLoading
    ? 'Loading...'
    : isError
      ? 'Error loading incarnations 😔'
      : null
  const _data = Array.isArray(data) ? data.filter(({ incarnationRepository }) => incarnationRepository.toLowerCase().includes(search.toLowerCase())) : []
  const table = isSuccess && (
    <Table>
      <thead>
        <tr>
          <th style={{ width: 40 }}>Id</th>
          <th style={{ width: 'calc(50% - 40px - 218px)' }}>Repository</th>
          <th style={{ width: 'calc(50% - 40px - 218px)' }}>Target directory</th>
          <th style={{ width: 218 }} />
        </tr>
      </thead>
      <tbody>
        {_data.map(x => (
          <tr key={x.id}>
            <td>{x.id}</td>
            <td>
              <CellText>{x.incarnationRepository}</CellText>
            </td>
            <td>{x.targetDirectory}</td>
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
        ))}
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

import styled from '@emotion/styled'
import { useQuery } from '@tanstack/react-query'
import { incarnations } from '../../services/incarnations'

const Section = styled.div({
  maxWidth: 1200,
  margin: '0 auto',
  padding: 8
})

const Table = styled.table(({ theme }) => ({
  width: '100%',
  borderCollapse: 'collapse',
  'td, th': {
    padding: 8,
    borderBottom: `1px solid ${theme.colors.grey}`,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    maxWidth: '200px'
  },
  th: {
    fontWeight: 700,
    textAlign: 'left'
  },
  'tr:last-child td': {
    borderBottom: 'none'
  },
  'thead tr': {

  }
}))

export const IncarnationsList = () => {
  const { isLoading, isError, data } = useQuery(['incarnations'], incarnations.get) // TODO: wrap it to useIncarnationsQuery
  if (isLoading) {
    return <Section>Loading...</Section>
  }
  if (isError) {
    return <Section>Error loading incarnations 😔</Section>
  }
  return (
    <Section>
      <h3>Incarnations</h3>
      <Table>
        <thead>
          <tr>
            <th>Id</th>
            <th>Repository</th>
            <th>Target directory</th>
            <th>Commit</th>
            <th>Merge Request</th>
          </tr>
        </thead>
        <tbody>
          {data.map(x => (
            <tr key={x.id}>
              <td>{x.id}</td>
              <td>{x.incarnationRepository}</td>
              <td>{x.targetDirectory}</td>
              <td><a href={x.commitUrl} title={x.commitUrl} target="_blank" rel="noreferrer">{x.commitUrl}</a></td>
              <td>{x.mergeRequestUrl}</td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Section>
  )
}

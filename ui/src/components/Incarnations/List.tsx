import styled from '@emotion/styled'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../services/api'
import { incarnations } from '../../services/incarnations'
import { useAuthStore } from '../../stores/auth'

const Section = styled.div({
  maxWidth: 1200,
  margin: '0 auto',
  padding: 8
})

const Table = styled.table({
  width: '100%',
  borderCollapse: 'collapse',
  'td, th': {
    padding: 8,
    borderBottom: '1px solid var(--grey)'
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
})

export const IncarnationsList = () => {
  const { isLoading, isError, isSuccess, data } = useQuery(['incarnations'], incarnations.get) // TODO: wrap it to useIncarnationsQuery
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
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map(x => (
            <tr key={x.id}>
              <td>{x.id}</td>
              <td>{x.incarnationRepository}</td>
              <td>{x.targetDirectory}</td>
              <td>coming soon&hellip;</td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Section>
  )
}

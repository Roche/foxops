import styled from '@emotion/styled'
import { Link, useNavigate } from 'react-router-dom'
import { Hug } from '../../components/common/Hug/Hug'
import { IconButton } from '../../components/common/IconButton/IconButton'
import { ExpandLeft } from '../../components/common/Icons/ExpandLeft'
import { Loader } from '../../components/common/Loader/Loader'
import { useIncarnationsOperations } from '../../stores/incarnations-operations'
import { BulkForm } from './BulkForm'
import { Section } from './parts'
import { IncarnationLinks } from './parts/IncarnationLinks'

const Paper = styled.div`
  box-shadow: ${x => x.theme.effects.paperShadow};
  border-radius: 4px;
  padding: 16px;
  margin-bottom: 16px;
`
const FormContainer = styled.div`
  margin-left: -42px;
  width: calc(50% + 42px);
  position: sticky;
  top: 60px;
`

export const BulkUpdateIncarnations = () => {
  const navigate = useNavigate()
  const onBackClick = () => navigate('/incarnations')
  const { selectedIncarnations: incarnations } = useIncarnationsOperations()
  const { length } = incarnations
  const noIncarnations = 'No incarnations selected'
  const form = <BulkForm />
  const { updatingIds, updatedIds, failedUpdatedIds } = useIncarnationsOperations()
  return (
    <Section>
      <Hug flex={['aifs']}>
        <FormContainer>
          <Hug flex={['aic']}>
            <Hug mr={8}>
              <IconButton flying title="Go back" onClick={onBackClick}>
                <ExpandLeft />
              </IconButton>
            </Hug>
            <Hug flex={['aic']} w="100%">
              <h3>Bulk update {length} incarnation{length > 1 ? 's' : ''}</h3>
            </Hug>
          </Hug>
          <Hug ml={42} mr={32}>
            {length ? form : noIncarnations}
          </Hug>
        </FormContainer>
        <Hug w="50%" mt={16}>
          {incarnations.map(x => (
            <Paper key={x.id}>
              <Hug flex={['aic', 'jcsb']} my={8}>
                <Hug>
                  <strong>#{x.id}</strong>
                </Hug>
                <Hug flex={['aic']}>
                  {
                    updatingIds.includes(x.id) && !updatedIds.includes(x.id) && !failedUpdatedIds.includes(x.id)
                      ? (
                        <Hug flex h={32}>
                          <Hug mr={4}>Updating&hellip;</Hug>
                          <Loader />
                        </Hug>
                      )
                      : (
                        <IncarnationLinks
                          id={x.id}
                          commitUrl={x.commitUrl}
                          mergeRequestUrl={x.mergeRequestUrl}
                          templateRepository={x.templateRepository} />
                      )
                  }
                </Hug>
              </Hug>
              <Hug my={8}>
                <strong>Repository: </strong>
                <Link to={`/incarnations/${x.id}`}>{x.incarnationRepository}</Link>
              </Hug>
              <Hug my={8}><strong>Target directory: </strong> {x.targetDirectory}</Hug>
              <Hug my={8}><strong>Template version: </strong> {x.templateRepositoryVersion}</Hug>
            </Paper>
          ))}
        </Hug>
      </Hug>
    </Section>
  )
}

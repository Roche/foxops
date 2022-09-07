import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { Hug } from '../../components/common/Hug/Hug'
import { Loader } from '../../components/common/Loader/Loader'
import { Incarnation, IncarnationInput, incarnations } from '../../services/incarnations'
import { IncarnationsForm } from './Form'
import { Section } from './parts'

const toIncarnationInput = (x: Incarnation): IncarnationInput => ({
  repository: x.incarnationRepository,
  targetDirectory: x.targetDirectory,
  templateRepository: x.templateRepository,
  templateVersion: x.templateRepositoryVersion,
  templateData: Object.entries(x.templateData).map(([key, value]) => ({ key, value }))
})

export const EditIncarnationForm = () => {
  const { id } = useParams()
  const { isLoading, isError, data, isSuccess } = useQuery(['incarnations', id], () => incarnations.getById(id))
  if (!id) return null // narrowing for TS
  const pendingMessage = isLoading
    ? 'Loading...'
    : isError
      ? 'Error loading incarnation 😔'
      : null
  const body = isSuccess
    ? (
      <IncarnationsForm
        mutation={(x => incarnations.update(id, x))}
        defaultValues={toIncarnationInput(data)}
        isEdit />
    )
    : (
      <Section>
        <Hug flex pl={8}>
          <Hug mr={4}>{pendingMessage}</Hug>
          {isLoading && <Loader />}
        </Hug>
      </Section>
    )
  return body
}

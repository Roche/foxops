import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Hug } from '../../components/common/Hug/Hug'
import { Loader } from '../../components/common/Loader/Loader'
import { IncarnationInput, incarnations } from '../../services/incarnations'
import { useCanShowStatusStore } from '../../stores/show-status'
import { IncarnationsForm } from './Form'
import { Section } from './parts'
import { Incarnation } from '../../interfaces/incarnations.types'

const toIncarnationInput = (x: Incarnation): IncarnationInput => ({
  automerge: true,
  repository: x.incarnationRepository,
  targetDirectory: x.targetDirectory,
  templateRepository: x.templateRepository ?? '',
  templateVersion: x.templateRepositoryVersion ?? '',
  templateData: Object.entries(x.templateData).map(([key, value]) => ({ key, value }))
})

export const EditIncarnationForm = () => {
  const { id } = useParams()
  const { isLoading, isError, data, isSuccess } = useQuery(['incarnations', Number(id)], () => incarnations.getById(id))
  if (!id) return null // narrowing for TS
  const pendingMessage = isLoading
    ? 'Loading...'
    : isError
      ? 'Error loading incarnation 😔'
      : null
  const { setCanShow } = useCanShowStatusStore()
  useEffect(() => {
    if (!isSuccess) return
    setCanShow(true)
  }, [isSuccess, setCanShow])
  const body = isSuccess
    ? (
      <IncarnationsForm
        mergeRequestUrl={data.mergeRequestUrl}
        commitUrl={data.commitUrl}
        mutation={x => incarnations.update(id, x)}
        defaultValues={toIncarnationInput(data)}
        incarnationMergeRequestStatus={data.mergeRequestStatus}
        deleteIncarnation={() => incarnations.delete(id)}
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

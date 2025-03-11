import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo } from 'react'
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
  templateData: JSON.stringify(x.templateData, null, 2)
})

const countChanges = (diff: string) => {
  const lines = diff.split('\n')

  const added = lines.filter(x => x.startsWith('+')).length
  const removed = lines.filter(x => x.startsWith('-') && !x.startsWith('--')).length

  return { added, removed }
}

export const EditIncarnationForm = () => {
  const { id } = useParams()
  const { isLoading, isError, data, isSuccess } = useQuery(['incarnations', id], () => incarnations.getById(id))
  const { data: diff } = useQuery(['incarnation_diff', id], () => incarnations.getDiffToTemplate(id))

  const diffCount = useMemo(() => diff !== undefined ? countChanges(diff) : undefined, [diff])

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

  const resetIncarnation = async (incarnation: Incarnation) => {
    const latestChange = await incarnations.getIncarnationChange(incarnation.id, incarnation.revision)
    await incarnations.reset(incarnation.id, latestChange.requestedVersion, latestChange.requestedData)
  }

  const body = isSuccess ? (
    <IncarnationsForm
      templateDataFull={data.templateDataFull}
      mergeRequestUrl={data.mergeRequestUrl}
      commitUrl={data.commitUrl}
      mutation={x => incarnations.update(id, x)}
      defaultValues={toIncarnationInput(data)}
      incarnationMergeRequestStatus={data.mergeRequestStatus}
      deleteIncarnation={() => incarnations.delete(id)}
      resetIncarnation={() => resetIncarnation(data)}
      diffChanges={diffCount}
      isEdit
    />
  ) : (
    <Section>
      <Hug flex pl={8}>
        <Hug mr={4}>{pendingMessage}</Hug>
        {isLoading && <Loader />}
      </Hug>
    </Section>
  )
  return body
}

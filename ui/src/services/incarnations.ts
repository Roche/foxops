import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { Change, ChangeApiView, Incarnation, IncarnationApiInput, IncarnationApiView, IncarnationBase, IncarnationBaseApiView, IncarnationResetApiInput, IncarnationUpdateApiInput } from '../interfaces/incarnations.types'

export const INCARNATION_SEARCH_FIELDS: (keyof IncarnationBase)[] = [
  'id',
  'incarnationRepository',
  'targetDirectory',
  'templateRepository',
  'revision',
  'type',
  'requestedVersion',
  'createdAt',
  'commitSha',
  'commitUrl',
  'mergeRequestId',
  'mergeRequestUrl',
  'templateVersion'
]

export interface IncarnationInput {
  automerge: boolean,
  repository: string,
  targetDirectory: string,
  templateRepository: string,
  templateVersion: string,
  templateData: string
}

export interface IncarnationUpdateInput {
  templateVersion: string,
  automerge: boolean,
  templateData: string
}

export const convertToUiBaseIncarnation = (incarnation: IncarnationBaseApiView): IncarnationBase => ({
  id: incarnation.id,
  incarnationRepository: incarnation.incarnation_repository,
  targetDirectory: incarnation.target_directory,
  commitUrl: incarnation.commit_url,
  mergeRequestUrl: incarnation.merge_request_url,
  mergeRequestId: incarnation.merge_request_id,
  commitSha: incarnation.commit_sha,
  createdAt: incarnation.created_at,
  requestedVersion: incarnation.requested_version,
  revision: incarnation.revision,
  templateRepository: incarnation.template_repository,
  type: incarnation.type,
  revison: incarnation.revision,
  templateVersion: '' // UI only
})

const convertToUiIncarnation = (incarnation: IncarnationApiView): Incarnation => ({
  id: incarnation.id,
  incarnationRepository: incarnation.incarnation_repository,
  targetDirectory: incarnation.target_directory,
  commitSha: incarnation.commit_sha,
  commitUrl: incarnation.commit_url,
  mergeRequestId: incarnation.merge_request_id,
  mergeRequestUrl: incarnation.merge_request_url,
  status: incarnation.status,
  mergeRequestStatus: incarnation.merge_request_status,
  templateRepository: incarnation.template_repository,
  templateRepositoryVersion: incarnation.template_repository_version,
  templateRepositoryVersionHash: incarnation.template_repository_version_hash,
  templateData: incarnation.template_data ?? {},
  templateDataFull: incarnation.template_data_full ?? {},
  revision: incarnation.revision
})

const convertToApiInput = (incarnation: IncarnationInput): IncarnationApiInput => ({
  incarnation_repository: incarnation.repository,
  template_repository: incarnation.templateRepository,
  template_repository_version: incarnation.templateVersion,
  target_directory: incarnation.targetDirectory,
  template_data: JSON.parse(incarnation.templateData),
  automerge: false
})

const convertToApiUpdateInput = (incarnation: IncarnationInput): IncarnationUpdateApiInput => ({
  template_repository_version: incarnation.templateVersion,
  template_data: JSON.parse(incarnation.templateData),
  automerge: incarnation.automerge
})

const convertToUiChange = (incarnationChange: ChangeApiView): Change => ({
  id: incarnationChange.id,
  incarnationId: incarnationChange.incarnation_id,
  revision: incarnationChange.revision,
  requestedVersion: incarnationChange.requested_version,
  requestedVersionHash: incarnationChange.requested_version_hash,
  requestedData: incarnationChange.requested_data,
  templateDataFull: incarnationChange.template_data_full,
  createdAt: incarnationChange.created_at,
  commitSha: incarnationChange.commit_sha,
  mergeRequestId: incarnationChange.merge_request_id,
  mergeRequestBranchName: incarnationChange.merge_request_branch_name,
  mergeRequestStatus: incarnationChange.merge_request_status,
  type: incarnationChange.type
})

export const incarnations = {
  get: async () => {
    const apiIncarnations = await api.get<undefined, IncarnationBaseApiView[]>('/incarnations')
    return apiIncarnations.map(convertToUiBaseIncarnation)
  },
  create: async (incarnation: IncarnationInput) => {
    const incarnationApiInput = convertToApiInput(incarnation)
    return api.post<IncarnationApiInput, IncarnationApiView>('/incarnations', { body: incarnationApiInput })
  },
  update: async (id: string | number, incarnation: IncarnationInput) => {
    const incarnationApiInput = convertToApiUpdateInput(incarnation)
    return api.put<IncarnationUpdateApiInput, IncarnationApiView>(`/incarnations/${id}`, { body: incarnationApiInput })
  },
  updateTemplateVersion: async (incarnation: Incarnation, input: Pick<IncarnationInput, 'automerge' | 'templateVersion'>) => {
    const incarnationApiInput: IncarnationUpdateApiInput = {
      automerge: input.automerge,
      template_repository_version: input.templateVersion,
      template_data: incarnation.templateData
    }
    const data = await api.put<IncarnationUpdateApiInput, IncarnationApiView>(`/incarnations/${incarnation.id}`, { body: incarnationApiInput })
    return convertToUiIncarnation(data)
  },

  getById: async (id?: number | string) => {
    if (!id) throw new Error('No id provided')
    const apiIncarnation = await api.get<undefined, IncarnationApiView>(`/incarnations/${id}`)
    return convertToUiIncarnation(apiIncarnation)
  },
  delete: async (id?: number | string) => {
    if (!id) throw new Error('No id provided')
    await api.delete<undefined, undefined>(`/incarnations/${id}`, { format: 'text' })
  },
  getDiffToTemplate: async (id?: number | string) => {
    if (!id) throw new Error('No id provided')
    return api.get<undefined, string>(`/incarnations/${id}/diff`, { format: 'text' })
  },
  reset: async (id: number | string, requestedVersion: string, requestedData: Record<string, string>) => {
    await api.post<IncarnationResetApiInput, undefined>(`/incarnations/${id}/reset`, { body: { requested_version: requestedVersion, requested_data: requestedData } })
  },
  getIncarnationChange: async (id: number | string, revisionVersion: number | string) => {
    const change = await api.get<undefined, ChangeApiView>(`/incarnations/${id}/changes/${revisionVersion}`)
    return convertToUiChange(change)
  }
}

export const useIncarnationsQuery = () => useQuery({
  queryKey: ['incarnations'],
  queryFn: incarnations.get,
  refetchOnWindowFocus: false
})

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

export const convertToUiBaseIncarnation = (x: IncarnationBaseApiView): IncarnationBase => ({
  id: x.id,
  incarnationRepository: x.incarnation_repository,
  targetDirectory: x.target_directory,
  commitUrl: x.commit_url,
  mergeRequestUrl: x.merge_request_url,
  mergeRequestId: x.merge_request_id,
  commitSha: x.commit_sha,
  createdAt: x.created_at,
  requestedVersion: x.requested_version,
  revision: x.revision,
  templateRepository: x.template_repository,
  type: x.type,
  revison: x.revision,
  templateVersion: '' // UI only
})

const convertToUiIncarnation = (x: IncarnationApiView): Incarnation => ({
  id: x.id,
  incarnationRepository: x.incarnation_repository,
  targetDirectory: x.target_directory,
  commitSha: x.commit_sha,
  commitUrl: x.commit_url,
  mergeRequestId: x.merge_request_id,
  mergeRequestUrl: x.merge_request_url,
  status: x.status,
  mergeRequestStatus: x.merge_request_status,
  templateRepository: x.template_repository,
  templateRepositoryVersion: x.template_repository_version,
  templateRepositoryVersionHash: x.template_repository_version_hash,
  templateData: x.template_data ?? {},
  templateDataFull: x.template_data_full ?? {},
  revision: x.revision
})

const convertToApiInput = (x: IncarnationInput): IncarnationApiInput => ({
  incarnation_repository: x.repository,
  template_repository: x.templateRepository,
  template_repository_version: x.templateVersion,
  target_directory: x.targetDirectory,
  template_data: JSON.parse(x.templateData),
  automerge: false
})

const convertToApiUpdateInput = (x: IncarnationInput): IncarnationUpdateApiInput => ({
  template_repository_version: x.templateVersion,
  template_data: JSON.parse(x.templateData),
  automerge: x.automerge
})

const convertToUiChange = (x: ChangeApiView): Change => ({
  id: x.id,
  incarnationId: x.incarnation_id,
  revision: x.revision,
  requestedVersion: x.requested_version,
  requestedVersionHash: x.requested_version_hash,
  requestedData: x.requested_data,
  templateDataFull: x.template_data_full,
  createdAt: x.created_at,
  commitSha: x.commit_sha,
  mergeRequestId: x.merge_request_id,
  mergeRequestBranchName: x.merge_request_branch_name,
  mergeRequestStatus: x.merge_request_status,
  type: x.type
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
  reset: async (id?: number | string, requestedVersion?: string, requestedData?: Record<string, string>) => {
    if (!id) throw new Error('No id provided')
    if (!requestedVersion) throw new Error('No requestedVersion provided')
    if (!requestedData) throw new Error('No requestedData provided')
    await api.post<IncarnationResetApiInput, undefined>(`/incarnations/${id}/reset`, { body: { requested_version: requestedVersion, requested_data: requestedData } })
  },
  getIncarnationChange: async (id?: number | string, revisionVersion?: number | string) => {
    if (!id) throw new Error('No id provided')
    if (!revisionVersion) throw new Error('No revisionVersion provided')
    const change = await api.get<undefined, ChangeApiView>(`/incarnations/${id}/changes/${revisionVersion}`)
    return convertToUiChange(change)
  }
}

export const useIncarnationsQuery = () => useQuery({
  queryKey: ['incarnations'],
  queryFn: incarnations.get,
  refetchOnWindowFocus: false
})

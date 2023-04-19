import { api } from '../services/api'

export interface IncarnationBaseApiView {
  id: number,
  incarnation_repository: string,
  target_directory: string,
  commit_url: string,
  commit_sha: string,
  merge_request_id: null | string,
  merge_request_url: null | string
}

export type MergeRequestStatus = 'open' | 'merged' | 'closed' | 'unknown'

export interface IncarnationApiView extends IncarnationBaseApiView {
  template_repository: string | null,
  template_repository_version: string | null,
  template_repository_version_hash: string | null,
  template_data: Record<string, string> | null,
  merge_request_id: string | null
  merge_request_url: string | null
  merge_request_status: MergeRequestStatus | null
}

export interface IncarnationBase {
  id: number,
  incarnationRepository: string,
  targetDirectory: string,
  commitUrl: string,
  mergeRequestUrl: null | string,
  templateVersion: string // UI only
}

export interface Incarnation extends IncarnationBase {
  templateRepository: string | null,
  templateRepositoryVersion: string | null,
  templateRepositoryVersionHash: string | null,
  templateData: Record<string, string>,
  mergeRequestId: string | null,
  mergeRequestUrl: string | null,
  mergeRequestStatus: MergeRequestStatus | null,
}

export interface IncarnationInput {
  automerge: boolean,
  repository: string,
  targetDirectory: string,
  templateRepository: string,
  templateVersion: string,
  templateData: {
    key: string,
    value: string,
  }[]
}

export interface IncarnationUpdateInput {
  templateVersion: string,
  automerge: boolean,
  templateData: {
    key: string,
    value: string,
  }[]
}

export const convertToUiBaseIncarnation = (x: IncarnationBaseApiView): IncarnationBase => ({
  id: x.id,
  incarnationRepository: x.incarnation_repository,
  targetDirectory: x.target_directory,
  commitUrl: x.commit_url,
  mergeRequestUrl: x.merge_request_url,
  templateVersion: '' // UI only
})

const convertToUiIncarnation = (x: IncarnationApiView): Incarnation => ({
  ...convertToUiBaseIncarnation(x),
  templateRepository: x.template_repository,
  templateRepositoryVersion: x.template_repository_version,
  templateRepositoryVersionHash: x.template_repository_version_hash,
  templateData: x.template_data ?? {},
  mergeRequestId: x.merge_request_id,
  mergeRequestUrl: x.merge_request_url,
  mergeRequestStatus: x.merge_request_status
})

interface IncarnationApiInput {
  incarnation_repository: string,
  template_repository: string,
  template_repository_version: string,
  target_directory: string,
  template_data: Record<string, string>,
  automerge: boolean
}

const convertToApiInput = (x: IncarnationInput): IncarnationApiInput => ({
  incarnation_repository: x.repository,
  template_repository: x.templateRepository,
  template_repository_version: x.templateVersion,
  target_directory: x.targetDirectory,
  template_data: x.templateData.reduce((acc, { key, value }) => {
    acc[key] = value
    return acc
  }, {} as Record<string, string>),
  automerge: false
})

interface IncarnationUpdateApiInput {
  template_repository_version: string,
  template_data: Record<string, string>,
  automerge: boolean
}

const convertToApiUpdateInput = (x: IncarnationInput): IncarnationUpdateApiInput => ({
  template_repository_version: x.templateVersion,
  template_data: x.templateData.reduce((acc, { key, value }) => {
    acc[key] = value
    return acc
  }, {} as Record<string, string>),
  automerge: x.automerge
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
  }
}

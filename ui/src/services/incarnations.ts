import { api } from '../services/api'

interface IncarnationApiView {
  id: number,
  incarnation_repository: string,
  target_directory: string,
  commit_url: string,
  merge_request_url: null | string
}

export interface Incarnation {
  id: number,
  incarnationRepository: string,
  targetDirectory: string,
  commitUrl: string,
  mergeRequestUrl: null | string,
}

export interface IncarnationInput {
  repository: string,
  targetDirectory: string,
  templateRepository: string,
  templateVersion: string,
  templateData: {
    key: string,
    value: string,
  }[]
}

const convertToUiIncarnation = (x: IncarnationApiView): Incarnation => ({
  id: x.id,
  incarnationRepository: x.incarnation_repository,
  targetDirectory: x.target_directory,
  commitUrl: x.commit_url,
  mergeRequestUrl: x.merge_request_url
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
// const mockedIncarnations = new Array(10).fill(0).map((_, i) => {
//   const x: number = i + 1
//   return {
//     id: x,
//     incarnation_repository: `Repository ${x}`,
//     target_directory: `Target ${x}`,
//     commit_url: `https://code.roche.com/navify-anywhere/limbo/demo-app/-/commit/${x}`,
//     merge_request_url: null
//   } as IncarnationApiView
// })

export const incarnations = {
  get: async () => {
    const apiIncarnations = await api.get<undefined, IncarnationApiView[]>('/incarnations')
    return apiIncarnations.map(convertToUiIncarnation)
  },
  create: async (incarnation: IncarnationInput) => {
    const incarnationApiInput = convertToApiInput(incarnation)
    return api.post<IncarnationApiInput, IncarnationApiView>('/incarnations', { body: incarnationApiInput })
    // return convertToUiIncarnation(apiIncarnation)
  }
}

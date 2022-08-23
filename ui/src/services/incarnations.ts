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
  mergeRequestUrl: null | string
}

const convertToUiIncarnation = (x: IncarnationApiView): Incarnation => ({
  id: x.id,
  incarnationRepository: x.incarnation_repository,
  targetDirectory: x.target_directory,
  commitUrl: x.commit_url,
  mergeRequestUrl: x.merge_request_url
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
    const apiIncarnations = await api.get<undefined, IncarnationApiView[]>({ url: '/incarnations' })
    return apiIncarnations.map(convertToUiIncarnation)
  }
}

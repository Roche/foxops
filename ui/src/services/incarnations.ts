import { api } from '../services/api'

interface IncarnationBasic {
  id: number,
  incarnation_repository: string,
  target_directory: string,
}

interface Incarnation {
  id: number,
  incarnationRepository: string,
  targetDirectory: string
}

const convertToUiIncarnation = (x: IncarnationBasic): Incarnation => ({
  id: x.id,
  incarnationRepository: x.incarnation_repository,
  targetDirectory: x.target_directory
})

export const incarnations = {
  get: async () => {
    const apiIncarnations = await api.get<undefined, IncarnationBasic[]>({ url: '/incarnations' })
    return apiIncarnations.map(convertToUiIncarnation)
  }
}

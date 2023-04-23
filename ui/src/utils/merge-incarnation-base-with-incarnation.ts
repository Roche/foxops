import { Incarnation, IncarnationBase } from '../interfaces/incarnations.types'

export const mergeIncarnationBaseWithIncarnation = (incarnationBase: IncarnationBase, incarnation: Incarnation): IncarnationBase => ({
  ...incarnationBase,
  templateVersion: incarnation.templateRepositoryVersion
})

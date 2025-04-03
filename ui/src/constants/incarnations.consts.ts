import { Paths } from 'shared/types'
import { IncarnationBase } from '../interfaces/incarnations.types'

export interface IncarnationTableColumn {
  id: Paths<IncarnationBase>, // keyof doesn't apply to nested objects!
  header: string,
  size: number,
  minSize?: number
}

const makeColumn = (config: Pick<IncarnationTableColumn, 'id' | 'header'> & Partial<Pick<IncarnationTableColumn, 'size' | 'minSize'>>) => ({
  size: 250,
  minSize: 80,
  ...config
})
export const INCARNATION_TABLE_COLUMNS: IncarnationTableColumn[] = [
  makeColumn({
    header: 'Id',
    id: 'id',
    size: 100,
    minSize: 100
  }),
  makeColumn({
    header: 'Incarnation Repository',
    id: 'incarnationRepository',
    size: 250,
    minSize: 100
  }),
  makeColumn({
    header: 'Template Repository',
    id: 'templateRepository',
    size: 250,
    minSize: 100
  }),
  makeColumn({
    header: 'Target Directory',
    id: 'targetDirectory',
    size: 250,
    minSize: 100
  }),
  makeColumn({
    header: 'Revision',
    id: 'revision',
    size: 250,
    minSize: 100
  }),
  makeColumn({
    header: 'Type',
    id: 'type',
    size: 250,
    minSize: 100
  }),
  makeColumn({
    header: 'Requested Version',
    id: 'requestedVersion',
    size: 250,
    minSize: 100
  }),
  makeColumn({
    header: 'Created At',
    id: 'createdAt',
    size: 250,
    minSize: 100
  }),
  makeColumn({
    header: 'Commit Sha',
    id: 'commitSha',
    size: 250,
    minSize: 100
  }),
  makeColumn({
    header: 'Commit Url',
    id: 'commitUrl',
    size: 250,
    minSize: 100
  }),
  makeColumn({
    header: 'Merge Request Id',
    id: 'mergeRequestId',
    size: 250,
    minSize: 100
  }),
  makeColumn({
    header: 'Merge Request Url',
    id: 'mergeRequestUrl',
    size: 250,
    minSize: 100
  }),
  makeColumn({
    header: 'Owner',
    id: 'owner.username',
    size: 250,
    minSize: 100
  })
]

import { IncarnationBase } from '../interfaces/incarnations.types'

export interface IncarnationTableColumn {
  id: keyof IncarnationBase,
  header: string,
  size: number,
  minSize?: number
}
const makeColumn = (config: Pick<IncarnationTableColumn, 'id' | 'header'> & Partial<Pick<IncarnationTableColumn, 'size' | 'minSize'>>) => ({
  size: 300,
  minSize: 80,
  ...config
})
export const INCARNATION_TABLE_COLUMNS: IncarnationTableColumn[] = [
  makeColumn({
    header: 'Id',
    id: 'id',
    size: 70,
    minSize: 70
  }),
  makeColumn({
    header: 'Incarnation Repository',
    id: 'incarnationRepository',
    size: 500
  }),
  makeColumn({
    header: 'Template Repository',
    id: 'templateRepository',
    size: 500
  }),
  makeColumn({
    header: 'Target Directory',
    id: 'targetDirectory'
  }),
  makeColumn({
    header: 'Revision',
    id: 'revision',
    size: 150
  }),
  makeColumn({
    header: 'Type',
    id: 'type'
  }),
  makeColumn({
    header: 'Requested Version',
    id: 'requestedVersion',
    size: 400
  }),
  makeColumn({
    header: 'Created At',
    id: 'createdAt'
  }),
  makeColumn({
    header: 'Commit Sha',
    id: 'commitSha'
  }),
  makeColumn({
    header: 'Commit Url',
    id: 'commitUrl'
  }),
  makeColumn({
    header: 'Merge Request Id',
    id: 'mergeRequestId'
  }),
  makeColumn({
    header: 'Merge Request Url',
    id: 'mergeRequestUrl'
  })
]

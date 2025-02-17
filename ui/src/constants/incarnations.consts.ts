import { IncarnationBase } from '../interfaces/incarnations.types'

export interface IncarnationTableColumn {
  id: keyof IncarnationBase,
  header: string,
  size: number,
  minSize?: number
}

export const MAGIC_COLUMN_SIZE_NUMBER = Math.round(Number.MAX_SAFE_INTEGER / 2)

const makeColumn = (config: Pick<IncarnationTableColumn, 'id' | 'header'> & Partial<Pick<IncarnationTableColumn, 'size' | 'minSize'>>) => ({
  size: 300,
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
    size: MAGIC_COLUMN_SIZE_NUMBER,
    minSize: MAGIC_COLUMN_SIZE_NUMBER - 250
  }),
  makeColumn({
    header: 'Template Repository',
    id: 'templateRepository',
    size: MAGIC_COLUMN_SIZE_NUMBER,
    minSize: MAGIC_COLUMN_SIZE_NUMBER - 250
  }),
  makeColumn({
    header: 'Target Directory',
    id: 'targetDirectory',
    size: MAGIC_COLUMN_SIZE_NUMBER,
    minSize: MAGIC_COLUMN_SIZE_NUMBER - 250
  }),
  makeColumn({
    header: 'Revision',
    id: 'revision',
    size: MAGIC_COLUMN_SIZE_NUMBER,
    minSize: MAGIC_COLUMN_SIZE_NUMBER - 250
  }),
  makeColumn({
    header: 'Type',
    id: 'type',
    size: MAGIC_COLUMN_SIZE_NUMBER,
    minSize: MAGIC_COLUMN_SIZE_NUMBER - 250
  }),
  makeColumn({
    header: 'Requested Version',
    id: 'requestedVersion',
    size: MAGIC_COLUMN_SIZE_NUMBER,
    minSize: MAGIC_COLUMN_SIZE_NUMBER - 250
  }),
  makeColumn({
    header: 'Created At',
    id: 'createdAt',
    size: MAGIC_COLUMN_SIZE_NUMBER,
    minSize: MAGIC_COLUMN_SIZE_NUMBER - 250
  }),
  makeColumn({
    header: 'Commit Sha',
    id: 'commitSha',
    size: MAGIC_COLUMN_SIZE_NUMBER,
    minSize: MAGIC_COLUMN_SIZE_NUMBER - 250
  }),
  makeColumn({
    header: 'Commit Url',
    id: 'commitUrl',
    size: MAGIC_COLUMN_SIZE_NUMBER,
    minSize: MAGIC_COLUMN_SIZE_NUMBER - 250
  }),
  makeColumn({
    header: 'Merge Request Id',
    id: 'mergeRequestId',
    size: MAGIC_COLUMN_SIZE_NUMBER,
    minSize: MAGIC_COLUMN_SIZE_NUMBER - 250
  }),
  makeColumn({
    header: 'Merge Request Url',
    id: 'mergeRequestUrl',
    size: MAGIC_COLUMN_SIZE_NUMBER,
    minSize: MAGIC_COLUMN_SIZE_NUMBER - 250
  })
]

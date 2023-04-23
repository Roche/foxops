import { IncarnationBase } from '../interfaces/incarnations.types'

export interface IncarnationTableColumn {
  id: keyof IncarnationBase,
  header: string,
  size: number,
  minSize?: number
}
export const INCARNATION_TABLE_COLUMNS: IncarnationTableColumn[] = [
  {
    id: 'id',
    header: 'Id',
    size: 70
  },
  {
    header: 'Incarnation Repository',
    id: 'incarnationRepository',
    size: 300,
    minSize: 80
  },
  {
    header: 'Template Repository',
    id: 'templateRepository',
    size: 300,
    minSize: 80
  },
  {
    header: 'Target Directory',
    id: 'targetDirectory',
    size: 300,
    minSize: 80
  },
  {
    header: 'Revision',
    id: 'revision',
    size: 300,
    minSize: 80
  },
  {
    header: 'Type',
    id: 'type',
    size: 300,
    minSize: 80
  },
  {
    header: 'Requested Version',
    id: 'requestedVersion',
    size: 300,
    minSize: 80
  },
  {
    header: 'Created At',
    id: 'createdAt',
    size: 300,
    minSize: 80
  },
  {
    header: 'Commit Sha',
    id: 'commitSha',
    size: 300,
    minSize: 80
  },
  {
    header: 'Commit Url',
    id: 'commitUrl',
    size: 300,
    minSize: 80
  },
  {
    header: 'Merge Request Id',
    id: 'mergeRequestId',
    size: 300,
    minSize: 80
  },
  {
    header: 'Merge Request Url',
    id: 'mergeRequestUrl',
    size: 300,
    minSize: 80
  },
  {
    header: 'Template Version',
    id: 'templateVersion',
    size: 300
  }
]

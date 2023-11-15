export interface IncarnationBaseApiView {
  id: number,
  incarnation_repository: string,
  target_directory: string,
  template_repository: null | string,
  revision: number,
  type: string,
  requested_version: null | string,
  created_at: string,
  commit_sha: string,
  commit_url: string,
  merge_request_id: null | string,
  merge_request_url: null | string
}

export type MergeRequestStatus = 'open' | 'merged' | 'closed' | 'unknown'

export interface IncarnationBase {
  id: number,
  incarnationRepository: string,
  targetDirectory: string,
  templateRepository: null | string,
  revision: number,
  type: string,
  requestedVersion: null | string,
  createdAt: string,
  commitSha: string,
  commitUrl: string,
  mergeRequestId: null | string,
  mergeRequestUrl: null | string
  templateVersion: string // UI only
}
export interface IncarnationApiView {
  id: number,
  incarnation_repository: string,
  target_directory: string,
  commit_sha: string,
  commit_url: string,
  merge_request_id: string | null,
  merge_request_url: string | null,
  status: string,
  merge_request_status: MergeRequestStatus | null,
  template_repository: string
  template_repository_version: string
  template_repository_version_hash: string
  template_data: Record<string, string> | null,
  template_data_full: Record<string, never> | null,
}
export interface Incarnation {
  id: number,
  incarnationRepository: string,
  targetDirectory: string,
  commitSha: string,
  commitUrl: string,
  mergeRequestId: string | null,
  mergeRequestUrl: string | null,
  status: string,
  mergeRequestStatus: MergeRequestStatus | null,
  templateRepository: string,
  templateRepositoryVersion: string,
  templateRepositoryVersionHash: string,
  templateData: Record<string, string>,
  templateDataFull: Record<string, never>
}

export interface IncarnationUpdateApiInput {
  template_repository_version: string,
  template_data: Record<string, string>,
  automerge: boolean
}

export interface IncarnationApiInput {
  incarnation_repository: string,
  template_repository: string,
  template_repository_version: string,
  target_directory: string,
  template_data: Record<string, string>,
  automerge: boolean
}

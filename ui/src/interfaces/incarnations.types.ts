import { Group, GroupApiView } from './group.types'
import { User, UserApiView } from './user.types'

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
export type ChangeType = 'merge_request' | 'direct'

export interface IncarnationBase {
  id: number,
  incarnationRepository: string,
  targetDirectory: string,
  templateRepository: null | string,
  revision: number,
  type: string,
  revison: number,
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
  revision: number
  merge_request_status: MergeRequestStatus | null,
  template_repository: string
  template_repository_version: string
  template_repository_version_hash: string
  template_data: Record<string, string> | null,
  template_data_full: Record<string, never> | null,
  owner: User,
  user_permissions: IncarnationUserPermissionApiView[],
  group_permissions: IncarnationGroupPermissionApiView[],
  current_user_permissions: IncarnationPermissionsAPIView,

}

export interface ChangeApiView {
  id: number,
  type: ChangeType,
  incarnation_id: number,
  revision: number,
  requested_version: string,
  requested_version_hash: string,
  requested_data: Record<string, string>,
  template_data_full: Record<string, never>,
  created_at: string,
  commit_sha: string,
  merge_request_id: string | null,
  merge_request_branch_name: string | null,
  merge_request_status: MergeRequestStatus | null,
}

export interface Change {
  id: number,
  type: ChangeType,
  incarnationId: number,
  revision: number,
  requestedVersion: string,
  requestedVersionHash: string,
  requestedData: Record<string, string>,
  templateDataFull: Record<string, never>,
  createdAt: string,
  commitSha: string,
  mergeRequestId: string | null,
  mergeRequestBranchName: string | null,
  mergeRequestStatus: MergeRequestStatus | null,
}

export interface IncarnationResetApiInput {
  requested_version: string,
  requested_data: Record<string, string>
}

export interface IncarnationUserPermission{
  user: User,
  type: 'write' | 'read',
}

export interface IncarnationGroupPermission{
  group: Group,
  type: 'write' | 'read',
}

export interface IncarnationGroupPermissionApiView{
  group: GroupApiView,
  type: 'write' | 'read',
}

export interface IncarnationUserPermissionApiView{
  user: UserApiView,
  type: 'write' | 'read',
}

export interface IncarnationPermissionsAPIView {
  can_read: boolean,
  can_update: boolean,
  can_reset: boolean,
  can_delete: boolean,
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
  revision: number,
  mergeRequestStatus: MergeRequestStatus | null,
  templateRepository: string,
  templateRepositoryVersion: string,
  templateRepositoryVersionHash: string,
  templateData: Record<string, string>,
  templateDataFull: Record<string, never>,
  owner: User,
  userPermissions: IncarnationUserPermission[],
  groupPermissions: IncarnationGroupPermission[],
  currentUserPermissions?: IncarnationPermissions,
}

export interface IncarnationPermissions {
  canRead: boolean,
  canUpdate: boolean,
  canReset: boolean,
  canDelete: boolean,
}

export interface IncarnationUpdateApiInput {
  requested_version: string,
  requested_data: Record<string, string>,
  automerge: boolean,
}

export interface IncarnationApiInput {
  incarnation_repository: string,
  template_repository: string,
  template_repository_version: string,
  target_directory: string,
  template_data: Record<string, string>,
  automerge: boolean
}

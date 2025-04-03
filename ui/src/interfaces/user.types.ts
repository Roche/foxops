import { Group, GroupApiView } from './group.types'

export interface User {
    id: number,
    username: string,
    isAdmin: boolean,
}

export interface UserApiView {
    id: number,
    username: string,
    is_admin: boolean
}

export interface UserWithGroups extends User {
    groups: Group[]
}

export interface UserWithGroupsApiView extends UserApiView {
    groups: GroupApiView[]
}

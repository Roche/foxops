import { UserWithGroups, UserWithGroupsApiView } from 'interfaces/user.types'
import { api } from './api'

export const convertToUiUserWithGroups = (user: UserWithGroupsApiView): UserWithGroups => ({
  username: user.username,
  id: user.id,
  isAdmin: user.is_admin,
  groups: user.groups.map(group => ({
    id: group.id,
    displayName: group.display_name,
    systemName: group.system_name
  }))
})

export const auth = {
  checkToken: async () => convertToUiUserWithGroups(await api.get<undefined, UserWithGroupsApiView>('/auth/test', { apiPrefix: '' }))
}

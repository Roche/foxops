from foxops.database.schema import Permission
from foxops.models.incarnation import IncarnationPermissions, IncarnationWithDetails
from foxops.models.user import UserWithGroups


class AuthorizationService:
    def __init__(self, current_user: UserWithGroups) -> None:
        self.current_user = current_user

    @property
    def admin(self) -> bool:
        return self.current_user.is_admin

    @property
    def id(self) -> int:
        return self.current_user.id

    def _read_access_incarnation_with_details(self, incarnation: IncarnationWithDetails) -> bool:
        if self.admin or self.id == incarnation.owner.id:
            return True

        user_ids_with_access = [p.user.id for p in incarnation.user_permissions]
        group_ids_with_access = [p.group.id for p in incarnation.group_permissions]
        return self.id in user_ids_with_access or any(
            group.id in group_ids_with_access for group in self.current_user.groups
        )

    def _write_access_incarnation_with_details(self, incarnation: IncarnationWithDetails) -> bool:
        if self.admin or self.id == incarnation.owner.id:
            return True

        user_ids_with_access = [p.user.id for p in incarnation.user_permissions if p.type == Permission.WRITE]
        group_ids_with_access = [p.group.id for p in incarnation.group_permissions if p.type == Permission.WRITE]

        return self.id in user_ids_with_access or any(
            group.id in group_ids_with_access for group in self.current_user.groups
        )

    def _read_access_incarnation_permissions(self, permissions: IncarnationPermissions) -> bool:
        if self.admin or self.id == permissions.owner_id:
            return True

        user_ids_with_access = [p.user_id for p in permissions.user_permissions]
        group_ids_with_access = [p.group_id for p in permissions.group_permissions]

        return self.id in user_ids_with_access or any(
            group.id in group_ids_with_access for group in self.current_user.groups
        )

    def _write_access_incarnation_permissions(self, permissions: IncarnationPermissions) -> bool:
        if self.admin or self.id == permissions.owner_id:
            return True

        user_ids_with_access = [p.user_id for p in permissions.user_permissions if p.type == Permission.WRITE]

        group_ids_with_access = [p.group_id for p in permissions.group_permissions if p.type == Permission.WRITE]

        return self.id in user_ids_with_access or any(
            group.id in group_ids_with_access for group in self.current_user.groups
        )

    def has_read_access(self, object: object) -> bool:
        match object:
            case IncarnationWithDetails():
                return self._read_access_incarnation_with_details(object)
            case IncarnationPermissions():
                return self._read_access_incarnation_permissions(object)
            case _:
                raise NotImplementedError(f"Read access for {type(object)} is not implemented")

    def has_write_access(self, object: object) -> bool:
        match object:
            case IncarnationWithDetails():
                return self._write_access_incarnation_with_details(object)
            case IncarnationPermissions():
                return self._write_access_incarnation_permissions(object)
            case _:
                raise NotImplementedError(f"Write access for {type(object)} is not implemented")

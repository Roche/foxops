from foxops.services.group import GroupService
from foxops.services.user import UserService, UserWithGroups


class AuthorizationService:    
    def __init__(self, current_user: UserWithGroups, user_service: UserService, group_service: GroupService) -> None:
        self.user_service = user_service
        self.group_service = group_service
        self.current_user = current_user

    def is_admin(self) -> bool:
        return self.current_user.is_admin
    
    def is_in_group(self, group_system_name_or_id: str | int) -> bool:
        if isinstance(group_system_name_or_id, str):
            return any(group.system_name == group_system_name_or_id for group in self.current_user.groups)
        else:
            return any(group.id == group_system_name_or_id for group in self.current_user.groups)
from pydantic import BaseModel, ConfigDict

from foxops.database.schema import Permission


class IncarnationInDB(BaseModel):
    id: int
    incarnation_repository: str
    target_directory: str
    template_repository: str
    owner: int
    model_config = ConfigDict(from_attributes=True)


class GroupPermissionInDB(BaseModel):
    group_id: int
    group_system_name: str
    group_display_name: str
    incarnation_id: int
    type: Permission
    model_config = ConfigDict(from_attributes=True)


class UserPermissionInDB(BaseModel):
    user_id: int
    user_username: str
    user_is_admin: bool
    incarnation_id: int
    type: Permission
    model_config = ConfigDict(from_attributes=True)

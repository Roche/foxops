from pydantic import BaseModel, ConfigDict

from foxops.models.group import Group


class User(BaseModel):
    id: int
    username: str
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class UserWithGroups(User):
    groups: list[Group]

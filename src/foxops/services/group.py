from typing import Optional

from pydantic import BaseModel, ConfigDict

from foxops.database.repositories.group.repository import GroupRepository


class Group(BaseModel):
    id: int
    system_name: str
    display_name: str

    model_config = ConfigDict(from_attributes=True)


class GroupService:
    def __init__(self, group_repository: GroupRepository) -> None:
        self.group_repository = group_repository

    async def create_group(
        self,
        system_name: str,
        display_name: Optional[str] = None,
    ) -> Group:
        if display_name is None:
            display_name = system_name

        group = await self.group_repository.create(
            system_name=system_name,
            display_name=display_name,
        )

        return Group.model_validate(group)

    async def get_group_by_system_name(self, system_name: str) -> Group:
        group = await self.group_repository.get_by_system_name(system_name)

        return Group.model_validate(group)

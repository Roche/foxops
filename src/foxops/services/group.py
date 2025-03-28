from typing import Optional

from foxops.database.repositories.group.repository import GroupRepository
from foxops.database.repositories.user.repository import UserRepository
from foxops.models.group import Group
from foxops.models.user import GroupWithUsers


class GroupService:
    def __init__(self, group_repository: GroupRepository, user_repository: UserRepository) -> None:
        self.group_repository = group_repository
        self.user_repository = user_repository

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

    async def list_groups_paginated(
        self,
        limit: int,
        page: int,
    ) -> list[Group]:
        groups = await self.group_repository.list_paginated(
            limit,
            limit * (page - 1),
        )

        return [Group.model_validate(group) for group in groups]

    async def get_group_by_id(self, group_id: int) -> Group:
        group = await self.group_repository.get_by_id(group_id)

        return Group.model_validate(group)

    async def get_group_by_id_with_users(self, group_id: int) -> Group:
        group = await self.group_repository.get_by_id(group_id)

        users = await self.user_repository.get_users_of_group(group_id)

        return GroupWithUsers(**group.model_dump(), users=users)

    async def delete_group(self, group_id: int) -> None:
        await self.group_repository.get_by_id(group_id)  # check if group exists

        await self.group_repository.delete(group_id)

    async def set_display_name(self, group_id: int, display_name: str) -> Group:
        group = await self.group_repository.set_display_name(group_id, display_name)

        return Group.model_validate(group)

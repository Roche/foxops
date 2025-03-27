from pydantic import BaseModel, ConfigDict

from foxops.database.repositories.group.repository import GroupRepository
from foxops.database.repositories.incarnation.repository import IncarnationRepository
from foxops.database.repositories.user.repository import UserRepository
from foxops.hosters import Hoster
from foxops.models.incarnation import (
    GroupPermission,
    UnresolvedGroupPermissions,
    UnresolvedUserPermissions,
    UserPermission,
)
from foxops.models.user import User


class Incarnation(BaseModel):
    id: int
    incarnation_repository: str
    target_directory: str
    template_repository: str

    owner: User

    model_config = ConfigDict(from_attributes=True)


class IncarnationService:
    def __init__(
        self,
        incarnation_repository: IncarnationRepository,
        hoster: Hoster,
        user_repository: UserRepository,
        group_repository: GroupRepository,
    ) -> None:
        self.incarnation_repository = incarnation_repository
        self.user_repository = user_repository
        self.group_repository = group_repository
        self.hoster = hoster

    async def create(
        self,
        incarnation_repository: str,
        target_directory: str,
        template_repository: str,
        owner_id: int,
    ) -> Incarnation:
        # verify that the incarnation repository exists
        await self.hoster.get_repository_metadata(incarnation_repository)

        # TODO: verify that the target directory is empty
        # TODO: verify that the template repository exists

        incarnation_in_db = await self.incarnation_repository.create(
            incarnation_repository=incarnation_repository,
            target_directory=target_directory,
            template_repository=template_repository,
            owner_id=owner_id,
        )
        return Incarnation.model_validate(incarnation_in_db)

    async def get_by_id(self, id_: int) -> Incarnation:
        incarnation_in_db = await self.incarnation_repository.get_by_id(id_)

        owner = await self.user_repository.get_by_id(incarnation_in_db.owner)

        incarnation_json = incarnation_in_db.model_dump()
        del incarnation_json["owner"]

        return Incarnation(owner=owner, **incarnation_json)

    async def delete(self, incarnation: Incarnation) -> None:
        await self.incarnation_repository.delete_by_id(incarnation.id)

    async def set_user_permissions(
        self, incarnation_id: int, user_permissions: list[UnresolvedUserPermissions]
    ) -> None:
        if len(user_permissions) == 0:
            return
        resolved_user_permissions = [
            UserPermission(
                user=await self.user_repository.get_by_id(user_permission.user_id),
                type=user_permission.type,
            )
            for user_permission in user_permissions
        ]

        await self.incarnation_repository.get_by_id(incarnation_id)  # Validate if the incarnation exists

        await self.incarnation_repository.set_user_permissions(incarnation_id, resolved_user_permissions)

    async def set_group_permissions(
        self, incarnation_id: int, group_permissions: list[UnresolvedGroupPermissions]
    ) -> None:
        if len(group_permissions) == 0:
            return
        resolved_group_permissions = [
            GroupPermission(
                group=await self.group_repository.get_by_id(group_permission.group_id),
                type=group_permission.type,
            )
            for group_permission in group_permissions
        ]

        await self.incarnation_repository.get_by_id(incarnation_id)  # Validate if the incarnation exists

        await self.incarnation_repository.set_group_permissions(incarnation_id, resolved_group_permissions)

    async def remove_all_user_permissions(self, incarnation_id: int) -> None:
        await self.incarnation_repository.remove_all_user_permissions(incarnation_id)

    async def remove_all_group_permissions(self, incarnation_id: int) -> None:
        await self.incarnation_repository.remove_all_group_permissions(incarnation_id)

    async def remove_all_permissions(self, incarnation_id: int) -> None:
        await self.remove_all_group_permissions(incarnation_id)
        await self.remove_all_user_permissions(incarnation_id)

    async def set_owner(self, incarnation_id: int, user_id: int):
        await self.incarnation_repository.set_owner(incarnation_id, user_id)

    async def get_user_ids_with_access(self, incarnation_id: int) -> list[int]:
        return await self.incarnation_repository.get_user_ids_with_permission(incarnation_id)

    async def get_group_ids_with_access(self, incarnation_id: int) -> list[int]:
        return await self.incarnation_repository.get_group_ids_with_permission(incarnation_id)

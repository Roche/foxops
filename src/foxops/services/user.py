from foxops.database.repositories.group.repository import GroupRepository
from foxops.database.repositories.user.repository import UserRepository
from foxops.models.user import User, UserWithGroups


class UserService:
    def __init__(self, user_repository: UserRepository, group_repository: GroupRepository) -> None:
        self.user_repository = user_repository
        self.group_repository = group_repository

    async def create_user(
        self,
        username: str,
        is_admin: bool = False,
    ) -> User:
        user = await self.user_repository.create(
            username=username,
            is_admin=is_admin,
        )

        return User.model_validate(user)

    async def get_user_by_username(self, username: str) -> User:
        user = await self.user_repository.get_by_username(username)

        return User.model_validate(user)

    async def join_groups(self, username: str, group_ids: list[int], remove_old_ref: bool = False) -> User:
        user = await self.user_repository.get_by_username(username)

        if remove_old_ref:
            await self.user_repository.remove_old_groups_from_user(user.id, group_ids)

        existing_groups = [group.id for group in await self.group_repository.get_by_userid(user.id)]

        not_joined_groups = [group_id for group_id in group_ids if group_id not in existing_groups]

        if len(not_joined_groups) > 0:
            await self.user_repository.join_groups(user.id, not_joined_groups)

        return User.model_validate(user)

    async def get_user_by_username_with_groups(self, username: str) -> UserWithGroups:
        user = await self.user_repository.get_by_username(username)

        groups = await self.group_repository.get_by_userid(user.id)

        return UserWithGroups(groups=groups, **user.model_dump())

    async def remove_all_groups_from_user(self, user_id: int) -> None:
        await self.user_repository.remove_all_groups(user_id)

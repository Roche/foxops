from typing import AsyncIterator, List

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncEngine

from foxops.database.repositories.incarnation.errors import (
    IncarnationAlreadyExistsError,
    IncarnationNotFoundError,
)
from foxops.database.repositories.incarnation.model import (
    GroupPermissionInDB,
    IncarnationInDB,
    UnresolvedGroupPermissionsInDB,
    UnresolvedUserPermissionsInDB,
    UserPermissionInDB,
)
from foxops.database.repositories.user.errors import UserNotFoundError
from foxops.database.schema import (
    group,
    group_incarnation_permission,
    incarnations,
    user,
    user_incarnation_permission,
)
from foxops.models.incarnation import GroupPermission, UserPermission


class IncarnationRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def create(
        self,
        incarnation_repository: str,
        target_directory: str,
        template_repository: str,
        owner_id: int,
    ) -> IncarnationInDB:
        async with self.engine.begin() as conn:
            query = (
                insert(incarnations)
                .values(
                    incarnation_repository=incarnation_repository,
                    target_directory=target_directory,
                    template_repository=template_repository,
                    owner=owner_id,
                )
                .returning(incarnations)
            )

            try:
                result = await conn.execute(query)
            except IntegrityError as e:
                raise IncarnationAlreadyExistsError(
                    f"repo={incarnation_repository}, directory={target_directory}"
                ) from e

            row = result.one()
            return IncarnationInDB.model_validate(row)

    async def list(self) -> AsyncIterator[IncarnationInDB]:
        query = select(incarnations)

        async with self.engine.begin() as conn:
            for row in await conn.execute(query):
                yield IncarnationInDB.model_validate(row)

    async def get_by_id(self, id_: int) -> IncarnationInDB:
        query = select(incarnations).where(incarnations.c.id == id_)

        async with self.engine.begin() as conn:
            result = await conn.execute(query)

            try:
                row = result.one()
            except NoResultFound:
                raise IncarnationNotFoundError(id_)
            else:
                return IncarnationInDB.model_validate(row)

    async def delete_by_id(self, id_: int) -> None:
        query = delete(incarnations).where(incarnations.c.id == id_)

        async with self.engine.begin() as conn:
            result = await conn.execute(query)

            if result.rowcount == 0:
                raise IncarnationNotFoundError(id_)

    async def get_group_permissions(self, incarnation_id: int) -> List[GroupPermissionInDB]:
        query = (
            select(
                group_incarnation_permission,
                group.c.system_name.label("group_system_name"),
                group.c.display_name.label("group_display_name"),
            )
            .where(group_incarnation_permission.c.incarnation_id == incarnation_id)
            .join(group)
        )

        async with self.engine.begin() as conn:
            rows = await conn.execute(query)

            return [GroupPermissionInDB.model_validate(row) for row in rows]

    async def get_user_permissions(self, incarnation_id: int) -> List[UserPermissionInDB]:
        query = (
            select(
                user_incarnation_permission,
                user.c.username.label("user_username"),
                user.c.is_admin.label("user_is_admin"),
            )
            .where(user_incarnation_permission.c.incarnation_id == incarnation_id)
            .join(user)
        )

        async with self.engine.begin() as conn:
            rows = await conn.execute(query)
            return [UserPermissionInDB.model_validate(row) for row in rows]

    async def get_unresolved_user_permissions(self, incarnation_id: int) -> List[UnresolvedUserPermissionsInDB]:
        query = select(user_incarnation_permission).where(
            user_incarnation_permission.c.incarnation_id == incarnation_id
        )

        async with self.engine.begin() as conn:
            rows = await conn.execute(query)
            return [UnresolvedUserPermissionsInDB.model_validate(row) for row in rows]

    async def get_unresolved_group_permissions(self, incarnation_id: int) -> List[UnresolvedGroupPermissionsInDB]:
        query = select(group_incarnation_permission).where(
            group_incarnation_permission.c.incarnation_id == incarnation_id
        )

        async with self.engine.begin() as conn:
            rows = await conn.execute(query)
            return [UnresolvedGroupPermissionsInDB.model_validate(row) for row in rows]

    async def set_user_permissions(self, incarnation_id: int, user_permissions: List[UserPermission]):
        query = insert(user_incarnation_permission).values(
            [
                {"user_id": user_permission.user.id, "incarnation_id": incarnation_id, "type": user_permission.type}
                for user_permission in user_permissions
            ]
        )
        async with self.engine.begin() as conn:
            await conn.execute(query)

    async def set_group_permissions(self, incarnation_id: int, group_permissions: List[GroupPermission]):
        query = insert(group_incarnation_permission).values(
            [
                {"group_id": group_permission.group.id, "incarnation_id": incarnation_id, "type": group_permission.type}
                for group_permission in group_permissions
            ]
        )
        async with self.engine.begin() as conn:
            await conn.execute(query)

    async def remove_all_user_permissions(self, incarnation_id: int):
        async with self.engine.begin() as conn:
            query = user_incarnation_permission.delete().where(
                user_incarnation_permission.c.incarnation_id == incarnation_id
            )
            await conn.execute(query)

    async def remove_all_group_permissions(self, incarnation_id: int):
        async with self.engine.begin() as conn:
            query = group_incarnation_permission.delete().where(
                group_incarnation_permission.c.incarnation_id == incarnation_id
            )
            await conn.execute(query)

    async def set_owner(self, incarnation_id: int, user_id: int):
        async with self.engine.begin() as conn:
            query = (
                update(incarnations)
                .where(incarnations.c.id == incarnation_id)
                .values(owner=user_id)
                .returning(incarnations)
            )
            try:
                result = await conn.execute(query)
            except IntegrityError as e:
                raise UserNotFoundError(id=user_id) from e
            try:
                row = result.one()
            except NoResultFound as e:
                raise IncarnationNotFoundError(incarnation_id) from e

            return IncarnationInDB.model_validate(row)

    async def get_owner_id(self, incarnation_id: int) -> int:
        query = select(incarnations.c.owner).where(incarnations.c.id == incarnation_id)

        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            try:
                row = result.one()
            except NoResultFound as e:
                raise IncarnationNotFoundError(incarnation_id) from e

            return row[0]

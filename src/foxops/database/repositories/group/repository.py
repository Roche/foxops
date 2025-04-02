from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncEngine

from foxops.database.repositories.group.errors import (
    GroupAlreadyExistsError,
    GroupNotFoundError,
)
from foxops.database.repositories.group.model import GroupInDB
from foxops.database.schema import group, group_user


class GroupRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def create(self, system_name: str, display_name: str) -> GroupInDB:
        async with self.engine.begin() as conn:
            query = insert(group).values(system_name=system_name, display_name=display_name).returning(group)

            try:
                result = await conn.execute(query)
            except IntegrityError as e:
                raise GroupAlreadyExistsError(system_name) from e

            row = result.one()
            return GroupInDB.model_validate(row)

    async def get_by_system_name(self, system_name: str) -> GroupInDB:
        query = select(group).where(group.c.system_name == system_name)

        async with self.engine.begin() as conn:
            result = await conn.execute(query)

            try:
                row = result.one()
            except NoResultFound as e:
                raise GroupNotFoundError(system_name=system_name) from e

            return GroupInDB.model_validate(row)

    async def get_by_userid(self, user_id: int) -> list[GroupInDB]:
        query = select(group_user, group).where(group_user.c.user_id == user_id).join(group)

        async with self.engine.begin() as conn:
            result = await conn.execute(query)

            return [GroupInDB.model_validate(row) for row in result]

    async def get_by_id(self, group_id: int) -> GroupInDB:
        query = select(group).where(group.c.id == group_id)

        async with self.engine.begin() as conn:
            result = await conn.execute(query)

            try:
                row = result.one()
            except NoResultFound as e:
                raise GroupNotFoundError(id=group_id) from e

            return GroupInDB.model_validate(row)

    async def list_paginated(
        self,
        limit: int,
        offset: int,
    ) -> list[GroupInDB]:
        query = select(group).limit(limit).offset(offset)

        async with self.engine.begin() as conn:
            result = await conn.execute(query)

            return [GroupInDB.model_validate(row) for row in result]

    async def delete(self, group_id: int) -> None:
        async with self.engine.begin() as conn:
            query = group.delete().where(group.c.id == group_id)
            await conn.execute(query)

    async def set_display_name(self, group_id: int, display_name: str) -> GroupInDB:
        async with self.engine.begin() as conn:
            query = group.update().where(group.c.id == group_id).values(display_name=display_name).returning(group)

            result = await conn.execute(query)

            try:
                row = result.one()
            except NoResultFound as e:
                raise GroupNotFoundError(id=group_id) from e

            return GroupInDB.model_validate(row)

from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncEngine

from foxops.database.repositories.user.errors import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from foxops.database.repositories.user.model import UserInDB
from foxops.database.schema import group_user, user


class UserRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def create(self, username: str, is_admin: bool) -> UserInDB:
        async with self.engine.begin() as conn:
            query = insert(user).values(username=username, is_admin=is_admin).returning(user)

            try:
                result = await conn.execute(query)
            except IntegrityError as e:
                raise UserAlreadyExistsError(username=username) from e

            row = result.one()
            return UserInDB.model_validate(row)

    async def get_by_username(self, username: str) -> UserInDB:
        query = select(user).where(user.c.username == username)

        async with self.engine.begin() as conn:
            result = await conn.execute(query)

            try:
                row = result.one()
            except NoResultFound as e:
                raise UserNotFoundError(username=username) from e

            return UserInDB.model_validate(row)

    async def remove_old_groups_from_user(self, user_id: int, group_ids_to_keep: list[int]):
        async with self.engine.begin() as conn:
            query = (
                group_user.delete()
                .where(group_user.c.user_id == user_id)
                .where(group_user.c.group_id.notin_(group_ids_to_keep))
            )
            await conn.execute(query)

    async def join_groups(self, user_id: int, group_ids: list[int]):
        async with self.engine.begin() as conn:
            query = insert(group_user).values([{"user_id": user_id, "group_id": group_id} for group_id in group_ids])
            await conn.execute(query)

    async def remove_all_groups(self, user_id: int):
        async with self.engine.begin() as conn:
            query = group_user.delete().where(group_user.c.user_id == user_id)
            await conn.execute(query)

    async def get_by_id(self, user_id: int) -> UserInDB:
        query = select(user).where(user.c.id == user_id)

        async with self.engine.begin() as conn:
            result = await conn.execute(query)

            try:
                row = result.one()
            except NoResultFound as e:
                raise UserNotFoundError(id=user_id) from e

            return UserInDB.model_validate(row)

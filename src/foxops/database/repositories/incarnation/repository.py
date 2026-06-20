from typing import AsyncIterator

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncEngine

from foxops.database.repositories.incarnation.errors import (
    IncarnationAlreadyExistsError,
    IncarnationNotFoundError,
)
from foxops.database.repositories.incarnation.model import IncarnationInDB
from foxops.database.schema import incarnations


class IncarnationRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def create(
        self,
        incarnation_repository: str,
        target_directory: str,
        template_repository: str,
        auto_update_interval_seconds: int = 0,
    ) -> IncarnationInDB:
        async with self.engine.begin() as conn:
            query = (
                insert(incarnations)
                .values(
                    incarnation_repository=incarnation_repository,
                    target_directory=target_directory,
                    template_repository=template_repository,
                    auto_update_interval_seconds=auto_update_interval_seconds,
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
                raise IncarnationNotFoundError(f"could not find incarnation in DB with id: {id_}")
            else:
                return IncarnationInDB.model_validate(row)

    async def update_auto_update_interval(self, id_: int, interval_seconds: int) -> None:
        query = (
            update(incarnations).values(auto_update_interval_seconds=interval_seconds).where(incarnations.c.id == id_)
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            if result.rowcount == 0:
                raise IncarnationNotFoundError(f"could not find incarnation in DB with id: {id_}")

    async def delete_by_id(self, id_: int) -> None:
        query = delete(incarnations).where(incarnations.c.id == id_)

        async with self.engine.begin() as conn:
            result = await conn.execute(query)

            if result.rowcount == 0:
                raise IncarnationNotFoundError(f"could not find incarnation in DB with id: {id_}")

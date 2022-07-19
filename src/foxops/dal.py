from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from foxops.database.config import meta
from foxops.errors import IncarnationNotFoundError
from foxops.hosters import GitSha
from foxops.logging import get_logger
from foxops.models import DesiredIncarnationState, Incarnation

#: Holds the module logger
logger = get_logger(__name__)


#: Holds the URL to the database
DATABASE_URL = "sqlite+aiosqlite:///./test.db"


async_engine = create_async_engine(
    DATABASE_URL, future=True, echo=False, pool_pre_ping=True
)


class DAL:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def initialize_db(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(meta.create_all)

    @asynccontextmanager
    async def connection(self):
        async with self.engine.connect() as conn:
            yield conn

    async def get_incarnations(self) -> AsyncIterator[Incarnation]:
        async with self.connection() as conn:
            for row in await conn.execute(text("SELECT * FROM incarnation")):
                yield Incarnation.from_orm(row)

    async def get_incarnation(self, id: int) -> Incarnation:
        async with self.connection() as conn:
            query = await conn.execute(
                text("SELECT * FROM incarnation WHERE id = :id"),
                {"id": id},
            )

            try:
                row = query.one()
            except NoResultFound:
                raise IncarnationNotFoundError(id)
            else:
                return Incarnation.from_orm(row)

    async def create_incarnation(
        self,
        desired_incarnation_state: DesiredIncarnationState,
        revision: GitSha,
    ) -> Incarnation:
        async with self.connection() as conn:
            # Check if the incarnation already exists and if so, just update it gracefully
            if incarnation := await self._get_incarnation_by_identity(
                desired_incarnation_state.incarnation_repository,
                desired_incarnation_state.target_directory,
                conn=conn,
            ):
                # FIXME: nothing to update for now ...
                return incarnation

            query = await conn.execute(
                text(
                    """
                    INSERT INTO incarnation
                        (incarnation_repository, target_directory, status, revision)
                    VALUES
                        (:incarnation_repository, :target_directory, :status, :revision)
                    RETURNING *
                    """
                ),
                {
                    "incarnation_repository": desired_incarnation_state.incarnation_repository,
                    "target_directory": desired_incarnation_state.target_directory,
                    "status": "created",
                    "revision": revision,
                },
            )

            row = query.one()
            await conn.commit()
            return Incarnation.from_orm(row)

    async def delete_incarnation(self, id: int) -> None:
        async with self.connection() as conn:
            await conn.execute(
                text("DELETE FROM incarnation WHERE id = :id"), {"id": id}
            )
            await conn.commit()

    async def _get_incarnation_by_identity(
        self,
        incarnation_repository: str,
        target_directory: str,
        conn: AsyncConnection,
    ) -> Incarnation | None:
        query = await conn.execute(
            text(
                """
                SELECT * FROM incarnation
                WHERE
                    incarnation_repository = :incarnation_repository
                AND
                    target_directory = :target_directory
                LIMIT 1
                """
            ),
            {
                "incarnation_repository": incarnation_repository,
                "target_directory": target_directory,
            },
        )

        try:
            row = query.one()
        except NoResultFound:
            return None
        else:
            return Incarnation.from_orm(row)


def get_dal():
    return DAL(async_engine)

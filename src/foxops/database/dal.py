from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy import select, text
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from foxops.database.schema import incarnations, meta
from foxops.errors import IncarnationNotFoundError
from foxops.hosters import GitSha, MergeRequestId
from foxops.logger import get_logger
from foxops.models import DesiredIncarnationState, Incarnation

#: Holds the module logger
logger = get_logger(__name__)


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
            for row in await conn.execute(select(incarnations)):
                yield Incarnation.from_orm(row)

    async def get_incarnation(self, id: int) -> Incarnation:
        async with self.connection() as conn:
            query = await conn.execute(select(incarnations).where(incarnations.c.id == id))

            try:
                row = query.one()
            except NoResultFound:
                raise IncarnationNotFoundError(id)
            else:
                return Incarnation.from_orm(row)

    async def create_incarnation(
        self,
        desired_incarnation_state: DesiredIncarnationState,
        commit_sha: GitSha,
        merge_request_id: str | None,
    ) -> Incarnation:
        async with self.connection() as conn:
            # Check if the incarnation already exists and if so, just update it gracefully
            if incarnation := await self.get_incarnation_by_identity(
                desired_incarnation_state.incarnation_repository,
                desired_incarnation_state.target_directory,
                conn=conn,
            ):
                return incarnation

            query = await conn.execute(
                text(
                    """
                    INSERT INTO incarnation
                        (incarnation_repository, target_directory, commit_sha, merge_request_id)
                    VALUES
                        (:incarnation_repository, :target_directory, :commit_sha, :merge_request_id)
                    RETURNING *
                    """
                ),
                {
                    "incarnation_repository": desired_incarnation_state.incarnation_repository,
                    "target_directory": desired_incarnation_state.target_directory,
                    "commit_sha": commit_sha,
                    "merge_request_id": merge_request_id,
                },
            )

            row = query.one()
            await conn.commit()
            return Incarnation.from_orm(row)

    async def update_incarnation(self, id: int, commit_sha: GitSha, merge_request_id: MergeRequestId) -> Incarnation:
        async with self.connection() as conn:
            query = await conn.execute(
                text(
                    """
                    UPDATE incarnation
                    SET
                        commit_sha = :commit_sha,
                        merge_request_id = :merge_request_id
                    WHERE
                        id = :id
                    RETURNING *
                    """
                ),
                {"id": id, "commit_sha": commit_sha, "merge_request_id": merge_request_id},
            )

            row = query.one()
            await conn.commit()
            return Incarnation.from_orm(row)

    async def delete_incarnation(self, id: int) -> None:
        async with self.connection() as conn:
            await conn.execute(incarnations.delete().where(incarnations.c.id == id))
            await conn.commit()

    async def get_incarnation_by_identity(
        self,
        incarnation_repository: str,
        target_directory: str,
        conn: AsyncConnection,
    ) -> Incarnation | None:
        query = await conn.execute(
            select(incarnations)
            .where(incarnations.c.incarnation_repository == incarnation_repository)
            .where(incarnations.c.target_directory == target_directory)
            .limit(1)
        )

        try:
            row = query.one()
        except NoResultFound:
            return None
        else:
            return Incarnation.from_orm(row)

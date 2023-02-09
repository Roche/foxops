import enum
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncEngine

from foxops.database.schema import change
from foxops.errors import FoxopsError


class ChangeConflictError(FoxopsError):
    def __init__(self, incarnation_id: int, revision: int) -> None:
        super().__init__(f"Change with revision {revision} already exists for incarnation {incarnation_id}")


class ChangeNotFoundError(FoxopsError):
    def __init__(self, id_: int) -> None:
        super().__init__(f"Change with id {id_} not found")


class IncarnationHasNoChangesError(FoxopsError):
    def __init__(self, incarnation_id: int) -> None:
        super().__init__(f"Incarnation with id {incarnation_id} has no changes")


class ChangeType(enum.Enum):
    DIRECT = "direct"
    MERGE_REQUEST = "merge_request"


class ChangeInDB(BaseModel):
    id: int

    incarnation_id: int
    revision: int

    commit_sha: str
    commit_pushed: bool

    type: ChangeType
    created_at: datetime

    requested_version: str | None
    requested_data: str | None

    class Config:
        orm_mode = True


class ChangeRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def create_change(
        self,
        incarnation_id: int,
        revision: int,
        change_type: ChangeType,
        commit_sha: str,
        commit_pushed: bool | None = None,
        requested_version: str | None = None,
        requested_data: str | None = None,
        merge_request_id: str | None = None,
        merge_request_status: str | None = None,
        branch_name: str | None = None,
        merge_commit_sha: str | None = None,
    ) -> ChangeInDB:
        """
        Create a new change for the given incarnation with the given "revision" number.

        It is the responsibility of the caller to ensure that the revision number is correct (last revision + 1).
        Due to the existing unique constraint on the (incarnation_id, revision) pair, this method will fail if another
        change with an identical revision number was created py another party.

        This is a useful mechanism to prevent conflicting changes.
        """

        async with self.engine.execution_options(isolation_level="SERIALIZABLE").begin() as conn:
            query = text(
                """
                    INSERT INTO change (
                        `incarnation_id`,
                        `revision`,
                        `type`,
                        `created_at`,
                        `requested_version`,
                        `requested_data`,
                        `commit_sha`,
                        `commit_pushed`,
                        `merge_request_id`,
                        `merge_request_status`,
                        `branch_name`,
                        `merge_commit_sha`
                    )
                    VALUES (
                        :incarnation_id,
                        :revision,
                        :type,
                        :created_at,
                        :requested_version,
                        :requested_data,
                        :commit_sha,
                        :commit_pushed,
                        :merge_request_id,
                        :merge_request_status,
                        :branch_name,
                        :merge_commit_sha
                    )
                    RETURNING *
                    """
            )
            try:
                result = await conn.execute(
                    query,
                    {
                        "incarnation_id": incarnation_id,
                        "revision": revision,
                        "type": change_type.value,
                        "created_at": datetime.now(timezone.utc),
                        "requested_version": requested_version,
                        "requested_data": requested_data,
                        "commit_sha": commit_sha,
                        "commit_pushed": commit_pushed,
                        "merge_request_id": merge_request_id,
                        "merge_request_status": merge_request_status,
                        "branch_name": branch_name,
                        "merge_commit_sha": merge_commit_sha,
                    },
                )
            except IntegrityError:
                raise ChangeConflictError(incarnation_id, revision)

            row = result.one()
            await conn.commit()

        return ChangeInDB.from_orm(row)

    async def get_change(self, id_: int) -> ChangeInDB:
        async with self.engine.connect() as conn:
            result = await conn.execute(select(change).where(change.c.id == id_))

            try:
                row = result.one()
            except NoResultFound:
                raise ChangeNotFoundError(id_)
            else:
                return ChangeInDB.from_orm(row)

    async def get_latest_change_for_incarnation(self, incarnation_id: int) -> ChangeInDB:
        async with self.engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT *
                    FROM change
                    WHERE incarnation_id = :incarnation_id
                    ORDER BY revision DESC
                    LIMIT 1
                    """
                ),
                {
                    "incarnation_id": incarnation_id,
                },
            )

            try:
                row = result.one()
            except NoResultFound:
                raise IncarnationHasNoChangesError(incarnation_id)
            else:
                return ChangeInDB.from_orm(row)

    async def delete_change(self, id_: int) -> None:
        async with self.engine.connect() as conn:
            result = await conn.execute(delete(change).where(change.c.id == id_))
            await conn.commit()

        if result.rowcount == 0:
            raise ChangeNotFoundError(id_)

    async def update_change_commit_pushed(self, id_: int, commit_pushed: bool) -> ChangeInDB:
        async with self.engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                    UPDATE change
                    SET commit_pushed = :commit_pushed
                    WHERE id = :id
                    RETURNING *
                    """
                ),
                {
                    "id": id_,
                    "commit_pushed": commit_pushed,
                },
            )

            row = result.one()
            await conn.commit()

        return ChangeInDB.from_orm(row)

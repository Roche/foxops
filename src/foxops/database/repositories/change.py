import enum
from datetime import datetime, timezone
from typing import AsyncIterator, Self

from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, delete, desc, insert, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncEngine

from foxops.database.schema import change, incarnations
from foxops.errors import FoxopsError, IncarnationNotFoundError


class ChangeConflictError(FoxopsError):
    def __init__(self, incarnation_id: int, revision: int) -> None:
        super().__init__(f"Change with revision {revision} already exists for incarnation {incarnation_id}")


class ChangeNotFoundError(FoxopsError):
    def __init__(self, id_: int) -> None:
        super().__init__(f"Change with id {id_} not found")


class ChangeCommitAlreadyPushedError(FoxopsError):
    def __init__(self, id_: int) -> None:
        super().__init__(
            f"The commit for change with id {id_} was already pushed. Then the commit sha cannot be changed."
        )


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

    requested_version_hash: str
    requested_version: str
    requested_data: str

    merge_request_id: str | None
    merge_request_branch_name: str | None
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_database_row(cls, obj) -> Self:
        change_in_db = cls.model_validate(obj)
        change_in_db.created_at = change_in_db.created_at.replace(tzinfo=timezone.utc)

        return change_in_db


class IncarnationWithChangesSummary(BaseModel):
    """Represents an incarnation combined with information about its latest change."""

    id: int

    incarnation_repository: str
    target_directory: str
    template_repository: str

    revision: int
    type: ChangeType
    commit_sha: str
    requested_version: str
    merge_request_id: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ChangeRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def create_change(
        self,
        incarnation_id: int,
        revision: int,
        change_type: ChangeType,
        commit_sha: str,
        commit_pushed: bool,
        requested_version_hash: str,
        requested_version: str,
        requested_data: str,
        merge_request_id: str | None = None,
        merge_request_branch_name: str | None = None,
    ) -> ChangeInDB:
        """
        Create a new change for the given incarnation with the given "revision" number.

        It is the responsibility of the caller to ensure that the revision number is correct (last revision + 1).
        Due to the existing unique constraint on the (incarnation_id, revision) pair, this method will fail if another
        change with an identical revision number was created py another party.

        This is a useful mechanism to prevent conflicting changes.
        """

        async with self.engine.connect() as conn:
            query = (
                insert(change)
                .values(
                    incarnation_id=incarnation_id,
                    revision=revision,
                    type=change_type.value,
                    created_at=datetime.now(timezone.utc),
                    requested_version_hash=requested_version_hash,
                    requested_version=requested_version,
                    requested_data=requested_data,
                    commit_sha=commit_sha,
                    commit_pushed=commit_pushed,
                    merge_request_id=merge_request_id,
                    merge_request_branch_name=merge_request_branch_name,
                )
                .returning(*change.columns)
            )
            try:
                result = await conn.execute(query)
            except IntegrityError:
                raise ChangeConflictError(incarnation_id, revision)

            row = result.one()
            await conn.commit()

        return ChangeInDB.model_validate(row)

    async def create_incarnation_with_first_change(
        self,
        incarnation_repository: str,
        target_directory: str,
        template_repository: str,
        commit_sha: str,
        requested_version_hash: str,
        requested_version: str,
        requested_data: str,
    ) -> ChangeInDB:
        async with self.engine.begin() as conn:
            query_insert_incarnation = (
                insert(incarnations)
                .values(
                    incarnation_repository=incarnation_repository,
                    target_directory=target_directory,
                    template_repository=template_repository,
                )
                .returning(incarnations.c.id)
            )
            result = await conn.execute(query_insert_incarnation)
            incarnation_id = result.one()[0]

            query_insert_change = (
                insert(change)
                .values(
                    incarnation_id=incarnation_id,
                    revision=1,
                    type=ChangeType.DIRECT.value,
                    created_at=datetime.now(timezone.utc),
                    requested_version_hash=requested_version_hash,
                    requested_version=requested_version,
                    requested_data=requested_data,
                    commit_sha=commit_sha,
                    commit_pushed=False,
                )
                .returning(*change.columns)
            )
            result = await conn.execute(query_insert_change)

            row = result.one()
            await conn.commit()

        return ChangeInDB.model_validate(row)

    async def delete_incarnation(self, id_: int) -> None:
        async with self.engine.connect() as conn:
            await conn.execute(delete(incarnations).where(incarnations.c.id == id_))
            await conn.commit()

    async def get_change_by_revision(self, incarnation_id: int, revision: int) -> ChangeInDB:
        query = select(change).where(and_(change.c.incarnation_id == incarnation_id, change.c.revision == revision))
        async with self.engine.connect() as conn:
            result = await conn.execute(query)

            try:
                row = result.one()
            except NoResultFound:
                raise ChangeNotFoundError(0)

        return ChangeInDB.from_database_row(row)

    async def get_change(self, id_: int) -> ChangeInDB:
        query = select(change).where(change.c.id == id_)
        async with self.engine.connect() as conn:
            result = await conn.execute(query)

            try:
                row = result.one()
            except NoResultFound:
                raise ChangeNotFoundError(id_)

        return ChangeInDB.from_database_row(row)

    async def get_latest_change_for_incarnation(self, incarnation_id: int) -> ChangeInDB:
        query = (
            select(change).where(change.c.incarnation_id == incarnation_id).order_by(change.c.revision.desc()).limit(1)
        )
        async with self.engine.connect() as conn:
            result = await conn.execute(query)

            try:
                row = result.one()
            except NoResultFound:
                raise IncarnationHasNoChangesError(incarnation_id)
            else:
                return ChangeInDB.model_validate(row)

    def _incarnations_with_changes_summary_query(self):
        alias_change = change.alias("change")
        alias_change_newer = change.alias("change_newer")

        return (
            incarnations.c,
            alias_change.c,
            (
                select(
                    incarnations.c.id,
                    incarnations.c.incarnation_repository,
                    incarnations.c.target_directory,
                    incarnations.c.template_repository,
                    alias_change.c.revision,
                    alias_change.c.type,
                    alias_change.c.requested_version,
                    alias_change.c.commit_sha,
                    alias_change.c.merge_request_id,
                    alias_change.c.created_at,
                )
                .select_from(incarnations)
                # join incarnations with the corresponding latest change
                .join(alias_change, alias_change.c.incarnation_id == incarnations.c.id)
                .join(
                    alias_change_newer,
                    and_(
                        alias_change_newer.c.incarnation_id == incarnations.c.id,
                        alias_change.c.revision < alias_change_newer.c.revision,
                    ),
                    isouter=True,
                )
                # filter out all combinations where a newer change exists - to only leave those
                # where the joined `change` is already the latest one
                .where(alias_change_newer.c.id.is_(None))
                .order_by(incarnations.c.id)
            ),
        )

    async def list_incarnations_with_changes_summary(self) -> AsyncIterator[IncarnationWithChangesSummary]:
        _, _, query = self._incarnations_with_changes_summary_query()

        async with self.engine.connect() as conn:
            for row in await conn.execute(query):
                yield IncarnationWithChangesSummary.model_validate(row)

    async def get_incarnation_by_repo_and_target_dir(
        self, incarnation_repository: str, target_directory: str
    ) -> IncarnationWithChangesSummary:
        incarnation_c, _, query = self._incarnations_with_changes_summary_query()
        query = query.where(incarnation_c.incarnation_repository == incarnation_repository).where(
            incarnation_c.target_directory == target_directory
        )

        async with self.engine.connect() as conn:
            result = await conn.execute(query)
            try:
                row = result.one()
            except NoResultFound:
                raise IncarnationNotFoundError(0)

        return IncarnationWithChangesSummary.model_validate(row)

    async def list_changes(self, incarnation_id: int) -> list[ChangeInDB]:
        query = select(change).where(change.c.incarnation_id == incarnation_id).order_by(desc(change.c.revision))
        async with self.engine.connect() as conn:
            result = await conn.execute(query)

            return [ChangeInDB.from_database_row(row) for row in result]

    async def delete_change(self, id_: int) -> None:
        async with self.engine.connect() as conn:
            result = await conn.execute(delete(change).where(change.c.id == id_))
            await conn.commit()

        if result.rowcount == 0:
            raise ChangeNotFoundError(id_)

    async def update_commit_sha(self, id_: int, commit_sha: str) -> ChangeInDB:
        query_select_change_commit_pushed = select(change.c.commit_pushed).where(change.c.id == id_)

        async with self.engine.begin() as conn:
            # verify that the change exists and the referenced commit was not yet pushed
            # NOTE: Maybe it makes sense to move this into the business service, to also verify that the commit
            #       referenced in the DB does NOT exist in the target repo
            result = await conn.execute(query_select_change_commit_pushed)
            try:
                commit_pushed = result.scalar_one()
            except NoResultFound:
                raise ChangeNotFoundError(id_)

            if commit_pushed:
                raise ChangeCommitAlreadyPushedError(id_)

            # all good, let's update the commit sha
            result = await conn.execute(
                update(change).values(commit_sha=commit_sha).where(change.c.id == id_).returning(*change.columns)
            )
            row = result.one()
            await conn.commit()

        return ChangeInDB.model_validate(row)

    async def update_commit_pushed(self, id_: int, commit_pushed: bool) -> ChangeInDB:
        return await self._update_one(id_, commit_pushed=commit_pushed)

    async def update_merge_request_id(self, id_: int, merge_request_id: str | None) -> ChangeInDB:
        return await self._update_one(id_, merge_request_id=merge_request_id)

    async def _update_one(self, id_: int, **kwargs) -> ChangeInDB:
        query = update(change).values(**kwargs).where(change.c.id == id_).returning(*change.columns)
        async with self.engine.connect() as conn:
            result = await conn.execute(query)

            row = result.one()
            await conn.commit()

        return ChangeInDB.model_validate(row)

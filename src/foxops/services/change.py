import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import foxops.engine as fengine
from foxops.database import DAL
from foxops.database.repositories.change import (
    ChangeRepository,
    ChangeType,
    IncarnationHasNoChangesError,
)
from foxops.external.git import GitError
from foxops.hosters import Hoster
from foxops.hosters.types import MergeRequestStatus
from foxops.models.change import ChangeWithDirectCommit
from foxops.utils import get_logger


class ChangeRejectedDueToNoChanges(Exception):
    pass


class ChangeRejectedDueToConflicts(Exception):
    def __init__(self, conflicting_paths: list[Path], deleted_paths: list[Path]):
        self.conflicting_paths = conflicting_paths
        self.deleted_paths = deleted_paths


class ChangeFailed(Exception):
    pass


class IncompleteChange(Exception):
    pass


class ChangeService:
    def __init__(self, hoster: Hoster, incarnation_repository: DAL, change_repository: ChangeRepository):
        self._hoster = hoster
        self._change_repository = change_repository
        self._incarnation_repository = incarnation_repository

        self._log = get_logger("change_service")

    async def initialize_legacy_incarnation(self, incarnation_id: int) -> ChangeWithDirectCommit:
        """
        Initialize a legacy incarnation.

        Legacy incarnations are incarnations that were created before the change service was
        introduced. This method will create the first change for the given incarnation.
        """

        # prevent from initializing an incarnation that already has a change history
        try:
            await self.get_latest_change_for_incarnation(incarnation_id)
        except IncarnationHasNoChangesError:
            pass
        else:
            raise ChangeFailed("Incarnation was already initialized for the changes datamodel")

        # verify there are no changes pending currently
        incarnation = await self._incarnation_repository.get_incarnation(incarnation_id)
        if incarnation.merge_request_id is not None:
            mr_status = await self._hoster.get_merge_request_status(
                incarnation.incarnation_repository, incarnation.merge_request_id
            )
            if mr_status != MergeRequestStatus.MERGED:
                raise ChangeFailed(
                    f"Cannot initialize legacy incarnation {incarnation_id} because it has "
                    f"a pending merge request: {incarnation.merge_request_id}. "
                    f"Please first clean up all pending foxops merge requests and then "
                    f"manually set the `merge_request_id` column to NULL."
                )

        commit_sha, incarnation_state = await self._hoster.get_incarnation_state(
            incarnation.incarnation_repository, incarnation.target_directory
        )
        if incarnation_state is None:
            raise ChangeFailed(
                f"Cannot initialize legacy incarnation {incarnation_id} because it does not have a .fengine.yaml file. "
                f"This is NOT expected at this stage. Please investigate."
            )

        change_in_db = await self._change_repository.create_change(
            incarnation_id=incarnation_id,
            revision=1,
            change_type=ChangeType.DIRECT,
            commit_sha=commit_sha,
            commit_pushed=True,
            requested_version=incarnation_state.template_repository_version,
            requested_data=json.dumps(incarnation_state.template_data),
        )

        return await self.get_change(change_in_db.id)

    async def create_change_direct(
        self, incarnation_id: int, requested_version: str | None, requested_data: dict[str, str] | None
    ) -> ChangeWithDirectCommit:
        """
        Perform a DIRECT change on the given incarnation.

        Direct changes are changes that are not performed via a merge request, but instead, directly
        pushed to the default branch.
        """

        if requested_version is None and requested_data is None:
            raise ChangeRejectedDueToNoChanges("Either requested_version or requested_data must be set.")

        incarnation = await self._incarnation_repository.get_incarnation(incarnation_id)
        last_change = await self.get_latest_change_for_incarnation(incarnation_id)

        to_version = requested_version or last_change.requested_version
        to_data = requested_data or last_change.requested_data

        incarnation_repo_cm = self._hoster.cloned_repository(incarnation.incarnation_repository)

        # Fetch the template repository
        # NOTE (ahg, 01/2023): Ideally, in the future we can just read this from the DB
        async with incarnation_repo_cm as local_incarnation_repository:
            incarnation_state = fengine.load_incarnation_state(local_incarnation_repository.directory / ".fengine.yaml")

        template_repo_cm = self._hoster.cloned_repository(
            incarnation_state.template_repository,
            bare=True,
        )
        async with (
            incarnation_repo_cm as local_incarnation_repository,
            template_repo_cm as local_template_repository,
        ):
            (
                update_performed,
                updated_incarnation_state,
                patch_result,
            ) = await fengine.update_incarnation_from_git_template_repository(
                template_git_repository=local_template_repository.directory,
                update_template_repository_version=to_version,
                update_template_data=to_data,
                incarnation_root_dir=(local_incarnation_repository.directory / incarnation.target_directory),
                diff_patch_func=fengine.diff_and_patch,
            )

            if not update_performed:
                raise ChangeRejectedDueToNoChanges()
            if patch_result and patch_result.has_errors():
                raise ChangeRejectedDueToConflicts(patch_result.conflicts, patch_result.deleted)

            await local_incarnation_repository.commit_all(f"foxops: updating incarnation to version {to_version}")
            commit_sha = await local_incarnation_repository.head()

            # now comes the tricky part:
            # Making the following logic resilient to failures at any stage (crashes, DB connection failures, ...)
            # 1. We will create the change object in the database with commit_pushed=False
            # 2. We will push the commit to the incarnation repository
            # 3. We will update the change object in the database with commit_pushed=True
            #
            # This will guarantee, that we never push a commit to the incarnation repository, that is not
            # referenced in the database.
            #
            # Records in the database with commit_pushed=False are in an "invalid intermediate state"
            # and can be cleaned:
            # - they can be removed, if the referenced commit is not present in the incarnation repository
            # - they can be updated to commit_pushed=True,
            #   if the referenced commit is present in the incarnation repository

            # We also explicitly set the revision number here which we are expecting.
            # This serves as a locking mechanism, because a parallel change would result in a unique constraint
            # violation on the revision number.
            change_in_db = await self._change_repository.create_change(
                incarnation_id=incarnation_id,
                revision=last_change.revision + 1,
                change_type=ChangeType.DIRECT,
                commit_sha=commit_sha,
                commit_pushed=False,
                requested_version=to_version,
                requested_data=json.dumps(to_data),
            )
            # FIXME: Add cleanup task

            try:
                await local_incarnation_repository.push()
            except GitError as e:
                self._log.exception(
                    "Failed to push commit to incarnation repository. Removing change from database.",
                    change_id=change_in_db.id,
                )
                await self._change_repository.delete_change(change_in_db.id)

                raise ChangeFailed from e
            else:
                change_in_db = await self._change_repository.update_change_commit_pushed(change_in_db.id, True)

        return await self.get_change(change_in_db.id)

    async def update_incomplete_change(self, change_id: int) -> None:
        """
        Updates an incomplete change (commit_pushed=False) to the latest state.

        Either by updating the flag (if the commit exists in Git) or by deleting the change object.
        """

        change = await self._change_repository.get_change(change_id)

        # don't touch if the change is very new - the git push might still be in progress
        if change.created_at > datetime.now(timezone.utc) - timedelta(minutes=1):
            return

        incarnation = await self._incarnation_repository.get_incarnation(change.incarnation_id)

        commit_exists = await self._hoster.does_commit_exist(incarnation.incarnation_repository, change.commit_sha)
        if commit_exists:
            await self._change_repository.update_change_commit_pushed(change_id, True)
        else:
            await self._change_repository.delete_change(change_id)

    async def get_change(self, change_id: int) -> ChangeWithDirectCommit:
        """
        Returns a change object for the given change ID.
        """

        change = await self._change_repository.get_change(change_id)
        if not change.commit_pushed:
            raise IncompleteChange()

        return ChangeWithDirectCommit(
            id=change.id,
            incarnation_id=change.incarnation_id,
            revision=change.revision,
            requested_version=change.requested_version,
            requested_data=json.loads(change.requested_data),
            created_at=change.created_at,
            commit_sha=change.commit_sha,
        )

    async def get_latest_change_for_incarnation(self, incarnation_id: int) -> ChangeWithDirectCommit:
        """
        Returns the latest change (highest revision) for the given incarnation.

        Be aware that this is only at the time of calling this function.
        New changes might come in between getting this response and doing other actions.
        """

        last_change = await self._change_repository.get_latest_change_for_incarnation(incarnation_id)
        return await self.get_change(last_change.id)

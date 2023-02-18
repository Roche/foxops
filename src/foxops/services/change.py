import inspect
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import AsyncIterator, Mapping

import foxops.engine as fengine
from foxops.database import DAL
from foxops.database.repositories.change import (
    ChangeRepository,
    ChangeType,
    IncarnationHasNoChangesError,
)
from foxops.engine.patching.git_diff_patch import PatchResult
from foxops.external.git import GitError, GitRepository
from foxops.hosters import Hoster
from foxops.hosters.types import MergeRequestStatus
from foxops.models.change import Change
from foxops.reconciliation.utils import generate_foxops_branch_name
from foxops.utils import get_logger


class IncarnationAlreadyExists(Exception):
    pass


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


@dataclass
class _PreparedChangeEnvironment:
    """
    Represents a locally checked out incarnation repository, where a change was applied.
    Contains metadata about the change that was applied (like the branch name and commit sha that contains it).
    """

    incarnation_repository: GitRepository
    incarnation_repository_identifier: str
    incarnation_repository_default_branch: str

    to_version_hash: str
    to_version: str
    to_data: dict[str, str]
    expected_revision: int

    branch_name: str
    commit_sha: str
    patch_result: PatchResult


class ChangeService:
    def __init__(self, hoster: Hoster, incarnation_repository: DAL, change_repository: ChangeRepository):
        self._hoster = hoster
        self._change_repository = change_repository
        self._incarnation_repository = incarnation_repository

        self._log = get_logger("change_service")

    async def create_incarnation(
        self,
        incarnation_repository: str,
        template_repository: str,
        template_repository_version: str,
        template_data: dict[str, str],
        target_directory: str = ".",
    ) -> Change:
        incarnation_state = await self._hoster.get_incarnation_state(incarnation_repository, target_directory)
        if incarnation_state is not None:
            raise IncarnationAlreadyExists(f"Cannot create incarnation because it already exists: {incarnation_state}")

        async with (
            self._hoster.cloned_repository(template_repository, refspec=template_repository_version) as template_git,
            self._hoster.cloned_repository(incarnation_repository) as incarnation_git,
        ):
            incarnation_state = await fengine.initialize_incarnation(
                template_root_dir=template_git.directory,
                template_repository=template_repository,
                template_repository_version=template_repository_version,
                template_data=template_data,
                incarnation_root_dir=incarnation_git.directory / target_directory,
            )

            await incarnation_git.commit_all(
                f"foxops: initializing incarnation from template {template_repository} "
                f"@ {template_repository_version}"
            )
            commit_sha = await incarnation_git.head()

            change = await self._change_repository.create_incarnation_with_first_change(
                incarnation_repository=incarnation_repository,
                target_directory=target_directory,
                commit_sha=commit_sha,
                requested_version_hash=incarnation_state.template_repository_version_hash,
                requested_version=template_repository_version,
                requested_data=json.dumps(template_data),
            )

            try:
                await incarnation_git.push()
            except GitError as e:
                self._log.exception(
                    "Failed to push commit to incarnation repository. Removing change from database.",
                    change_id=change.id,
                )
                await self._change_repository.delete_change(change.id)

                raise ChangeFailed from e
            else:
                change = await self._change_repository.update_commit_pushed(change.id, True)

        return await self.get_change(change.id)

    async def initialize_legacy_incarnation(self, incarnation_id: int) -> Change:
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

        get_incarnation_state_result = await self._hoster.get_incarnation_state(
            incarnation.incarnation_repository, incarnation.target_directory
        )
        if get_incarnation_state_result is None:
            raise ChangeFailed(
                f"Cannot initialize legacy incarnation {incarnation_id} because it does not have a .fengine.yaml file. "
                f"This is NOT expected at this stage. Please investigate."
            )
        commit_sha, incarnation_state = get_incarnation_state_result

        change_in_db = await self._change_repository.create_change(
            incarnation_id=incarnation_id,
            revision=1,
            change_type=ChangeType.DIRECT,
            commit_sha=commit_sha,
            commit_pushed=True,
            requested_version_hash=incarnation_state.template_repository_version_hash,
            requested_version=incarnation_state.template_repository_version,
            requested_data=json.dumps(incarnation_state.template_data),
        )

        return await self.get_change(change_in_db.id)

    async def create_change_direct(
        self, incarnation_id: int, requested_version: str | None = None, requested_data: dict[str, str] | None = None
    ) -> Change:
        """
        Perform a DIRECT change on the given incarnation.

        Direct changes are changes that are not performed via a merge request, but instead, directly
        pushed to the default branch.
        """

        # https://youtrack.jetbrains.com/issue/PY-36444
        env: _PreparedChangeEnvironment
        async with self._prepared_change_environment(incarnation_id, requested_version, requested_data) as env:
            # because we want to apply the change without an MR
            # ... let's merge the change directly into the default branch
            await env.incarnation_repository.checkout_branch(env.incarnation_repository_default_branch)
            await env.incarnation_repository.merge_ff_only(env.branch_name)

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
                revision=env.expected_revision,
                change_type=ChangeType.DIRECT,
                commit_sha=env.commit_sha,
                commit_pushed=False,
                requested_version_hash=env.to_version_hash,
                requested_version=env.to_version,
                requested_data=json.dumps(env.to_data),
            )

            await self._push_change_commit_and_update_database(env.incarnation_repository, change_in_db.id)

        return await self.get_change(change_in_db.id)

    async def create_change_merge_request(
        self,
        incarnation_id: int,
        requested_version: str | None = None,
        requested_data: dict[str, str] | None = None,
        automerge: bool = False,
    ):
        # https://youtrack.jetbrains.com/issue/PY-36444
        env: _PreparedChangeEnvironment
        async with self._prepared_change_environment(incarnation_id, requested_version, requested_data) as env:
            change_in_db = await self._change_repository.create_change(
                incarnation_id=incarnation_id,
                revision=env.expected_revision,
                change_type=ChangeType.MERGE_REQUEST,
                commit_sha=env.commit_sha,
                commit_pushed=False,
                requested_version_hash=env.to_version_hash,
                requested_version=env.to_version,
                requested_data=json.dumps(env.to_data),
                merge_request_branch_name=env.branch_name,
            )

            await self._push_change_commit_and_update_database(env.incarnation_repository, change_in_db.id)

        if env.patch_result.has_errors():
            title = f"🚧 - CONFLICT: Update to {env.to_version}"
            description = _construct_merge_request_conflict_description(
                conflict_files=env.patch_result.conflicts,
                deleted_files=env.patch_result.deleted,
            )
            automerge = False
        else:
            title = f"Update to {env.to_version}"
            description = "Foxops detected no conflicts when applying this change."

        _, merge_request_id = await self._hoster.merge_request(
            incarnation_repository=env.incarnation_repository_identifier,
            source_branch=env.branch_name,
            title=title,
            description=description,
            with_automerge=automerge,
        )

        await self._change_repository.update_merge_request_id(change_in_db.id, merge_request_id)

        return await self.get_change(change_in_db.id)

    async def update_incomplete_change(self, change_id: int) -> None:
        """
        Updates an incomplete change (commit_pushed=False) to the latest state.

        Either by updating the flag (if the commit exists in Git) or by deleting the change object.
        """

        # FIXME: needs an update to also work with MR changes

        change = await self._change_repository.get_change(change_id)
        if change.commit_pushed:
            self._log.debug("Change is already complete (commit_pushed=True). Skipping.", change_id=change_id)
            return

        # don't touch if the change is very new - the git push might still be in progress
        if change.created_at > datetime.now(timezone.utc) - timedelta(minutes=1):
            return

        incarnation = await self._incarnation_repository.get_incarnation(change.incarnation_id)

        commit_exists = await self._hoster.does_commit_exist(incarnation.incarnation_repository, change.commit_sha)
        if commit_exists:
            await self._change_repository.update_commit_pushed(change_id, True)
        else:
            await self._change_repository.delete_change(change_id)

    async def get_change(self, change_id: int) -> Change:
        """
        Returns a change object for the given change ID.
        """

        change = await self._change_repository.get_change(change_id)
        if not change.commit_pushed:
            raise IncompleteChange(
                "the given change is in an incomplete state (commit_pushed=False). "
                "Try calling update_incomplete_change(change_id) first."
            )

        return Change(
            id=change.id,
            incarnation_id=change.incarnation_id,
            revision=change.revision,
            requested_version_hash=change.requested_version_hash,
            requested_version=change.requested_version,
            requested_data=json.loads(change.requested_data),
            created_at=change.created_at,
            commit_sha=change.commit_sha,
        )

    async def get_latest_change_for_incarnation(self, incarnation_id: int) -> Change:
        """
        Returns the latest change (the highest revision) for the given incarnation.

        Be aware that this is only at the time of calling this function.
        New changes might come in between getting this response and doing other actions.
        """

        last_change = await self._change_repository.get_latest_change_for_incarnation(incarnation_id)
        return await self.get_change(last_change.id)

    @asynccontextmanager
    async def _prepared_change_environment(
        self, incarnation_id: int, requested_version: str | None, requested_data: Mapping[str, str] | None
    ) -> AsyncIterator[_PreparedChangeEnvironment]:
        """
        This method checks out the incarnation repository, prepares a branch that contains the update and commits.
        """
        if requested_version is None and requested_data is None:
            raise ChangeRejectedDueToNoChanges("Either requested_version or requested_data must be set.")

        incarnation = await self._incarnation_repository.get_incarnation(incarnation_id)
        last_change = await self.get_latest_change_for_incarnation(incarnation_id)

        to_version = last_change.requested_version
        if requested_version is not None:
            to_version = requested_version

        to_data = last_change.requested_data.copy()
        if requested_data is not None:
            to_data.update(requested_data)

        incarnation_repo_metadata = await self._hoster.get_repository_metadata(incarnation.incarnation_repository)

        # Fetch the template repository
        # NOTE (ahg, 01/2023): Ideally, in the future we can just read this from the DB
        async with self._hoster.cloned_repository(incarnation.incarnation_repository) as local_incarnation_repository:
            incarnation_state = fengine.load_incarnation_state(
                local_incarnation_repository.directory / incarnation.target_directory / ".fengine.yaml"
            )

        async with (
            self._hoster.cloned_repository(incarnation.incarnation_repository) as local_incarnation_repository,
            self._hoster.cloned_repository(
                incarnation_state.template_repository, bare=True
            ) as local_template_repository,
        ):
            branch_name = generate_foxops_branch_name(
                prefix="update-to",
                target_directory=incarnation.target_directory,
                template_repository_version=to_version,
            )
            await local_incarnation_repository.create_and_checkout_branch(branch_name, exist_ok=False)

            (update_performed, _, patch_result,) = await fengine.update_incarnation_from_git_template_repository(
                template_git_repository=local_template_repository.directory,
                update_template_repository_version=to_version,
                update_template_data=to_data,
                incarnation_root_dir=(local_incarnation_repository.directory / incarnation.target_directory),
                diff_patch_func=fengine.diff_and_patch,
            )

            if not update_performed:
                raise ChangeRejectedDueToNoChanges()
            if patch_result is None:
                raise ChangeFailed("Patch result was None. That is unexpected at this stage.")

            await local_incarnation_repository.commit_all(f"foxops: updating incarnation to version {to_version}")
            commit_sha = await local_incarnation_repository.head()

            yield _PreparedChangeEnvironment(
                incarnation_repository=local_incarnation_repository,
                incarnation_repository_identifier=incarnation.incarnation_repository,
                incarnation_repository_default_branch=incarnation_repo_metadata["default_branch"],
                to_version_hash=await local_template_repository.head(),
                to_version=to_version,
                to_data=to_data,
                expected_revision=last_change.revision + 1,
                branch_name=branch_name,
                commit_sha=commit_sha,
                patch_result=patch_result,
            )

    async def _push_change_commit_and_update_database(self, incarnation_git: GitRepository, change_id: int) -> None:
        try:
            await incarnation_git.push()
        except GitError as e:
            self._log.exception(
                "Failed to push commit to incarnation repository. Removing change from database.",
                change_id=change_id,
            )
            await self._change_repository.delete_change(change_id)

            raise ChangeFailed from e
        else:
            await self._change_repository.update_commit_pushed(change_id, True)


def _construct_merge_request_conflict_description(
    conflict_files: list[Path] | None, deleted_files: list[Path] | None
) -> str:
    description_paragraphs = ["Foxops couldn't automatically apply the changes from the template in this incarnation"]

    if conflict_files is not None:
        conflict_files_text = "\n".join([f"- {f}" for f in conflict_files])
        description_paragraphs.append(
            inspect.cleandoc(
                f"""
            The following files were updated in the template repository - and at the same time - also
            **modified** in the incarnation repository. Please resolve the conflicts manually:

            {conflict_files_text}
            """
            )
        )

    if deleted_files is not None:
        deleted_files_text = "\n".join([f"- {f}" for f in deleted_files])
        description_paragraphs.append(
            inspect.cleandoc(
                f"""
            The following files were updated in the template repository but are **no longer
            present** in this incarnation repository. Please resolve the conflicts manually:

            {deleted_files_text}
            """
            )
        )

    return "\n\n".join(description_paragraphs)

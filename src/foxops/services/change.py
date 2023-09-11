import asyncio
import hashlib
import inspect
import json
import shutil
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncIterator

from pydantic import BaseModel

import foxops.engine as fengine
from foxops.database.repositories.change import (
    ChangeRepository,
    ChangeType,
    IncarnationWithChangesSummary,
)
from foxops.database.repositories.incarnation.repository import IncarnationRepository
from foxops.engine import TemplateData
from foxops.engine.patching.git_diff_patch import PatchResult
from foxops.errors import RetryableError
from foxops.external.git import GitError, GitRepository
from foxops.hosters import Hoster
from foxops.hosters.types import MergeRequestStatus
from foxops.models import IncarnationWithDetails
from foxops.models.change import Change, ChangeWithMergeRequest
from foxops.utils import get_logger


class IncarnationAlreadyExists(Exception):
    pass


class IncarnationAlreadyUpgraded(Exception):
    pass


class ChangeRejectedDueToNoChanges(Exception):
    pass


class ChangeRejectedDueToPreviousUnfinishedChange(Exception):
    pass


class ChangeRejectedDueToConflicts(Exception):
    def __init__(self, conflicting_paths: list[Path], deleted_paths: list[Path]):
        self.conflicting_paths = conflicting_paths
        self.deleted_paths = deleted_paths


class IncarnationWithLatestChangeDetails(BaseModel):
    id: int
    incarnation_repository: str
    target_directory: str
    template_repository: str

    revision: int
    type: ChangeType
    requested_version: str
    created_at: datetime

    commit_sha: str
    commit_url: str

    merge_request_id: str | None
    merge_request_url: str | None


class ChangeFailed(Exception):
    pass


class IncompleteChange(Exception):
    pass


class CannotRepairChangeException(Exception):
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
    to_data: TemplateData
    expected_revision: int

    branch_name: str
    commit_sha: str
    patch_result: PatchResult


class ChangeService:
    def __init__(
        self, hoster: Hoster, incarnation_repository: IncarnationRepository, change_repository: ChangeRepository
    ):
        self._hoster = hoster

        self._incarnation_repository = incarnation_repository
        self._change_repository = change_repository

        self._log = get_logger("change_service")

    async def _incarnation_with_latest_change_details_from_dbobj(
        self, dbobj: IncarnationWithChangesSummary
    ) -> IncarnationWithLatestChangeDetails:
        merge_request_url = None
        if dbobj.merge_request_id is not None:
            merge_request_url = await self._hoster.get_merge_request_url(
                dbobj.incarnation_repository, dbobj.merge_request_id
            )

        return IncarnationWithLatestChangeDetails(
            id=dbobj.id,
            incarnation_repository=dbobj.incarnation_repository,
            target_directory=dbobj.target_directory,
            template_repository=dbobj.template_repository,
            revision=dbobj.revision,
            type=dbobj.type,
            requested_version=dbobj.requested_version,
            created_at=dbobj.created_at,
            commit_sha=dbobj.commit_sha,
            commit_url=await self._hoster.get_commit_url(dbobj.incarnation_repository, dbobj.commit_sha),
            merge_request_id=dbobj.merge_request_id,
            merge_request_url=merge_request_url,
        )

    async def list_incarnations(self) -> list[IncarnationWithLatestChangeDetails]:
        return [
            await self._incarnation_with_latest_change_details_from_dbobj(inc)
            async for inc in self._change_repository.list_incarnations_with_changes_summary()
        ]

    async def get_incarnation_by_repo_and_target_directory(
        self, repo: str, target_directory: str
    ) -> IncarnationWithLatestChangeDetails:
        return await self._incarnation_with_latest_change_details_from_dbobj(
            await self._change_repository.get_incarnation_by_repo_and_target_dir(repo, target_directory)
        )

    async def create_incarnation(
        self,
        incarnation_repository: str,
        template_repository: str,
        template_repository_version: str,
        template_data: TemplateData,
        target_directory: str = ".",
    ) -> Change:
        if await self._hoster.get_incarnation_state(incarnation_repository, target_directory) is not None:
            raise IncarnationAlreadyExists("Cannot create incarnation because it already exists")

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
                template_repository=template_repository,
                commit_sha=commit_sha,
                requested_version_hash=incarnation_state.template_repository_version_hash,
                requested_version=template_repository_version,
                requested_data=json.dumps(template_data),
            )

            try:
                await self._push_change_commit_and_update_database(incarnation_git, change.id)
            except ChangeFailed:
                await self._change_repository.delete_incarnation(change.incarnation_id)
                raise

        return await self.get_change(change.id)

    async def reset_incarnation(
        self, incarnation_id: int, override_version: str | None = None, override_data: TemplateData | None = None
    ) -> ChangeWithMergeRequest:
        """
        Resets an incarnation by removing all customizations that were done to it
        ... and bring it back to a pristine state as if it was just created freshly from the template.

        By default, the target version and data is taken from the last change that was successfully applied
        to the incarnation, but they can be overridden. For the data, partial overrides are also allowed.

        Returns the merge request ID that was created.
        """

        incarnation = await self._incarnation_repository.get_by_id(incarnation_id)
        last_change = await self.get_latest_change_for_incarnation_if_completed(incarnation_id)
        if incarnation.template_repository is None:
            raise ValueError("template_repository is None. That should not happen.")

        reset_branch_name = f"foxops-reset-{str(uuid.uuid4())[:8]}"

        to_version = last_change.requested_version
        if override_version is not None:
            to_version = override_version
        to_data = dict(last_change.requested_data)
        if override_data is not None:
            to_data.update(override_data)

        async with (
            self._hoster.cloned_repository(incarnation.template_repository, refspec=to_version) as template_git,
            self._hoster.cloned_repository(incarnation.incarnation_repository) as incarnation_git,
        ):
            await incarnation_git.create_and_checkout_branch(reset_branch_name)
            delete_all_files_in_local_git_repository(incarnation_git.directory / incarnation.target_directory)

            incarnation_state = await fengine.initialize_incarnation(
                template_root_dir=template_git.directory,
                template_repository=incarnation.template_repository,
                template_repository_version=to_version,
                template_data=to_data,
                incarnation_root_dir=incarnation_git.directory / incarnation.target_directory,
            )

            if not await incarnation_git.has_uncommitted_changes():
                raise ChangeRejectedDueToNoChanges("No changes were made to the incarnation. Nothing to reset.")

            await incarnation_git.commit_all(f"foxops: resetting incarnation to version {to_version}")
            commit_sha = await incarnation_git.head()

            change_in_db = await self._change_repository.create_change(
                incarnation_id=incarnation_id,
                revision=last_change.revision + 1,
                change_type=ChangeType.MERGE_REQUEST,
                commit_sha=commit_sha,
                commit_pushed=False,
                requested_version_hash=incarnation_state.template_repository_version_hash,
                requested_version=incarnation_state.template_repository_version,
                requested_data=json.dumps(incarnation_state.template_data),
                merge_request_branch_name=reset_branch_name,
            )

            await self._push_change_commit_and_update_database(incarnation_git, change_in_db.id)

        title = f"↩️ - RESET: To version {to_version}"
        description = (
            "This MR helps to bring back the incarnation to a 'pristine' state, as if it was "
            "just created. Feel free to edit the branch to remove the changes and customizations "
            "which you want to keep before merging!"
        )
        _, merge_request_id = await self._hoster.merge_request(
            incarnation_repository=incarnation.incarnation_repository,
            source_branch=reset_branch_name,
            title=title,
            description=description,
            with_automerge=False,
        )

        await self._change_repository.update_merge_request_id(change_in_db.id, merge_request_id)

        return await self.get_change_with_merge_request(change_in_db.id)

    async def create_change_direct(
        self, incarnation_id: int, requested_version: str | None = None, requested_data: TemplateData | None = None
    ) -> Change:
        """
        Perform a DIRECT change on the given incarnation.

        Direct changes are changes that are not performed via a merge request, but instead, directly
        pushed to the default branch.

        Initiating a change via this method guarantees that there are no commits pushed to the incarnation repository
        that are not recorded in the foxops database.
        """

        # https://youtrack.jetbrains.com/issue/PY-36444
        env: _PreparedChangeEnvironment
        async with self._prepared_change_environment(incarnation_id, requested_version, requested_data) as env:
            # because we want to apply the change without an MR
            # ... let's merge the change directly into the default branch
            await env.incarnation_repository.checkout_branch(env.incarnation_repository_default_branch)
            await env.incarnation_repository.merge(env.branch_name, ff_only=True)

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

            # if some failure happens after this point, the database object can be cleaned
            # by the update_incomplete_change() method.
            await self._push_change_commit_and_update_database(env.incarnation_repository, change_in_db.id)

        return await self.get_change(change_in_db.id)

    async def create_change_merge_request(
        self,
        incarnation_id: int,
        requested_version: str | None = None,
        requested_data: TemplateData | None = None,
        automerge: bool = False,
    ) -> ChangeWithMergeRequest:
        """
        Perform a MERGE_REQUEST change on the given incarnation.

        Such a change will result in a merge request being created on the incarnation repository. The merge request
        can be merged manually or automatically (if the `automerge` parameter is set to `True`).
        """

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

        return await self.get_change_with_merge_request(change_in_db.id)

    async def list_changes(self, incarnation_id: int) -> list[Change | ChangeWithMergeRequest]:
        changes = []
        for change_in_db in await self._change_repository.list_changes(incarnation_id):
            if change_in_db.type == ChangeType.DIRECT:
                changes.append(await self.get_change(change_in_db.id))
            elif change_in_db.type == ChangeType.MERGE_REQUEST:
                changes.append(await self.get_change_with_merge_request(change_in_db.id))
            else:
                raise ValueError(f"Unknown change type {change_in_db.type}")

        return changes

    async def update_incomplete_change(self, change_id: int) -> None:
        """
        Updates an incomplete change (commit not pushed, MR not created) to the latest state.

        Either by updating the flag (if the commit exists in Git) or by deleting the change object.
        """

        change = await self._change_repository.get_change(change_id)
        log = self._log.bind(change_id=change.id)

        match change.type:
            case ChangeType.DIRECT:
                if change.commit_pushed:
                    log.debug("Change is already complete (commit_pushed=True). Skipping.")
                    return
            case ChangeType.MERGE_REQUEST:
                if change.commit_pushed and change.merge_request_id is not None:
                    log.debug("Change is already complete (commit_pushed=True, merge_request_id set). Skipping.")
                    return
            case _:
                raise Exception(f"unsupported change type {change.type}")

        incarnation = await self._incarnation_repository.get_by_id(change.incarnation_id)

        commit_exists = await self._hoster.does_commit_exist(incarnation.incarnation_repository, change.commit_sha)
        if not commit_exists:
            await self._change_repository.delete_change(change.id)
            return

        await self._change_repository.update_commit_pushed(change.id, True)

        if change.type == ChangeType.MERGE_REQUEST:
            assert change.merge_request_branch_name is not None
            merge_request_id = await self._hoster.has_pending_incarnation_merge_request(
                incarnation.incarnation_repository, change.merge_request_branch_name
            )

            if merge_request_id is None:
                raise CannotRepairChangeException(
                    "the commit and branch for the change exist, but the MR does not. "
                    f"Please go ahead and manually create a merge request for "
                    f"branch '{change.merge_request_branch_name}', then rerun update_incomplete_change()"
                )

            await self._change_repository.update_merge_request_id(change.id, merge_request_id)

    async def get_change_type(self, change_id: int) -> ChangeType:
        change = await self._change_repository.get_change(change_id)
        return change.type

    async def get_change_id_by_revision(self, incarnation_id: int, revision: int) -> int:
        change = await self._change_repository.get_change_by_revision(incarnation_id, revision)
        return change.id

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

    async def get_change_with_merge_request(self, change_id: int) -> ChangeWithMergeRequest:
        change_basic = await self.get_change(change_id)

        change_in_db = await self._change_repository.get_change(change_id)
        incarnation_in_db = await self._incarnation_repository.get_by_id(change_in_db.incarnation_id)

        if change_in_db.type != ChangeType.MERGE_REQUEST:
            raise ValueError(f"Change {change_id} is not a merge request change.")
        assert change_in_db.merge_request_id is not None
        assert change_in_db.merge_request_branch_name is not None

        status = await self._hoster.get_merge_request_status(
            incarnation_repository=incarnation_in_db.incarnation_repository,
            merge_request_id=change_in_db.merge_request_id,
        )

        return ChangeWithMergeRequest(
            **change_basic.model_dump(),
            merge_request_id=change_in_db.merge_request_id,
            merge_request_branch_name=change_in_db.merge_request_branch_name,
            merge_request_status=status,
        )

    async def get_latest_change_id_for_incarnation(self, incarnation_id: int) -> int:
        """
        Returns the latest change (the highest revision) for the given incarnation.

        Be aware that this is only at the time of calling this function.
        New changes might come in between getting this response and doing other actions.
        """

        last_change = await self._change_repository.get_latest_change_for_incarnation(incarnation_id)
        return last_change.id

    async def get_latest_change_for_incarnation_if_completed(
        self, incarnation_id: int
    ) -> Change | ChangeWithMergeRequest:
        change_id = await self.get_latest_change_id_for_incarnation(incarnation_id)

        change_type = await self.get_change_type(change_id)
        if change_type == ChangeType.MERGE_REQUEST:
            change = await self.get_change_with_merge_request(change_id)
            if change.merge_request_status not in (MergeRequestStatus.CLOSED, MergeRequestStatus.MERGED):
                raise ChangeRejectedDueToPreviousUnfinishedChange(
                    "There is still an open MR for the previous change. Please close it first."
                )

            return change
        elif change_type == ChangeType.DIRECT:
            return await self.get_change(change_id)

        raise ValueError(f"Unknown change type {change_type}")

    async def get_incarnation_with_details(self, incarnation_id: int) -> IncarnationWithDetails:
        """
        Returns an IncarnationWithDetails object for the given incarnation ID.
        """

        incarnation = await self._incarnation_repository.get_by_id(incarnation_id)

        change_id = await self.get_latest_change_id_for_incarnation(incarnation_id)
        change_type = await self.get_change_type(change_id)

        merge_request_id: str | None = None
        merge_request_url: str | None = None
        merge_request_status: MergeRequestStatus | None = None

        change: Change | ChangeWithMergeRequest
        if change_type == ChangeType.MERGE_REQUEST:
            change = await self.get_change_with_merge_request(change_id)

            merge_request_id = change.merge_request_id
            merge_request_status = await self._hoster.get_merge_request_status(
                incarnation.incarnation_repository, merge_request_id
            )
            merge_request_url = await self._hoster.get_merge_request_url(
                incarnation.incarnation_repository, merge_request_id
            )
        elif change_type == ChangeType.DIRECT:
            change = await self.get_change(change_id)
        else:
            raise ValueError(f"Unknown change type {change_type}")

        status = await self._hoster.get_reconciliation_status(
            incarnation_repository=incarnation.incarnation_repository,
            target_directory=incarnation.target_directory,
            commit_sha=change.commit_sha,
            merge_request_id=merge_request_id,
            pipeline_timeout=timedelta(seconds=10),
        )

        return IncarnationWithDetails(
            id=incarnation.id,
            incarnation_repository=incarnation.incarnation_repository,
            target_directory=incarnation.target_directory,
            commit_sha=change.commit_sha,
            commit_url=await self._hoster.get_commit_url(incarnation.incarnation_repository, change.commit_sha),
            merge_request_id=merge_request_id,
            merge_request_url=merge_request_url,
            merge_request_status=merge_request_status,
            status=status,
            template_repository=incarnation.template_repository,
            template_repository_version=change.requested_version,
            template_repository_version_hash=change.requested_version_hash,
            template_data=change.requested_data,
        )

    @asynccontextmanager
    async def _prepared_change_environment(
        self, incarnation_id: int, requested_version: str | None, requested_data: TemplateData | None
    ) -> AsyncIterator[_PreparedChangeEnvironment]:
        """
        This method checks out the incarnation repository, prepares a branch that contains the update and commits.
        """
        incarnation = await self._incarnation_repository.get_by_id(incarnation_id)

        if incarnation.template_repository is None:
            raise Exception("upgrade failed. Should not happen.")

        # if the previous change was of type merge request and is still open, we dont want to continue
        last_change = await self.get_latest_change_for_incarnation_if_completed(incarnation_id)

        to_version = last_change.requested_version
        if requested_version is not None:
            to_version = requested_version

        to_data = dict(last_change.requested_data)
        if requested_data is not None:
            to_data.update(requested_data)

        incarnation_repo_metadata = await self._hoster.get_repository_metadata(incarnation.incarnation_repository)

        async with (
            self._hoster.cloned_repository(incarnation.incarnation_repository) as local_incarnation_repository,
            self._hoster.cloned_repository(incarnation.template_repository, bare=True) as local_template_repository,
        ):
            branch_name = generate_foxops_branch_name(
                prefix="update-to",
                target_directory=incarnation.target_directory,
                template_repository_version=to_version,
            )
            await local_incarnation_repository.create_and_checkout_branch(branch_name, exist_ok=False)

            (
                update_performed,
                incarnation_state,
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
                to_data=incarnation_state.template_data,
                expected_revision=last_change.revision + 1,
                branch_name=branch_name,
                commit_sha=commit_sha,
                patch_result=patch_result,
            )

    async def _push_change_commit_and_update_database(self, incarnation_git: GitRepository, change_id: int) -> None:
        # the push might fail when other changes are pushed in the meantime. We need to rebase/retry in that case
        last_exception = None
        for attempt in range(10):
            log = self._log.bind(change_id=change_id, attempt=attempt)

            try:
                await incarnation_git.push()
            except RetryableError as e:
                log.info(
                    "Failed to push commit to incarnation repository. "
                    "But a retry is possible (possibly someone else pushed in the meantime)."
                )
                last_exception = e

                await incarnation_git.pull(rebase=True)

                new_commit_sha = await incarnation_git.head()
                await self._change_repository.update_commit_sha(change_id, new_commit_sha)

                await asyncio.sleep(3)
                continue
            except GitError as e:
                log.exception("Failed to push commit to incarnation repository. Removing change from database.")
                await self._change_repository.delete_change(change_id)

                raise ChangeFailed from e

            await self._change_repository.update_commit_pushed(change_id, True)
            return
        else:
            if last_exception:
                self._log.error("last exception", last_exception=last_exception)
            await self._change_repository.delete_change(change_id)
            raise ChangeFailed("Failed to push commit to incarnation repository. Retries exceeded.")


def _construct_merge_request_conflict_description(
    conflict_files: list[Path] | None, deleted_files: list[Path] | None
) -> str:
    description_paragraphs = ["Foxops couldn't automatically apply the changes from the template in this incarnation"]

    if conflict_files:
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

    if deleted_files:
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


def delete_all_files_in_local_git_repository(directory: Path) -> None:
    for file in directory.glob("*"):
        if file.name == ".git":
            continue

        if file.is_dir():
            shutil.rmtree(file)
        else:
            file.unlink()


def generate_foxops_branch_name(prefix: str, target_directory: str, template_repository_version: str) -> str:
    target_directory_hash = hashlib.sha1(target_directory.encode("utf-8")).hexdigest()[:7]
    return f"foxops/{prefix}-{target_directory_hash}-{template_repository_version}"

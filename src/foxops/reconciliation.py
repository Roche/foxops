import asyncio
import glob
import hashlib
import os
import uuid
from enum import IntEnum, auto
from pathlib import Path

from structlog.stdlib import BoundLogger
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from foxops.engine import (
    FVARS_FILENAME,
    diff_and_patch,
    initialize_incarnation,
    load_incarnation_state_from_string,
    update_incarnation_from_git_template_repository,
)
from foxops.engine.update import get_data_mismatch
from foxops.errors import RetryableError
from foxops.external.git import GitRepository, TemporaryGitRepository
from foxops.external.gitlab import AsyncGitlabClient, GitlabNotFoundException
from foxops.logging import get_logger
from foxops.models import (
    DesiredIncarnationStateConfig,
    IncarnationRemoteGitRepositoryState,
)

logger = get_logger("reconciliation")


class ReconciliationState(IntEnum):
    UNCHANGED = auto()
    CHANGED = auto()
    CHANGED_WITH_CONFLICT = auto()
    FAILED = auto()
    UNSUPPORTED = auto()


async def get_actual_incarnation_state(
    gitlab: AsyncGitlabClient,
    desired_incarnation_state: DesiredIncarnationStateConfig,
) -> IncarnationRemoteGitRepositoryState | None:
    try:
        gitlab_project = await gitlab.project_get(
            desired_incarnation_state.gitlab_project
        )
    except GitlabNotFoundException:
        return None

    default_branch = gitlab_project.get("default_branch") or "main"
    fengine_path = os.path.normpath(
        desired_incarnation_state.target_directory / ".fengine.yaml"
    )

    try:
        # TODO(TF): we should make the default branch configurable.
        actual_incarnation_state_raw = (
            await gitlab.project_repository_files_get_content(
                gitlab_project["id"],
                default_branch,
                fengine_path,
            )
        )
    except GitlabNotFoundException:
        return IncarnationRemoteGitRepositoryState(
            gitlab_project_id=gitlab_project["id"],
            remote_url=gitlab_project["http_url_to_repo"],
            default_branch=default_branch,
            incarnation_directory=desired_incarnation_state.target_directory,
        )
    else:
        actual_incarnation_state = load_incarnation_state_from_string(
            actual_incarnation_state_raw.decode("utf-8")
        )

    return IncarnationRemoteGitRepositoryState(
        gitlab_project_id=gitlab_project["id"],
        remote_url=gitlab_project["http_url_to_repo"],
        default_branch=default_branch,
        incarnation_directory=desired_incarnation_state.target_directory,
        incarnation_state=actual_incarnation_state,
    )


async def reconcile(
    gitlab: AsyncGitlabClient,
    desired_incarnation_states: list[DesiredIncarnationStateConfig],
    parallelism: int,
) -> list[ReconciliationState]:
    """Reconcile the given projects to a desired incarnation state.

    The `parallelism` parameter controls how many projects are reconciled in parallel.
    However, it's not a real parallelism "pool", but basically batches the reconciliations
    in `parallelism` sized batches.
    """
    reconciliation_states = []

    async def __reconcile_project(
        desired_incarnation_state: DesiredIncarnationStateConfig,
    ):
        log = logger.bind(desired_incarnation_state=desired_incarnation_state)
        try:
            reconciliation_state = await reconcile_project(
                gitlab, desired_incarnation_state
            )
        except Exception as exc:
            log.exception(
                f"failed to reconcile project {desired_incarnation_state.gitlab_project}: {exc}"
            )
            reconciliation_state = ReconciliationState.FAILED
        return reconciliation_state

    for group in (
        desired_incarnation_states[i : i + parallelism]
        for i in range(0, len(desired_incarnation_states), parallelism)
    ):
        logger.info(f"scheduling reconciliation for {len(group)} projects")
        group_reconciliation_states = await asyncio.gather(
            *[
                __reconcile_project(desired_incarnation_state)
                for desired_incarnation_state in group
            ]
        )
        reconciliation_states.extend(group_reconciliation_states)

    return reconciliation_states


@retry(
    retry=retry_if_exception_type(RetryableError),
    # NOTE: "why retry 4 times?" ... well, go figure ;)
    stop=stop_after_attempt(4),
)
async def reconcile_project(
    gitlab: AsyncGitlabClient,
    desired_incarnation_state: DesiredIncarnationStateConfig,
) -> ReconciliationState:
    reconciliation_uuid = str(uuid.uuid4())[:8]
    log = logger.bind(
        reconciliation_uuid=reconciliation_uuid,
        gitlab_project=desired_incarnation_state.gitlab_project,
        target_directory=desired_incarnation_state.target_directory,
    )
    actual_incarnation_state = await get_actual_incarnation_state(
        gitlab, desired_incarnation_state
    )

    if actual_incarnation_state is None:
        log.error(
            "couldn't find the incarnation project on Gitlab. Make sure it exists before running foxops"
        )
        return ReconciliationState.FAILED

    # NOTE(TF): clone incarnation and updated template remote git repository to a local folder for further operations
    async with TemporaryGitRepository(
        logger=log,
        source=actual_incarnation_state.remote_url,
        username="__token__",
        password=gitlab.token,
    ) as local_incarnation_git_repository, TemporaryGitRepository(
        logger=log,
        source=desired_incarnation_state.template_repository,
        username="__token__",
        password=gitlab.token,
        refspec=desired_incarnation_state.template_repository_version,
    ) as local_template_git_repository:
        # check for incarnation is still empty and an initialization is required
        if actual_incarnation_state.incarnation_state is None:
            log.info(
                "incarnation has not yet been initialized, initializing it now ..."
            )
            return await initialize_incarnation_from_template(
                gitlab,
                actual_incarnation_state=actual_incarnation_state,
                desired_incarnation_state=desired_incarnation_state,
                local_template_repository=local_template_git_repository,
                local_incarnation_repository=local_incarnation_git_repository,
                logger=log,
            )

        # check if the existing incarnation requires an update
        if (
            actual_incarnation_state.incarnation_state.template_repository
            != desired_incarnation_state.template_repository
        ):
            log.error("changing the template repository is not supported")
            return ReconciliationState.UNSUPPORTED

        # check if an existing incarnation has already been updated and pushed, but apparently not merged yet.
        update_branch_name = generate_foxops_branch_name(
            "update-to",
            desired_incarnation_state.target_directory,
            desired_incarnation_state.template_repository_version,
        )
        update_branches = await gitlab.project_repository_branches_list(
            actual_incarnation_state.gitlab_project_id, f"^{update_branch_name}"
        )
        if len(update_branches) > 0:
            log.info(
                f"branch for an update to {desired_incarnation_state.template_repository_version} already exists. Skipping update"
            )
            return ReconciliationState.UNCHANGED

        needs_update = False
        # check if the existing incarnation requires an update because of a template version mismatch
        if (
            actual_incarnation_state.incarnation_state.template_repository_version
            != desired_incarnation_state.template_repository_version
        ):
            needs_update = True
            log.info(
                "reconciliation update is required because of a version mismatch",
                actual_template_version=actual_incarnation_state.incarnation_state.template_repository_version,
                desired_template_version=desired_incarnation_state.template_repository_version,
            )

        # check if it really(tm) is the same version by checking the exact version hash
        if not needs_update:
            if (
                actual_incarnation_state.incarnation_state.template_repository_version_hash
                != await local_template_git_repository.head()
            ):
                needs_update = True
                log.info(
                    "reconciliation update is required because of a version hash mismatch even though the version is the same - it's most likely a branch",
                    actual_template_version_hash=actual_incarnation_state.incarnation_state.template_repository_version_hash,
                    desired_template_version_hash=await local_template_git_repository.head(),
                )
            else:
                log.debug(
                    "the template is already in the desired version",
                    version=desired_incarnation_state.template_repository_version,
                    version_hash=await local_template_git_repository.head(),
                )

        # check if the existing incarnation requires an update because of a template data mismatch
        if data_diff := get_data_mismatch(
            desired_incarnation_state.template_data,
            actual_incarnation_state.incarnation_state.template_data,
            local_template_git_repository.directory,
            logger,
        ):
            needs_update = True
            log.info(
                "reconciliation update is required because of template data mismatch",
                actual_data=actual_incarnation_state.incarnation_state.template_data,
                desired_data=desired_incarnation_state.template_data,
                diff=data_diff,
            )
        else:
            log.debug(
                "the template data is the same",
                data=desired_incarnation_state.template_data,
            )

        if not needs_update:
            log.info("no reconciliation update is required, see debug logs for details")
            return ReconciliationState.UNCHANGED

        log.debug(
            f"fetching actual template repository version {actual_incarnation_state.incarnation_state.template_repository_version_hash} for update"
        )
        await local_template_git_repository.fetch(
            refspec=actual_incarnation_state.incarnation_state.template_repository_version_hash
        )

        # create new branch in incarnation repository to operate in
        await local_incarnation_git_repository.create_and_checkout_branch(
            update_branch_name
        )

        (
            updated_incarnation_state,
            files_with_conflicts,
        ) = await update_incarnation_from_git_template_repository(
            template_git_root_dir=local_template_git_repository.directory,
            update_template_repository=desired_incarnation_state.template_repository,
            update_template_repository_version=desired_incarnation_state.template_repository_version,
            update_template_data=desired_incarnation_state.template_data,
            incarnation_root_dir=local_incarnation_git_repository.directory
            / desired_incarnation_state.target_directory,
            diff_patch_func=diff_and_patch,
            logger=log,
        )
        log.info(
            "successfully updated incarnation with new template version",
            updated_incarnation_state=updated_incarnation_state,
        )

        mr_title = f"Update to {desired_incarnation_state.template_repository_version}"
        mr_description = (
            f"Update to {desired_incarnation_state.template_repository_version}"
        )
        reconciliation_state = ReconciliationState.CHANGED
        if files_with_conflicts:
            reconciliation_state = ReconciliationState.CHANGED_WITH_CONFLICT
            log.info(
                f"detected conflicts for files: {', '.join([str(f) for f in files_with_conflicts])} after update to new template"
            )
            mr_title = f"🚧 - CONFLICT: {mr_title}"
            mr_description = f"""{mr_description}

There are conflicts in this Merge Request. Please check the rejection files
of the following files from your repository:

{os.linesep.join([f"- {f}" for f in files_with_conflicts])}
"""

        automerge = desired_incarnation_state.automerge and reconciliation_state in {
            ReconciliationState.CHANGED
        }

        await local_incarnation_git_repository.commit_all(
            f"foxops: updating to template version {desired_incarnation_state.template_repository_version}"
        )
        await local_incarnation_git_repository.push_with_potential_retry()

        await ensure_merge_request_is_submitted(
            gitlab=gitlab,
            gitlab_project_id=actual_incarnation_state.gitlab_project_id,
            source_branch_name=update_branch_name,
            target_branch_name=actual_incarnation_state.default_branch,
            title=mr_title,
            description=mr_description,
            automerge=automerge,
            logger=log,
        )
        return reconciliation_state


async def initialize_incarnation_from_template(
    gitlab: AsyncGitlabClient,
    actual_incarnation_state: IncarnationRemoteGitRepositoryState,
    desired_incarnation_state: DesiredIncarnationStateConfig,
    local_template_repository: GitRepository,
    local_incarnation_repository: GitRepository,
    logger: BoundLogger,
) -> ReconciliationState:
    target_directory = (
        local_incarnation_repository.directory
        / desired_incarnation_state.target_directory
    )

    should_create_mr = (
        await local_incarnation_repository.has_any_commits()
        and target_directory.exists()
        and list(glob.glob("*", root_dir=target_directory)) != [FVARS_FILENAME]
    )

    branch_name = actual_incarnation_state.default_branch
    merge_request_required = False
    if should_create_mr:
        logger.debug(
            "incarnation repository is not empty, creating a branch for initialization"
        )
        merge_request_required = True

        # check if an incarnation initialization branch exists already
        branch_name = generate_foxops_branch_name(
            "initialize-to",
            desired_incarnation_state.target_directory,
            desired_incarnation_state.template_repository_version,
        )
        existing_initialization_branches = (
            await gitlab.project_repository_branches_list(
                actual_incarnation_state.gitlab_project_id, f"^{branch_name}"
            )
        )
        if len(existing_initialization_branches) > 0:
            logger.info(
                f"branch for an initialization to {desired_incarnation_state.template_repository_version} already exists. Skipping initialization"
            )
            return ReconciliationState.UNCHANGED

        # create new branch in incarnation repository where the template will be rendered
        await local_incarnation_repository.create_and_checkout_branch(branch_name)
        await local_incarnation_repository.push()
    else:
        logger.debug("incarnation repository is empty")
        await local_incarnation_repository.create_and_checkout_branch(
            branch_name,
            exist_ok=True,
        )

    incarnation_state = await initialize_incarnation(
        template_root_dir=local_template_repository.directory,
        template_repository=desired_incarnation_state.template_repository,
        template_repository_version=desired_incarnation_state.template_repository_version,
        template_data=desired_incarnation_state.template_data,
        incarnation_root_dir=local_incarnation_repository.directory
        / desired_incarnation_state.target_directory,
        logger=logger,
    )
    logger.debug(
        "existing files in directory",
        files=list(local_incarnation_repository.directory.rglob("*")),
    )
    result = await local_incarnation_repository._run("status")
    logger.debug(
        "git status",
        result=(await result.stdout.read())
        if result.stdout is not None
        else "no output",
    )

    result = await local_incarnation_repository.commit_all(
        f"foxops: initializing incarnation from template {desired_incarnation_state.template_repository} "
        f"@ {desired_incarnation_state.template_repository_version}"
    )
    logger.debug(
        "git commit",
        result=(await result.stdout.read())
        if result.stdout is not None
        else "no output",
    )
    result = await local_incarnation_repository._run("status")
    logger.debug(
        "git status",
        result=(await result.stdout.read())
        if result.stdout is not None
        else "no output",
    )

    await local_incarnation_repository.push_with_potential_retry()

    if merge_request_required:
        await ensure_merge_request_is_submitted(
            gitlab=gitlab,
            gitlab_project_id=actual_incarnation_state.gitlab_project_id,
            source_branch_name=branch_name,
            target_branch_name=actual_incarnation_state.default_branch,
            title=f"Initialize to {desired_incarnation_state.template_repository_version}",
            description=f"Initialize to {desired_incarnation_state.template_repository_version}",
            automerge=desired_incarnation_state.automerge,
            logger=logger,
        )

    logger.info(
        "successfully initialized incarnation from template",
        incarnation_state=incarnation_state,
    )
    return ReconciliationState.CHANGED


async def ensure_merge_request_is_submitted(
    gitlab: AsyncGitlabClient,
    gitlab_project_id: int,
    source_branch_name: str,
    target_branch_name: str,
    title: str,
    description: str,
    automerge: bool,
    logger: BoundLogger,
) -> bool:
    """Ensure that a Merge Request has been submitted.

    If no Merge Request exists, submit a new one.
    """
    existing_merge_requests = await gitlab.project_merge_requests_list(
        gitlab_project_id, "opened", source_branch_name
    )
    if len(existing_merge_requests) > 0:
        logger.info(
            f"a Merge Request for the update branch {source_branch_name} already exists."
        )
        return False

    merge_request = await gitlab.project_merge_requests_create(
        gitlab_project_id,
        source_branch_name,
        target_branch_name,
        title,
        description,
    )
    logger.info(f"created a new Merge Request at {merge_request['web_url']}")

    if automerge:
        logger.info(
            f"Triggering automerge for the new Merge Request {merge_request['web_url']}"
        )
        await gitlab.automerge_merge_request(gitlab_project_id, merge_request["iid"])
    return True


def generate_foxops_branch_name(
    prefix: str, target_directory: Path, template_version: str
) -> str:
    target_directory_hash = hashlib.sha1(
        str(target_directory).encode("utf-8")
    ).hexdigest()[:7]
    return f"foxops/{prefix}-{target_directory_hash}-{template_version}"

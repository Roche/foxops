import hashlib
import os
from glob import glob
from pathlib import Path

import foxops.engine as fengine
from foxops.errors import IncarnationRepositoryNotFound, ReconciliationError
from foxops.external.git import GitRepository
from foxops.hosters import GitSha, Hoster
from foxops.logging import get_logger
from foxops.models import (
    DesiredIncarnationState,
    DesiredIncarnationStatePatch,
    Incarnation,
    incarnation_identifier,
)

#: Holds the module logger
logger = get_logger(__name__)


async def initialize_incarnation(
    hoster: Hoster, desired_incarnation_state: DesiredIncarnationState
) -> GitSha:
    logger.info("Verifying if the incarnation can be initialized")

    try:
        actual_incarnation_state = await hoster.get_incarnation_state(
            desired_incarnation_state.incarnation_repository,
            desired_incarnation_state.target_directory,
        )
    except IncarnationRepositoryNotFound as exc:
        logger.warning(f"Reconciliation failed, because: {exc}")
        raise ReconciliationError(
            f"Failed to reconcile incarnation because the remote Incarnation repository at '{exc.incarnation_repository}' doesn't exist. "
            "Create it first, then try again."
        )

    if actual_incarnation_state is not None:
        raise ReconciliationError(
            f"Incarnation {incarnation_identifier(desired_incarnation_state)} already initialized"
        )

    logger.debug("Cloning Incarnation and Template repository to local directory")

    incarnation_repo_cm = hoster.cloned_repository(
        desired_incarnation_state.incarnation_repository
    )
    template_repo_cm = hoster.cloned_repository(
        desired_incarnation_state.template_repository,
        refspec=desired_incarnation_state.template_repository_version,
    )

    # FIXME: why are these types not correctly deduced?!
    local_incarnation_repository: GitRepository
    local_template_repository: GitRepository
    async with incarnation_repo_cm as local_incarnation_repository, template_repo_cm as local_template_repository:
        logger.debug(
            f"Cloned Incarnation repository to '{local_incarnation_repository.directory}' and Template repository to '{local_template_repository.directory}'"
        )

        with_merge_request = await _should_initialize_with_merge_request(
            local_incarnation_repository, desired_incarnation_state.target_directory
        )

        # preparing the branch to initialize the incarnation
        init_branch = None
        if with_merge_request:
            init_branch = generate_foxops_branch_name(
                "initialize-to",
                desired_incarnation_state.target_directory,
                desired_incarnation_state.template_repository_version,
            )

            if git_sha := await hoster.has_pending_incarnation_branch(
                desired_incarnation_state.incarnation_repository, init_branch
            ):
                logger.info(
                    f"Branch '{init_branch}' already exists, skipping initialization"
                )
                return git_sha
        else:
            init_branch = (
                await hoster.get_repository_metadata(
                    desired_incarnation_state.incarnation_repository
                )
            )["default_branch"]

        await local_incarnation_repository.create_and_checkout_branch(
            init_branch,
            exist_ok=True,
        )

        _ = await fengine.initialize_incarnation(
            template_root_dir=local_template_repository.directory,
            template_repository=desired_incarnation_state.template_repository,
            template_repository_version=desired_incarnation_state.template_repository_version,
            template_data=desired_incarnation_state.template_data,
            incarnation_root_dir=(
                local_incarnation_repository.directory
                / desired_incarnation_state.target_directory
            ),
        )

        await local_incarnation_repository.commit_all(
            f"foxops: initializing incarnation from template {desired_incarnation_state.template_repository} "
            f"@ {desired_incarnation_state.template_repository_version}"
        )
        commit_sha = await local_incarnation_repository.push_with_potential_retry()
        logger.debug(
            "Local reconciliation finished and synced with remote",
            commit_sha=commit_sha,
        )

        if with_merge_request:
            merge_request_sha = await hoster.merge_request(
                incarnation_repository=desired_incarnation_state.incarnation_repository,
                source_branch=init_branch,
                title=f"Initialize to {desired_incarnation_state.template_repository_version}",
                description=f"Initialize to {desired_incarnation_state.template_repository_version}",
                with_automerge=desired_incarnation_state.automerge,
            )
            return merge_request_sha
        else:
            return commit_sha


async def _should_initialize_with_merge_request(
    local_repository: GitRepository, target_directory: str
) -> bool:
    """Checks if the given local incarnation repository should be initialize with a Merge Request or directly pushed to the default branch."""
    incarnation_dir = local_repository.directory / target_directory
    repo_has_commits = await local_repository.has_any_commits()
    incarnated_files = set(
        glob("*", root_dir=incarnation_dir) + glob(".*", root_dir=incarnation_dir)
    ) - {".git", fengine.FVARS_FILENAME}

    return repo_has_commits and incarnation_dir.exists() and len(incarnated_files) > 0


async def update_incarnation(
    hoster: Hoster,
    incarnation: Incarnation,
    desired_incarnation_state_patch: DesiredIncarnationStatePatch,
) -> GitSha | None:
    logger.info("Updating incarnation")

    logger.debug("Fetching current incarnation state")
    incarnation_state_before_update = await hoster.get_incarnation_state(
        incarnation.incarnation_repository, incarnation.target_directory
    )

    if incarnation_state_before_update is None:
        raise ReconciliationError(
            f"Failed to update incarnation {incarnation_identifier(incarnation)} because it is not initialized"
        )

    template_repository_version_update = (
        desired_incarnation_state_patch.template_repository_version
        if desired_incarnation_state_patch.template_repository_version is not None
        else incarnation_state_before_update.template_repository_version
    )
    template_data_update = {
        **incarnation_state_before_update.template_data,
        **desired_incarnation_state_patch.template_data,
    }
    logger.info(
        "Updating incarnation with",
        template_repository_version_update=template_repository_version_update,
        template_data_update=template_data_update,
    )

    update_branch = generate_foxops_branch_name(
        "update-to",
        incarnation.target_directory,
        template_repository_version_update,
    )
    if git_sha := await hoster.has_pending_incarnation_branch(
        incarnation.incarnation_repository, update_branch
    ):
        logger.info(f"Branch '{update_branch}' already exists, skipping update")
        return git_sha

    logger.debug("Cloning Incarnation and Template repository to local directory")

    incarnation_repo_cm = hoster.cloned_repository(incarnation.incarnation_repository)
    template_repo_cm = hoster.cloned_repository(
        incarnation_state_before_update.template_repository,
        refspec=incarnation_state_before_update.template_repository_version_hash,
    )

    # FIXME: why are these types not correctly deduced?!
    local_incarnation_repository: GitRepository
    local_template_repository: GitRepository
    async with incarnation_repo_cm as local_incarnation_repository, template_repo_cm as local_template_repository:
        logger.debug(
            f"Cloned Incarnation repository to '{local_incarnation_repository.directory}' and Template repository to '{local_template_repository.directory}'"
        )

        logger.debug(
            f"Creating new update branch {update_branch} in incarnation repository"
        )
        await local_incarnation_repository.create_and_checkout_branch(update_branch)

        (
            update_performed,
            updated_incarnation_state,
            files_with_conflicts,
        ) = await fengine.update_incarnation_from_git_template_repository(
            template_git_root_dir=local_template_repository.directory,
            update_template_repository=incarnation_state_before_update.template_repository,
            update_template_repository_version=template_repository_version_update,
            update_template_data=template_data_update,
            incarnation_root_dir=(
                local_incarnation_repository.directory / incarnation.target_directory
            ),
            diff_patch_func=fengine.diff_and_patch,
        )

        if not update_performed:
            # FIXME: what is the proper thing to do here?
            #        Should we return a git sha?
            return None

        logger.info(
            "updated incarnation with new template version",
            updated_incarnation_state=updated_incarnation_state,
        )
        await local_incarnation_repository.commit_all(
            f"foxops: updating incarnation from template {template_repository_version_update} "
        )
        commit_sha = await local_incarnation_repository.push_with_potential_retry()
        logger.debug(
            "Local reconciliation finished and synced with remote",
            commit_sha=commit_sha,
        )

        if not files_with_conflicts:
            revision = await _handle_update_merge_request_without_conflicts(
                hoster,
                incarnation,
                update_branch,
                template_repository_version_update,
                desired_incarnation_state_patch.automerge,
            )
        else:
            revision = await _handle_update_merge_request_with_conflicts(
                hoster,
                incarnation,
                update_branch,
                template_repository_version_update,
                files_with_conflicts,
            )

        return revision


async def _handle_update_merge_request_without_conflicts(
    hoster: Hoster,
    incarnation: Incarnation,
    update_branch: str,
    template_repository_version: str,
    automerge: bool,
) -> GitSha:
    merge_request_sha = await hoster.merge_request(
        incarnation_repository=incarnation.incarnation_repository,
        source_branch=update_branch,
        title=f"Initialize to {template_repository_version}",
        description=f"Initialize to {template_repository_version}",
        with_automerge=automerge,
    )
    return merge_request_sha


async def _handle_update_merge_request_with_conflicts(
    hoster: Hoster,
    incarnation: Incarnation,
    update_branch: str,
    template_repository_version: str,
    files_with_conflicts: list[Path],
) -> GitSha:
    logger.info(
        f"detected conflicts for files: {', '.join([str(f) for f in files_with_conflicts])} after update to new template"
    )
    title = f"🚧 - CONFLICT: Initialize to {template_repository_version}"
    description = f"""Initialize to {template_repository_version}

There are conflicts in this Merge Request. Please check the rejection files
of the following files from your repository:

{os.linesep.join([f"- {f}" for f in files_with_conflicts])}
    """
    merge_request_sha = await hoster.merge_request(
        incarnation_repository=incarnation.incarnation_repository,
        source_branch=update_branch,
        title=title,
        description=description,
        with_automerge=False,
    )
    return merge_request_sha


def generate_foxops_branch_name(
    prefix: str, target_directory: str, template_repository_version: str
) -> str:
    target_directory_hash = hashlib.sha1(target_directory.encode("utf-8")).hexdigest()[
        :7
    ]
    return f"foxops/{prefix}-{target_directory_hash}-{template_repository_version}"

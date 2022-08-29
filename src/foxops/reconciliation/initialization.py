from glob import glob

import foxops.engine as fengine
from foxops.errors import (
    IncarnationAlreadyInitializedError,
    IncarnationRepositoryNotFound,
    ReconciliationUserError,
)
from foxops.external.git import GitRepository
from foxops.hosters import GitSha, Hoster, MergeRequestId
from foxops.logger import get_logger
from foxops.models import DesiredIncarnationState
from foxops.reconciliation.utils import generate_foxops_branch_name, retry_if_possible

#: Holds the module logger
logger = get_logger(__name__)


@retry_if_possible
async def initialize_incarnation(
    hoster: Hoster, desired_incarnation_state: DesiredIncarnationState
) -> tuple[GitSha, MergeRequestId | None]:
    logger.info("Verifying if the incarnation can be initialized")

    try:
        incarnation_state = await hoster.get_incarnation_state(
            desired_incarnation_state.incarnation_repository,
            desired_incarnation_state.target_directory,
        )
    except IncarnationRepositoryNotFound as exc:
        logger.warning(f"Reconciliation failed, because: {exc}")
        raise ReconciliationUserError(
            f"Failed to reconcile incarnation because the remote Incarnation repository "
            f"at '{exc.incarnation_repository}' doesn't exist. Create it first, then try again."
        )

    if incarnation_state is not None:
        last_commit_sha, actual_incarnation_state = incarnation_state
        logger.debug("Incarnation is already initialized, checking if conflicts in data ...")

        raise IncarnationAlreadyInitializedError(
            desired_incarnation_state.incarnation_repository,
            desired_incarnation_state.target_directory,
            commit_sha=last_commit_sha,
            has_mismatch=desired_incarnation_state != actual_incarnation_state,
        )

    logger.debug("Cloning Incarnation and Template repository to local directory")

    incarnation_repo_cm = hoster.cloned_repository(desired_incarnation_state.incarnation_repository)
    template_repo_cm = hoster.cloned_repository(
        desired_incarnation_state.template_repository,
        refspec=desired_incarnation_state.template_repository_version,
    )

    # FIXME: why are these types not correctly deduced?!
    local_incarnation_repository: GitRepository
    local_template_repository: GitRepository
    async with incarnation_repo_cm as local_incarnation_repository, template_repo_cm as local_template_repository:
        logger.debug(
            f"Cloned Incarnation repository to '{local_incarnation_repository.directory}' "
            f"and Template repository to '{local_template_repository.directory}'"
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
                logger.info(f"Branch '{init_branch}' already exists, skipping initialization")

                if merge_request_id := await hoster.has_pending_incarnation_merge_request(
                    desired_incarnation_state.incarnation_repository, init_branch
                ):
                    logger.info(f"Branch '{init_branch}' is already merge requested, skipping initialization")
                    return git_sha, merge_request_id
                else:
                    merge_request_sha, merge_request_id = await hoster.merge_request(
                        incarnation_repository=desired_incarnation_state.incarnation_repository,
                        source_branch=init_branch,
                        title=f"Initialize to {desired_incarnation_state.template_repository_version}",
                        description=f"Initialize to {desired_incarnation_state.template_repository_version}",
                        with_automerge=desired_incarnation_state.automerge,
                    )
                    return git_sha, merge_request_id
        else:
            init_branch = (await hoster.get_repository_metadata(desired_incarnation_state.incarnation_repository))[
                "default_branch"
            ]

        await local_incarnation_repository.create_and_checkout_branch(
            init_branch,
            exist_ok=True,
        )

        _ = await fengine.initialize_incarnation(
            template_root_dir=local_template_repository.directory,
            template_repository=desired_incarnation_state.template_repository,
            template_repository_version=desired_incarnation_state.template_repository_version,
            template_data=desired_incarnation_state.template_data,
            incarnation_root_dir=(local_incarnation_repository.directory / desired_incarnation_state.target_directory),
        )

        await local_incarnation_repository.commit_all(
            f"foxops: initializing incarnation from template {desired_incarnation_state.template_repository} "
            f"@ {desired_incarnation_state.template_repository_version}"
        )
        commit_sha = await local_incarnation_repository.push()
        logger.debug(
            "Local reconciliation finished and synced with remote",
            commit_sha=commit_sha,
        )

        if with_merge_request:
            merge_request_sha, merge_request_id = await hoster.merge_request(
                incarnation_repository=desired_incarnation_state.incarnation_repository,
                source_branch=init_branch,
                title=f"Initialize to {desired_incarnation_state.template_repository_version}",
                description=f"Initialize to {desired_incarnation_state.template_repository_version}",
                with_automerge=desired_incarnation_state.automerge,
            )
            return merge_request_sha, merge_request_id
        else:
            return commit_sha, None


async def _should_initialize_with_merge_request(local_repository: GitRepository, target_directory: str) -> bool:
    """Checks if the given local incarnation repository should be initialized
    with a Merge Request or directly pushed to the default branch."""
    incarnation_dir = local_repository.directory / target_directory
    repo_has_commits = await local_repository.has_any_commits()
    incarnated_files = set(glob("*", root_dir=incarnation_dir) + glob(".*", root_dir=incarnation_dir)) - {
        ".git",
        fengine.FVARS_FILENAME,
    }

    return repo_has_commits and incarnation_dir.exists() and len(incarnated_files) > 0

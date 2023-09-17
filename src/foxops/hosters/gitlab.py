import asyncio
import base64
import shutil
from contextlib import asynccontextmanager
from datetime import timedelta
from http import HTTPStatus
from pathlib import Path
from ssl import SSLZeroReturnError
from tempfile import mkdtemp
from typing import AsyncIterator, TypedDict
from urllib.parse import quote_plus

import httpx
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_fixed

from foxops.engine import IncarnationState
from foxops.engine.models import load_incarnation_state_from_string
from foxops.errors import IncarnationRepositoryNotFound
from foxops.external.git import (
    GitRepository,
    add_authentication_to_git_clone_url,
    git_exec,
)
from foxops.hosters.types import (
    GitSha,
    Hoster,
    MergeRequestId,
    MergeRequestStatus,
    ReconciliationStatus,
    RepositoryMetadata,
)
from foxops.logger import bound, get_logger

#: Holds the module logger
logger = get_logger(__name__)


class MergeRequest(TypedDict):
    iid: int
    project_id: int
    web_url: str
    sha: str
    state: str
    merge_status: str
    merge_commit_sha: str | None
    head_pipeline: dict | None


class LastCommitPipeline(TypedDict):
    id: int
    status: str


class Commit(TypedDict):
    last_pipeline: dict | None
    status: str


def evaluate_gitlab_address(address: str) -> tuple[str, str]:
    """Evaluate the given GitLab address and return a tuple containing the GitLab Web UI URL and the GitLab API URL."""
    if address.endswith("/api/v4"):
        return address.removesuffix("/api/v4"), address
    else:
        return address, f"{address}/api/v4"


class GitlabHoster(Hoster):
    """REST API client for GitLab"""

    def __init__(self, address: str, token: str):
        self.web_address, self.api_address = evaluate_gitlab_address(address)
        self.token = token
        self.client = httpx.AsyncClient(
            base_url=self.api_address, headers={"Authorization": f"Bearer {self.token}"}, timeout=httpx.Timeout(120)
        )

    async def validate(self) -> None:
        (await self.client.get("/version")).raise_for_status()

    async def __project_exists(self, project_identifier: str) -> bool:
        response = await self.client.head(f"/projects/{quote_plus(project_identifier)}")
        return response.status_code == HTTPStatus.OK

    async def get_incarnation_state(
        self, incarnation_repository: str, target_directory: str
    ) -> tuple[GitSha, IncarnationState] | None:
        if not await self.__project_exists(incarnation_repository):
            raise IncarnationRepositoryNotFound(incarnation_repository)

        fengine_config_file = Path(target_directory, ".fengine.yaml")
        response = await self.client.get(
            f"/projects/{quote_plus(incarnation_repository)}/repository/files/{quote_plus(str(fengine_config_file))}",
            params={"ref": "main"},
        )
        if response.status_code == HTTPStatus.NOT_FOUND:
            logger.debug(
                f"Incarnation repository at '{incarnation_repository}' and target directory '{target_directory}' not found."
            )
            return None

        # raising for all other non-success statuses
        response.raise_for_status()
        file_data = response.json()

        return file_data["last_commit_id"], load_incarnation_state_from_string(
            base64.b64decode(file_data["content"]).decode("utf-8")
        )

    async def merge_request(
        self,
        *,
        incarnation_repository: str,
        source_branch: str,
        title: str,
        description: str,
        with_automerge=False,
    ) -> tuple[GitSha, MergeRequestId]:
        response = await self.client.get(
            f"/projects/{quote_plus(incarnation_repository)}/merge_requests",
            params={"state": "opened", "source_branch": source_branch},
        )
        response.raise_for_status()
        existing_merge_requests: list[MergeRequest] = response.json()
        if len(existing_merge_requests) > 0:
            logger.debug(f"Merge request for '{source_branch}' already exists in '{incarnation_repository}'")
            return existing_merge_requests[0]["sha"], str(existing_merge_requests[0]["iid"])

        # Get project details to retrieve the default branch name
        # In the future we might want to leave it up to the caller to
        # figure out which branch to merge to.
        # For now, foxops anyways only supports operating on the default branch.
        target_branch = (await self.get_repository_metadata(incarnation_repository))["default_branch"]

        response = await self.client.post(
            f"/projects/{quote_plus(incarnation_repository)}/merge_requests",
            json={
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": description,
                "remove_source_branch": "True",
            },
        )
        response.raise_for_status()
        merge_request: MergeRequest = response.json()
        logger.info(
            f"Created merge request at {merge_request['web_url']}",
            title=title,
            source_branch=source_branch,
            with_automerge=with_automerge,
        )

        if with_automerge:
            logger.info(f"Triggering automerge for the new Merge Request {merge_request['web_url']}")
            merge_request = await self._automerge_merge_request(merge_request)

        return merge_request["sha"], str(merge_request["iid"])

    @asynccontextmanager
    async def cloned_repository(
        self, repository: str, *, refspec: str | None = None, bare: bool = False
    ) -> AsyncIterator[GitRepository]:
        if not repository.startswith(("https://", "http://")):
            # it's not a URL, but a `path_with_namespace`, so, let's think it a URL
            metadata = await self.get_repository_metadata(repository)
            repository = metadata["http_url"]

        clone_url = add_authentication_to_git_clone_url(repository, "oauth2", self.token)

        # we assume that `repository` is already a proper HTTP(S) URL
        local_clone_directory = Path(mkdtemp())

        try:
            if refspec is None:
                if not bare:
                    await git_exec(
                        "clone",
                        "--depth=1",
                        clone_url,
                        local_clone_directory,
                        cwd=Path.home(),
                    )
                else:
                    await git_exec(
                        "clone",
                        "--bare",
                        clone_url,
                        local_clone_directory,
                        cwd=Path.home(),
                    )
            else:
                # NOTE(TF): this only works for git hosters which have enabled `uploadpack.allowReachableSHA1InWant`
                #           on the server side. It seems to be the case for GitHub and GitLab.
                #           In addition, it seems that if the refspec is a tag, it won't be created locally
                #           and we later on cannot address it in e.g. a `switch`.
                #           So we need to fetch all tag refs, which should be fine.
                await git_exec("init", local_clone_directory, cwd=Path.home())
                await git_exec("remote", "add", "origin", clone_url, cwd=local_clone_directory)
                await git_exec(
                    "fetch",
                    "--depth=1",
                    "origin",
                    "--tags",
                    refspec,
                    cwd=local_clone_directory,
                )
                await git_exec("reset", "--hard", "FETCH_HEAD", cwd=local_clone_directory)

            # NOTE(TF): set author data
            await git_exec(
                "config",
                "user.name",
                "foxops",
                cwd=local_clone_directory,
            )
            await git_exec("config", "user.email", "noreply@foxops.io", cwd=local_clone_directory)

            yield GitRepository(local_clone_directory)
        finally:
            shutil.rmtree(local_clone_directory)

    async def has_pending_incarnation_branch(self, project_identifier: str, branch: str) -> GitSha | None:
        response = await self.client.get(
            f"/projects/{quote_plus(project_identifier)}/repository/branches/{quote_plus(branch)}"
        )
        if response.status_code == HTTPStatus.OK:
            return response.json()["commit"]["id"]
        return None

    async def has_pending_incarnation_merge_request(
        self, project_identifier: str, branch: str
    ) -> MergeRequestId | None:
        response = await self.client.get(
            f"/projects/{quote_plus(project_identifier)}/merge_requests",
            params={"source_branch": branch, "state": "opened"},
        )
        response.raise_for_status()
        merge_requests: list[MergeRequest] = response.json()
        if len(merge_requests) > 0:
            return str(merge_requests[0]["iid"])

        return None

    async def get_repository_metadata(self, project_identifier: str) -> RepositoryMetadata:
        response = await self.client.get(f"/projects/{quote_plus(project_identifier)}")
        response.raise_for_status()
        data = response.json()
        return {
            "default_branch": data["default_branch"],
            "http_url": data["http_url_to_repo"],
        }

    async def _automerge_merge_request(
        self, merge_request: MergeRequest, timeout: timedelta | None = None
    ) -> MergeRequest:
        """Automerge the given Merge Request.

        It will immediately merge if possible, otherwise when the pipeline succeeds.
        There won't be made any rebases or similar nor wait for the actual merge to happen.
        """
        if timeout is None:
            timeout = timedelta(minutes=5)

        @retry(
            retry=retry_if_exception_type(httpx.HTTPStatusError),
            stop=stop_after_delay(timeout.total_seconds()),
            wait=wait_fixed(1),
        )
        async def __merge(mr: MergeRequest) -> MergeRequest:
            response = await self.client.get(f"/projects/{mr['project_id']}/merge_requests/{mr['iid']}")
            response.raise_for_status()
            merge_request: MergeRequest = response.json()
            has_pipeline = bool(merge_request["head_pipeline"])
            data = {"merge_when_pipeline_succeeds": True} if has_pipeline else None
            response = await self.client.put(
                f"/projects/{merge_request['project_id']}/merge_requests/{merge_request['iid']}/merge",
                json=data,
            )
            response.raise_for_status()
            return response.json()

        return await __merge(merge_request)

    async def get_reconciliation_status(
        self,
        incarnation_repository: str,
        target_directory: str,
        commit_sha: GitSha,
        merge_request_id: str | None,
        pipeline_timeout: timedelta | None = None,
    ) -> ReconciliationStatus:
        if pipeline_timeout is None:
            pipeline_timeout = timedelta()

        async def _get_commit_status(commit_sha: GitSha, pipeline_timeout: timedelta) -> ReconciliationStatus:
            try:
                response = await self.client.get(
                    f"/projects/{quote_plus(incarnation_repository)}/repository/commits/{commit_sha}"
                )
            except SSLZeroReturnError as e:
                logger.warning(
                    "failed to get commit status due to an SSL error when connecting to Gitlab. Returning UNKNOWN.",
                    commit_sha=commit_sha,
                    repository=incarnation_repository,
                    error=str(e),
                )
                return ReconciliationStatus.UNKNOWN
            if response.status_code == 404:
                logger.warning("commit or project not found", commit_sha=commit_sha, repository=incarnation_repository)
                return ReconciliationStatus.UNKNOWN

            response.raise_for_status()
            commit: Commit = response.json()

            with bound(commit=commit):
                if commit["status"] is None and commit["last_pipeline"] is None:
                    has_pipeline_config = await self._has_gitlab_ci_configuration(incarnation_repository, commit_sha)
                    if has_pipeline_config:
                        if pipeline_timeout.total_seconds() > 0:
                            logger.debug(
                                f"Reconciliation status: no commit status and no pipeline, and pipeline_timeout "
                                f"is {pipeline_timeout.total_seconds()} seconds, sleeping 1 second and retry"
                            )
                            await asyncio.sleep(1)
                            return await _get_commit_status(commit_sha, pipeline_timeout - timedelta(seconds=1))

                    logger.debug(
                        "Reconciliation status: no commit status and no pipeline, assuming SUCCESS",
                        has_pipeline_config=has_pipeline_config,
                    )
                    return ReconciliationStatus.SUCCESS

                if commit["status"] == "success":
                    logger.debug("Reconciliation status: commit status is success, returning SUCCESS")
                    return ReconciliationStatus.SUCCESS

                if commit["status"] in {"created", "pending", "waiting_for_resource", "running"}:
                    logger.debug(f"Reconciliation status: commit status is {commit['status']}, returning PENDING")
                    return ReconciliationStatus.PENDING

                if commit["status"] in {"failed", "canceled"}:
                    logger.debug(f"Reconciliation status: commit status is {commit['status']}, returning FAILED")
                    return ReconciliationStatus.FAILED

                logger.error(
                    f"Incarnation '{incarnation_repository}' / '{target_directory}' has an unknown commit status "
                    f"'{commit['status']}' for commit '{commit_sha}'"
                )

            return ReconciliationStatus.UNKNOWN

        if merge_request_id is None:
            logger.debug(f"No merge request id given, therefore checking commit status of '{commit_sha}'")
            return await _get_commit_status(commit_sha, pipeline_timeout=pipeline_timeout)

        logger.debug("Checking merge request status")
        response = await self.client.get(
            f"/projects/{quote_plus(incarnation_repository)}/merge_requests/{merge_request_id}"
        )
        response.raise_for_status()
        merge_request: MergeRequest = response.json()

        with bound(merge_request=merge_request):
            if merge_request["state"] == "opened":
                if merge_request["merge_status"] in {"cannot_be_merged", "cannot_be_merged_recheck"}:
                    logger.debug(
                        f"Reconciliation status: merge request state is open "
                        f"and status is {merge_request['merge_status']}, returning FAILED"
                    )
                    return ReconciliationStatus.FAILED

                if merge_request["head_pipeline"] is not None and merge_request["head_pipeline"]["status"] in {
                    "failed",
                    "canceled",
                }:
                    logger.debug(
                        f"Reconciliation status: merge request state is open and pipeline status is "
                        f"{merge_request['head_pipeline']['status']}, returning FAILED"
                    )
                    return ReconciliationStatus.FAILED

                logger.debug("Reconciliation status: merge request state is open, returning PENDING")
                return ReconciliationStatus.PENDING
            elif merge_request["state"] == "merged":
                if merge_request["merge_commit_sha"] is not None:
                    logger.debug(
                        f"Reconciliation status: merge request is merged at {merge_request['merge_commit_sha']}, "
                        f"checking its commit status ..."
                    )
                    merge_commit_sha = merge_request["merge_commit_sha"]
                    return await _get_commit_status(merge_commit_sha, pipeline_timeout=pipeline_timeout)
                elif merge_request["sha"] is not None:
                    logger.debug(
                        f"Reconciliation status: merge request is merged without merge commit at {merge_request['sha']}, "
                        f"checking its commit status ..."
                    )
                    sha = merge_request["sha"]
                    return await _get_commit_status(sha, pipeline_timeout=pipeline_timeout)
            elif merge_request["state"] == "closed":
                logger.debug("Reconciliation status: merge request is closed, returning FAILED")
                return ReconciliationStatus.FAILED

            logger.error(
                f"Incarnation '{incarnation_repository}' / '{target_directory}' has an unknown merge request status "
                f"'{merge_request['state']}' for merge request '{merge_request_id}'"
            )
            return ReconciliationStatus.UNKNOWN

    async def does_commit_exist(self, incarnation_repository: str, commit_sha: GitSha) -> bool:
        response = await self.client.get(
            f"/projects/{quote_plus(incarnation_repository)}/repository/commits/{commit_sha}"
        )
        if response.status_code == 404:
            return False

        response.raise_for_status()
        return True

    async def get_commit_url(self, incarnation_repository: str, commit_sha: GitSha) -> str:
        return f"{self.web_address}/{incarnation_repository}/-/commit/{commit_sha}"

    async def get_merge_request_url(self, incarnation_repository: str, merge_request_id: str) -> str:
        return f"{self.web_address}/{incarnation_repository}/-/merge_requests/{merge_request_id}"

    async def get_merge_request_status(self, incarnation_repository: str, merge_request_id: str) -> MergeRequestStatus:
        response = await self.client.get(
            f"/projects/{quote_plus(incarnation_repository)}/merge_requests/{merge_request_id}"
        )
        if response.status_code == 404:
            if not await self.__project_exists(incarnation_repository):
                raise IncarnationRepositoryNotFound(incarnation_repository)

            # if the merge request does not exist, we assume it has been closed (because it was deleted)
            return MergeRequestStatus.CLOSED
        response.raise_for_status()

        merge_request: MergeRequest = response.json()

        mapping = {
            "opened": MergeRequestStatus.OPEN,
            "locked": MergeRequestStatus.OPEN,  # assumed to be a transitional, internal Gitlab state
            "closed": MergeRequestStatus.CLOSED,
            "merged": MergeRequestStatus.MERGED,
        }
        state = merge_request["state"]
        try:
            return mapping[state]
        except KeyError:
            logger.warning(
                f"unknown merge request state '{state}'",
                incarnation_repository=incarnation_repository,
                merge_request_id=merge_request_id,
            )
            return MergeRequestStatus.UNKNOWN

    async def _has_gitlab_ci_configuration(self, incarnation_repository: str, ref: str) -> bool:
        response = await self.client.head(
            f"/projects/{quote_plus(incarnation_repository)}/repository/files/{quote_plus('.gitlab-ci.yml')}",
            params={"ref": ref},
        )
        return response.status_code == HTTPStatus.OK

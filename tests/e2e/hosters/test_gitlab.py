import base64
import uuid
from collections import namedtuple
from datetime import timedelta

import pytest
from httpx import AsyncClient, HTTPStatusError
from pydantic import SecretStr
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_fixed

from foxops.hosters import Hoster, ReconciliationStatus
from foxops.hosters.gitlab import GitLab
from foxops.hosters.gitlab.settings import GitLabSettings

# mark all tests in this module as e2e
pytestmark = pytest.mark.e2e


#: Holds a namedtuple for the test repository information
RepositoryTestData = namedtuple(
    "RepositoryTestData",
    ["project", "commit_sha_main", "commit_sha_branch_without_pipeline", "commit_sha_branch_with_pipeline"],
)


@pytest.fixture(name="test_repository")
async def create_test_repository(gitlab_test_client: AsyncClient) -> RepositoryTestData:
    response = await gitlab_test_client.post(
        "/projects",
        json={
            "name": f"gitlab-hoster-test-{uuid.uuid4()}",
            "initialize_with_readme": True,
        },
    )
    response.raise_for_status()
    project = response.json()

    # Create new commit with new file in new branch without a pipeline
    response = await gitlab_test_client.post(
        f"/projects/{project['id']}/repository/files/test.txt",
        json={
            "branch": "without-pipeline",
            "start_branch": project["default_branch"],
            "content": "Hello World",
            "commit_message": "Some new file",
        },
    )
    response.raise_for_status()
    commit_sha_branch_without_pipeline = "without-pipeline"

    # Create new commit with pipeline in new branch
    response = await gitlab_test_client.post(
        f"/projects/{project['id']}/repository/files/.gitlab-ci.yml",
        json={
            "branch": "with-pipeline",
            "start_branch": project["default_branch"],
            "encoding": "base64",
            "content": base64.b64encode(
                b"""
build:
    image: alpine:latest
    script:
        - echo Hello World

            """
            ).decode("utf-8"),
            "commit_message": "Some new file",
        },
    )
    response.raise_for_status()
    commit_sha_branch_with_pipeline = "with-pipeline"

    return RepositoryTestData(project, "main", commit_sha_branch_without_pipeline, commit_sha_branch_with_pipeline)


@pytest.fixture(name="test_gitlab_hoster")
async def create_test_gitlab_hoster(gitlab_test_address: str, gitlab_test_user_token: str) -> Hoster:
    settings: GitLabSettings = GitLabSettings(
        address=gitlab_test_address, client_id="FIXME", client_secret=SecretStr("FIXME")
    )
    return GitLab(settings, SecretStr(gitlab_test_user_token))


async def should_return_success_reconciliation_status_for_default_branch_commit_without_pipeline(
    test_gitlab_hoster: Hoster, test_repository: RepositoryTestData
):
    # WHEN
    status = await test_gitlab_hoster.get_reconciliation_status(
        incarnation_repository=test_repository.project["path_with_namespace"],
        target_directory=".",
        commit_sha=test_repository.commit_sha_main,
        merge_request_id=None,
    )

    # THEN
    assert status == ReconciliationStatus.SUCCESS


async def should_return_pending_reconciliation_status_for_default_branch_commit_with_pending_pipeline(
    test_gitlab_hoster: Hoster, test_repository: RepositoryTestData
):
    # WHEN
    status = await test_gitlab_hoster.get_reconciliation_status(
        incarnation_repository=test_repository.project["path_with_namespace"],
        target_directory=".",
        commit_sha=test_repository.commit_sha_branch_with_pipeline,
        merge_request_id=None,
        pipeline_timeout=timedelta(seconds=10),
    )

    # THEN
    assert status == ReconciliationStatus.PENDING


async def should_return_pending_reconciliation_status_for_open_merge_request(
    test_gitlab_hoster: Hoster, gitlab_test_client: AsyncClient, test_repository: RepositoryTestData
):
    # GIVEN
    response = await gitlab_test_client.post(
        f"/projects/{test_repository.project['id']}/merge_requests",
        json={
            "source_branch": "without-pipeline",
            "target_branch": test_repository.project["default_branch"],
            "title": "Some merge request",
        },
    )
    response.raise_for_status()
    merge_request = response.json()

    # WHEN
    status = await test_gitlab_hoster.get_reconciliation_status(
        incarnation_repository=test_repository.project["path_with_namespace"],
        target_directory=".",
        commit_sha=test_repository.commit_sha_branch_without_pipeline,
        merge_request_id=merge_request["iid"],
    )

    # THEN
    assert status == ReconciliationStatus.PENDING


async def should_return_success_reconciliation_status_for_merged_merge_request_without_pipeline_in_target_branch(
    test_gitlab_hoster: Hoster, gitlab_test_client: AsyncClient, test_repository: RepositoryTestData
):
    # GIVEN
    response = await gitlab_test_client.post(
        f"/projects/{test_repository.project['id']}/merge_requests",
        json={
            "source_branch": "without-pipeline",
            "target_branch": test_repository.project["default_branch"],
            "title": "Some merge request",
        },
    )
    response.raise_for_status()
    merge_request = response.json()

    @retry(
        retry=retry_if_exception_type(HTTPStatusError),
        stop=stop_after_delay(10),
        wait=wait_fixed(1),
    )
    async def __merge():
        (
            await gitlab_test_client.put(
                f"/projects/{test_repository.project['id']}/merge_requests/{merge_request['iid']}/merge",
            )
        ).raise_for_status()

    await __merge()

    # WHEN
    status = await test_gitlab_hoster.get_reconciliation_status(
        incarnation_repository=test_repository.project["path_with_namespace"],
        target_directory=".",
        commit_sha=test_repository.commit_sha_branch_without_pipeline,
        merge_request_id=merge_request["iid"],
    )

    # THEN
    assert status == ReconciliationStatus.SUCCESS


async def should_return_success_reconciliation_status_for_merged_merge_request_without_merge_commit_and_without_pipeline_in_target_branch(  # noqa: B950
    test_gitlab_hoster: Hoster, gitlab_test_client: AsyncClient, test_repository: RepositoryTestData
):
    # GIVEN
    (
        await gitlab_test_client.put(f"/projects/{test_repository.project['id']}", json={"merge_method": "ff"})
    ).raise_for_status()

    response = await gitlab_test_client.post(
        f"/projects/{test_repository.project['id']}/merge_requests",
        json={
            "source_branch": "without-pipeline",
            "target_branch": test_repository.project["default_branch"],
            "title": "Some merge request",
        },
    )
    response.raise_for_status()
    merge_request = response.json()

    @retry(
        retry=retry_if_exception_type(HTTPStatusError),
        stop=stop_after_delay(10),
        wait=wait_fixed(1),
    )
    async def __merge():
        (
            await gitlab_test_client.put(
                f"/projects/{test_repository.project['id']}/merge_requests/{merge_request['iid']}/merge",
            )
        ).raise_for_status()

    await __merge()

    # WHEN
    status = await test_gitlab_hoster.get_reconciliation_status(
        incarnation_repository=test_repository.project["path_with_namespace"],
        target_directory=".",
        commit_sha=test_repository.commit_sha_branch_without_pipeline,
        merge_request_id=merge_request["iid"],
    )

    # THEN
    assert status == ReconciliationStatus.SUCCESS


async def should_return_failed_reconciliation_status_for_closed_merge_request(
    test_gitlab_hoster: Hoster, gitlab_test_client: AsyncClient, test_repository: RepositoryTestData
):
    # GIVEN
    response = await gitlab_test_client.post(
        f"/projects/{test_repository.project['id']}/merge_requests",
        json={
            "source_branch": "without-pipeline",
            "target_branch": test_repository.project["default_branch"],
            "title": "Some merge request",
        },
    )
    response.raise_for_status()
    merge_request = response.json()
    (
        await gitlab_test_client.put(
            f"/projects/{test_repository.project['id']}/merge_requests/{merge_request['iid']}",
            json={"state_event": "close"},
        )
    ).raise_for_status()

    # WHEN
    status = await test_gitlab_hoster.get_reconciliation_status(
        incarnation_repository=test_repository.project["path_with_namespace"],
        target_directory=".",
        commit_sha=test_repository.commit_sha_branch_without_pipeline,
        merge_request_id=merge_request["iid"],
    )

    # THEN
    assert status == ReconciliationStatus.FAILED

import base64
from collections import namedtuple
from datetime import timedelta

import pytest
from httpx import Client, HTTPStatusError
from tenacity import retry
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_fixed

from foxops.hosters import Hoster, ReconciliationStatus
from foxops.hosters.gitlab import GitlabHoster
from foxops.hosters.types import MergeRequestStatus
from tests._plugins.fixtures_gitlab import GitlabTestSettings

# mark all tests in this module as e2e
pytestmark = pytest.mark.e2e


#: Holds a namedtuple for the test repository information
RepositoryTestData = namedtuple(
    "RepositoryTestData",
    ["project", "commit_sha_main", "commit_sha_branch_without_pipeline", "commit_sha_branch_with_pipeline"],
)


@pytest.fixture
def gitlab_project(gitlab_client: Client, gitlab_project_factory) -> RepositoryTestData:
    project = gitlab_project_factory("gitlab-hoster-test", initialize_with_readme=True)

    # Create new commit with new file in new branch without a pipeline
    response = gitlab_client.post(
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
    response = gitlab_client.post(
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


@pytest.fixture
async def gitlab_hoster(gitlab_settings: GitlabTestSettings) -> Hoster:
    assert gitlab_settings.token is not None

    return GitlabHoster(address=gitlab_settings.address, token=gitlab_settings.token.get_secret_value())


async def test_get_reconciliation_status_returns_success_for_default_branch_commit_without_pipeline(
    gitlab_hoster: Hoster, gitlab_project: RepositoryTestData
):
    # WHEN
    status = await gitlab_hoster.get_reconciliation_status(
        incarnation_repository=gitlab_project.project["path_with_namespace"],
        target_directory=".",
        commit_sha=gitlab_project.commit_sha_main,
        merge_request_id=None,
    )

    # THEN
    assert status == ReconciliationStatus.SUCCESS


async def test_get_reconciliation_status_returns_pending_for_default_branch_commit_with_pending_pipeline(
    gitlab_hoster: Hoster, gitlab_project: RepositoryTestData
):
    # WHEN
    status = await gitlab_hoster.get_reconciliation_status(
        incarnation_repository=gitlab_project.project["path_with_namespace"],
        target_directory=".",
        commit_sha=gitlab_project.commit_sha_branch_with_pipeline,
        merge_request_id=None,
        pipeline_timeout=timedelta(seconds=10),
    )

    # THEN
    assert status == ReconciliationStatus.PENDING


async def test_get_merge_request_status_returns_open_for_open_merge_request(
    gitlab_hoster: Hoster, gitlab_client: Client, gitlab_project: RepositoryTestData
):
    # GIVEN
    response = gitlab_client.post(
        f"/projects/{gitlab_project.project['id']}/merge_requests",
        json={
            "source_branch": "without-pipeline",
            "target_branch": gitlab_project.project["default_branch"],
            "title": "Some merge request",
        },
    )
    response.raise_for_status()
    merge_request = response.json()

    # WHEN
    status = await gitlab_hoster.get_merge_request_status(
        incarnation_repository=gitlab_project.project["path_with_namespace"],
        merge_request_id=merge_request["iid"],
    )

    # THEN
    assert status == MergeRequestStatus.OPEN


async def test_get_merge_request_status_returns_merged_for_merged_merge_request(
    gitlab_hoster: Hoster, gitlab_client: Client, gitlab_project: RepositoryTestData
):
    # GIVEN
    response = gitlab_client.post(
        f"/projects/{gitlab_project.project['id']}/merge_requests",
        json={
            "source_branch": "without-pipeline",
            "target_branch": gitlab_project.project["default_branch"],
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
            gitlab_client.put(
                f"/projects/{gitlab_project.project['id']}/merge_requests/{merge_request['iid']}/merge",
            )
        ).raise_for_status()

    await __merge()

    # WHEN
    status = await gitlab_hoster.get_merge_request_status(
        incarnation_repository=gitlab_project.project["path_with_namespace"],
        merge_request_id=merge_request["iid"],
    )

    # THEN
    assert status == MergeRequestStatus.MERGED


async def test_get_merge_request_status_returns_closed_for_closed_merge_request(
    gitlab_hoster: Hoster, gitlab_client: Client, gitlab_project: RepositoryTestData
):
    # GIVEN
    response = gitlab_client.post(
        f"/projects/{gitlab_project.project['id']}/merge_requests",
        json={
            "source_branch": "without-pipeline",
            "target_branch": gitlab_project.project["default_branch"],
            "title": "Some merge request",
        },
    )
    response.raise_for_status()
    merge_request = response.json()

    response = gitlab_client.put(
        f"/projects/{gitlab_project.project['id']}/merge_requests/{merge_request['iid']}",
        json={
            "state_event": "close",
        },
    )
    response.raise_for_status()

    # WHEN
    status = await gitlab_hoster.get_merge_request_status(
        incarnation_repository=gitlab_project.project["path_with_namespace"],
        merge_request_id=merge_request["iid"],
    )

    # THEN
    assert status == MergeRequestStatus.CLOSED


async def test_get_reconciliation_status_returns_pending_for_open_merge_request(
    gitlab_hoster: Hoster, gitlab_client: Client, gitlab_project: RepositoryTestData
):
    # GIVEN
    response = gitlab_client.post(
        f"/projects/{gitlab_project.project['id']}/merge_requests",
        json={
            "source_branch": "without-pipeline",
            "target_branch": gitlab_project.project["default_branch"],
            "title": "Some merge request",
        },
    )
    response.raise_for_status()
    merge_request = response.json()

    # WHEN
    status = await gitlab_hoster.get_reconciliation_status(
        incarnation_repository=gitlab_project.project["path_with_namespace"],
        target_directory=".",
        commit_sha=gitlab_project.commit_sha_branch_without_pipeline,
        merge_request_id=merge_request["iid"],
    )

    # THEN
    assert status == ReconciliationStatus.PENDING


async def test_get_reconciliation_status_return_success_for_merged_merge_request_without_pipeline_in_target_branch(
    gitlab_hoster: Hoster, gitlab_client: Client, gitlab_project: RepositoryTestData
):
    # GIVEN
    response = gitlab_client.post(
        f"/projects/{gitlab_project.project['id']}/merge_requests",
        json={
            "source_branch": "without-pipeline",
            "target_branch": gitlab_project.project["default_branch"],
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
            gitlab_client.put(
                f"/projects/{gitlab_project.project['id']}/merge_requests/{merge_request['iid']}/merge",
            )
        ).raise_for_status()

    await __merge()

    # WHEN
    status = await gitlab_hoster.get_reconciliation_status(
        incarnation_repository=gitlab_project.project["path_with_namespace"],
        target_directory=".",
        commit_sha=gitlab_project.commit_sha_branch_without_pipeline,
        merge_request_id=merge_request["iid"],
    )

    # THEN
    assert status == ReconciliationStatus.SUCCESS


async def test_get_reconciliation_status_return_success_for_merged_merge_request_without_merge_commit_and_without_pipeline_in_target_branch(  # noqa: B950
    gitlab_hoster: Hoster, gitlab_client: Client, gitlab_project: RepositoryTestData
):
    # GIVEN
    (gitlab_client.put(f"/projects/{gitlab_project.project['id']}", json={"merge_method": "ff"})).raise_for_status()

    response = gitlab_client.post(
        f"/projects/{gitlab_project.project['id']}/merge_requests",
        json={
            "source_branch": "without-pipeline",
            "target_branch": gitlab_project.project["default_branch"],
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
            gitlab_client.put(
                f"/projects/{gitlab_project.project['id']}/merge_requests/{merge_request['iid']}/merge",
            )
        ).raise_for_status()

    await __merge()

    # WHEN
    status = await gitlab_hoster.get_reconciliation_status(
        incarnation_repository=gitlab_project.project["path_with_namespace"],
        target_directory=".",
        commit_sha=gitlab_project.commit_sha_branch_without_pipeline,
        merge_request_id=merge_request["iid"],
    )

    # THEN
    assert status == ReconciliationStatus.SUCCESS


async def test_get_reconciliation_status_returns_failed_for_closed_merge_request(
    gitlab_hoster: Hoster, gitlab_client: Client, gitlab_project: RepositoryTestData
):
    # GIVEN
    response = gitlab_client.post(
        f"/projects/{gitlab_project.project['id']}/merge_requests",
        json={
            "source_branch": "without-pipeline",
            "target_branch": gitlab_project.project["default_branch"],
            "title": "Some merge request",
        },
    )
    response.raise_for_status()
    merge_request = response.json()
    (
        gitlab_client.put(
            f"/projects/{gitlab_project.project['id']}/merge_requests/{merge_request['iid']}",
            json={"state_event": "close"},
        )
    ).raise_for_status()

    # WHEN
    status = await gitlab_hoster.get_reconciliation_status(
        incarnation_repository=gitlab_project.project["path_with_namespace"],
        target_directory=".",
        commit_sha=gitlab_project.commit_sha_branch_without_pipeline,
        merge_request_id=merge_request["iid"],
    )

    # THEN
    assert status == ReconciliationStatus.FAILED

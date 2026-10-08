from datetime import timedelta
from http import HTTPStatus

import httpx
import pytest
from pytest_mock import MockerFixture

from foxops.errors import MergeRequestCreationFailedError
from foxops.hosters.gitlab import GitlabHoster

RETRY_TIMEOUT_PATH = "foxops.hosters.gitlab.MERGE_REQUEST_SOURCE_BRANCH_RETRY_TIMEOUT"
RETRY_WAIT_PATH = "foxops.hosters.gitlab.MERGE_REQUEST_SOURCE_BRANCH_RETRY_WAIT"

INCARNATION_REPOSITORY = "group/incarnation"
SOURCE_BRANCH = "foxops/update-ab12cd"

#: What GitLab answers while it does not see the freshly pushed branch yet.
SOURCE_BRANCH_MISSING_BODY = {"message": [f'Source branch "{SOURCE_BRANCH}" does not exist']}

CREATED_MERGE_REQUEST = {
    "iid": 42,
    "project_id": 1,
    "web_url": f"https://gitlab.example.com/{INCARNATION_REPOSITORY}/-/merge_requests/42",
    "sha": "0123456789abcdef0123456789abcdef01234567",
    "state": "opened",
    "merge_status": "can_be_merged",
    #: Anything but preparing/checking/unchecked, so the mergeability loop does not sleep.
    "detailed_merge_status": "mergeable",
    "merge_commit_sha": None,
    "head_pipeline": None,
}


class FakeGitlab:
    def __init__(self, create_responses: list[httpx.Response]) -> None:
        self._create_responses = create_responses
        self.create_attempts = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/merge_requests"):
            response = self._create_responses[min(self.create_attempts, len(self._create_responses) - 1)]
            self.create_attempts += 1
            return response

        if request.method != "GET":
            raise AssertionError(f"unexpected request: {request.method} {request.url}")

        if request.url.path.endswith("/merge_requests"):
            return httpx.Response(HTTPStatus.OK, json=[])

        return httpx.Response(
            HTTPStatus.OK,
            json={
                "default_branch": "main",
                "http_url_to_repo": f"https://gitlab.example.com/{INCARNATION_REPOSITORY}.git",
            },
        )


@pytest.fixture(autouse=True)
def fast_retry_wait(mocker: MockerFixture) -> None:
    mocker.patch(RETRY_WAIT_PATH, timedelta(seconds=0.01))


def build_hoster(fake_gitlab: FakeGitlab) -> GitlabHoster:
    hoster = GitlabHoster("https://gitlab.example.com", "token")
    hoster.client = httpx.AsyncClient(base_url=hoster.api_address, transport=httpx.MockTransport(fake_gitlab))
    return hoster


async def create_merge_request(fake_gitlab: FakeGitlab) -> tuple[str, str]:
    return await build_hoster(fake_gitlab).merge_request(
        incarnation_repository=INCARNATION_REPOSITORY,
        source_branch=SOURCE_BRANCH,
        title="Update to v1.2.3",
        description="Foxops detected no conflicts when applying this change.",
        incarnation_sub_directory=".",
    )


@pytest.mark.parametrize("status_code", [HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY])
async def test_merge_request_retries_until_gitlab_sees_the_pushed_branch(
    status_code: HTTPStatus, mocker: MockerFixture
):
    mocker.patch(RETRY_TIMEOUT_PATH, timedelta(seconds=5))
    fake_gitlab = FakeGitlab(
        [
            httpx.Response(status_code, json=SOURCE_BRANCH_MISSING_BODY),
            httpx.Response(HTTPStatus.CREATED, json=CREATED_MERGE_REQUEST),
        ]
    )

    sha, merge_request_id = await create_merge_request(fake_gitlab)

    assert fake_gitlab.create_attempts == 2
    assert sha == CREATED_MERGE_REQUEST["sha"]
    assert merge_request_id == "42"


async def test_merge_request_fails_cleanly_when_the_branch_never_becomes_visible(mocker: MockerFixture):
    mocker.patch(RETRY_TIMEOUT_PATH, timedelta(seconds=0.2))
    fake_gitlab = FakeGitlab([httpx.Response(HTTPStatus.BAD_REQUEST, json=SOURCE_BRANCH_MISSING_BODY)])

    with pytest.raises(MergeRequestCreationFailedError) as exc_info:
        await create_merge_request(fake_gitlab)

    assert fake_gitlab.create_attempts > 1
    assert SOURCE_BRANCH in str(exc_info.value)
    assert INCARNATION_REPOSITORY in str(exc_info.value)
    assert "does not exist" in str(exc_info.value)


async def test_merge_request_does_not_retry_unrelated_gitlab_errors():
    fake_gitlab = FakeGitlab([httpx.Response(HTTPStatus.FORBIDDEN, json={"message": "403 Forbidden"})])

    with pytest.raises(MergeRequestCreationFailedError) as exc_info:
        await create_merge_request(fake_gitlab)

    assert fake_gitlab.create_attempts == 1
    assert "403 Forbidden" in str(exc_info.value)

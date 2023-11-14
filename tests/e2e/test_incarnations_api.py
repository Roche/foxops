import base64
from http import HTTPStatus
from typing import Callable
from urllib.parse import quote_plus

import pytest
from httpx import AsyncClient, Client
from pytest_mock import MockFixture

from e2e.conftest import TemplateFactory, TemplateVersion, IncarnationFactory
from foxops.engine.models.template_config import TemplateConfig, StringVariableDefinition
from tests.e2e.assertions import (
    assert_file_in_repository,
    assert_update_merge_request_exists,
    assert_update_merge_request_with_conflicts_exists,
)

# mark all tests in this module as e2e
pytestmark = [pytest.mark.e2e, pytest.mark.api]


@pytest.fixture
def gitlab_incarnation_repository(gitlab_project_factory: Callable[[str], dict]) -> str:
    return gitlab_project_factory("incarnation")["path_with_namespace"]


async def test_post_incarnations_creates_incarnation_in_root_of_empty_repository(
    foxops_client: AsyncClient,
    gitlab_client: Client,
    gitlab_template_repository: str,
    gitlab_incarnation_repository: str,
    mocker: MockFixture,
):
    # GIVEN
    template_repository_version = "v1.0.0"
    template_data = {"name": "Jon", "age": "18"}

    # WHEN
    response = await foxops_client.post(
        "/api/incarnations",
        json={
            "incarnation_repository": gitlab_incarnation_repository,
            "template_repository": gitlab_template_repository,
            "template_repository_version": template_repository_version,
            "template_data": template_data,
        },
    )
    response.raise_for_status()
    incarnation = response.json()

    # THEN
    assert incarnation["incarnation_repository"] == gitlab_incarnation_repository
    assert incarnation["target_directory"] == "."
    assert incarnation["status"] == mocker.ANY
    assert incarnation["template_repository"] == gitlab_template_repository
    assert incarnation["template_repository_version"] == template_repository_version
    assert incarnation["template_data"] == template_data

    assert incarnation["id"] == mocker.ANY
    assert incarnation["commit_sha"] == mocker.ANY
    assert incarnation["commit_url"] == mocker.ANY
    assert incarnation["merge_request_id"] is None
    assert incarnation["merge_request_url"] == mocker.ANY
    assert incarnation["merge_request_status"] is None
    assert incarnation["template_repository_version_hash"] == mocker.ANY

    assert_file_in_repository(
        gitlab_client,
        gitlab_incarnation_repository,
        "README.md",
        "Jon is of age 18",
    )


async def test_post_incarnations_creates_incarnation_in_root_of_nonempty_repository_with_a_direct_commit(
    foxops_client: AsyncClient,
    gitlab_client: Client,
    gitlab_template_repository: str,
    gitlab_incarnation_repository: str,
    mocker: MockFixture,
):
    # GIVEN
    (
        gitlab_client.post(
            f"/projects/{quote_plus(gitlab_incarnation_repository)}/repository/files/{quote_plus('test.md')}",
            json={
                "encoding": "base64",
                "content": base64.b64encode(b"Hello World").decode("utf-8"),
                "commit_message": "Initial commit",
                "branch": "main",
            },
        )
    ).raise_for_status()

    # WHEN
    response = await foxops_client.post(
        "/api/incarnations",
        json={
            "incarnation_repository": gitlab_incarnation_repository,
            "template_repository": gitlab_template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Jon", "age": 18},
        },
    )
    response.raise_for_status()
    incarnation = response.json()

    # THEN
    assert incarnation["incarnation_repository"] == gitlab_incarnation_repository
    assert incarnation["target_directory"] == "."
    assert incarnation["status"] == mocker.ANY
    assert incarnation["commit_url"] == mocker.ANY
    assert incarnation["merge_request_id"] is None
    assert incarnation["merge_request_status"] is None
    assert incarnation["template_data"] == {"name": "Jon", "age": 18}

    assert incarnation["template_data_full"]["name"] == "Jon"
    assert incarnation["template_data_full"]["age"] == 18
    assert incarnation["template_data_full"]["country"] == "Switzerland"
    assert incarnation["template_data_full"]["fengine"]

    assert_file_in_repository(
        gitlab_client,
        gitlab_incarnation_repository,
        "README.md",
        "Jon is of age 18",
    )


async def test_post_incarnations_creates_incarnation_in_subdir_of_empty_repository(
    foxops_client: AsyncClient,
    gitlab_client: Client,
    gitlab_template_repository: str,
    gitlab_incarnation_repository: str,
    mocker: MockFixture,
):
    # WHEN
    response = await foxops_client.post(
        "/api/incarnations",
        json={
            "incarnation_repository": gitlab_incarnation_repository,
            "target_directory": "subdir",
            "template_repository": gitlab_template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Jon", "age": 18},
        },
    )
    response.raise_for_status()
    incarnation = response.json()

    # THEN
    assert incarnation["incarnation_repository"] == gitlab_incarnation_repository
    assert incarnation["target_directory"] == "subdir"
    assert incarnation["status"] == mocker.ANY
    assert incarnation["commit_url"] == mocker.ANY
    assert incarnation["merge_request_url"] == mocker.ANY
    assert incarnation["merge_request_status"] is None

    assert_file_in_repository(
        gitlab_client,
        gitlab_incarnation_repository,
        "subdir/README.md",
        "Jon is of age 18",
    )


async def test_post_incarnations_returns_error_if_variable_is_missing(
    foxops_client: AsyncClient,
    gitlab_template_repository: str,
    gitlab_incarnation_repository: str,
):
    # WHEN
    response = await foxops_client.post(
        "/api/incarnations",
        json={
            "incarnation_repository": gitlab_incarnation_repository,
            "template_repository": gitlab_template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Jon"},  # missing `age` variable
        },
    )

    # THEN
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "'age' - no value was provided for this required template variable" in response.json()["message"]


async def test_post_incarnations_returns_error_if_template_repository_version_does_not_exist(
    foxops_client: AsyncClient,
    gitlab_template_repository: str,
    gitlab_incarnation_repository: str,
):
    # GIVEN
    template_repository_version = "vNon-existing"
    template_data = {"name": "Jon", "age": "18"}

    # WHEN
    response = await foxops_client.post(
        "/api/incarnations",
        json={
            "incarnation_repository": gitlab_incarnation_repository,
            "template_repository": gitlab_template_repository,
            "template_repository_version": template_repository_version,
            "template_data": template_data,
        },
    )

    # THEN
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Revision 'vNon-existing' not found" in response.json()["message"]


async def test_multiple_post_incarnations_create_incarnations_in_subdirs_of_empty_repository(
    foxops_client: AsyncClient,
    gitlab_client: Client,
    gitlab_template_repository: str,
    gitlab_incarnation_repository: str,
    mocker: MockFixture,
):
    # WHEN
    subdir1_response = await foxops_client.post(
        "/api/incarnations",
        json={
            "incarnation_repository": gitlab_incarnation_repository,
            "target_directory": "subdir1",
            "template_repository": gitlab_template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Jon", "age": 18},
        },
    )
    subdir1_response.raise_for_status()
    subdir1_incarnation = subdir1_response.json()

    subdir2_response = await foxops_client.post(
        "/api/incarnations",
        json={
            "incarnation_repository": gitlab_incarnation_repository,
            "target_directory": "subdir2",
            "template_repository": gitlab_template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Ygritte", "age": 17},
        },
    )
    subdir2_response.raise_for_status()
    subdir2_incarnation = subdir2_response.json()

    # THEN
    assert subdir1_incarnation["id"] == 1
    assert subdir1_incarnation["incarnation_repository"] == gitlab_incarnation_repository
    assert subdir1_incarnation["target_directory"] == "subdir1"
    assert subdir1_incarnation["commit_url"] == mocker.ANY
    assert subdir1_incarnation["merge_request_url"] == mocker.ANY

    assert subdir2_incarnation["id"] == 2
    assert subdir2_incarnation["incarnation_repository"] == gitlab_incarnation_repository
    assert subdir2_incarnation["target_directory"] == "subdir2"
    assert subdir2_incarnation["commit_url"] == mocker.ANY
    assert subdir2_incarnation["merge_request_url"] == mocker.ANY

    assert_file_in_repository(
        gitlab_client,
        gitlab_incarnation_repository,
        "subdir1/README.md",
        "Jon is of age 18",
    )
    assert_file_in_repository(
        gitlab_client,
        gitlab_incarnation_repository,
        "subdir2/README.md",
        "Ygritte is of age 17",
    )


async def test_put_incarnation_updates_incarnation_with_merge_request(
    foxops_client: AsyncClient,
    gitlab_client: Client,
    gitlab_incarnation_repository_in_v1: tuple[str, str],
    mocker: MockFixture,
):
    # GIVEN
    incarnation_repository, incarnation_id = gitlab_incarnation_repository_in_v1

    # WHEN
    response = await foxops_client.put(
        f"/api/incarnations/{incarnation_id}",
        json={
            "template_repository_version": "v2.0.0",
            "template_data": {"name": "Jon", "age": 18},
            "automerge": False,
        },
    )
    response.raise_for_status()
    incarnation = response.json()

    # THEN
    assert incarnation["incarnation_repository"] == incarnation_repository
    assert incarnation["target_directory"] == "."
    assert incarnation["status"] == "pending"
    assert incarnation["commit_url"] == mocker.ANY
    assert incarnation["merge_request_url"] == mocker.ANY
    assert incarnation["template_data"] == {"name": "Jon", "age": 18}

    assert incarnation["template_data_full"]["name"] == "Jon"
    assert incarnation["template_data_full"]["age"] == 18
    assert incarnation["template_data_full"]["country"] == "Switzerland"
    assert incarnation["template_data_full"]["fengine"]

    update_branch_name = assert_update_merge_request_exists(gitlab_client, incarnation_repository)
    assert_file_in_repository(
        gitlab_client,
        incarnation_repository,
        "README.md",
        "Hello Jon, age: 18",
        branch=update_branch_name,
    )


async def test_put_incarnation_updates_incarnation_with_merge_request_and_automerge(
    foxops_client: AsyncClient,
    gitlab_client: Client,
    gitlab_incarnation_repository_in_v1: tuple[str, str],
    mocker: MockFixture,
):
    # GIVEN
    incarnation_repository, incarnation_id = gitlab_incarnation_repository_in_v1

    # WHEN
    response = await foxops_client.put(
        f"/api/incarnations/{incarnation_id}",
        json={
            "template_repository_version": "v2.0.0",
            "template_data": {"name": "Jon", "age": 18},
            "automerge": True,
        },
    )
    response.raise_for_status()
    incarnation = response.json()

    # THEN
    assert incarnation["incarnation_repository"] == incarnation_repository
    assert incarnation["target_directory"] == "."
    assert incarnation["status"] == "success"
    assert incarnation["commit_url"] == mocker.ANY
    assert incarnation["merge_request_url"] == mocker.ANY
    assert incarnation["merge_request_status"] == "merged"

    assert_file_in_repository(
        gitlab_client,
        incarnation_repository,
        "README.md",
        "Hello Jon, age: 18",
    )


@pytest.mark.parametrize(
    "automerge",
    [True, False],
)
async def test_put_incarnation_creates_merge_request_with_conflicts(
    automerge: bool,
    foxops_client: AsyncClient,
    gitlab_client: Client,
    gitlab_incarnation_repository_in_v1: tuple[str, str],
    mocker: MockFixture,
):
    # GIVEN
    incarnation_repository, incarnation_id = gitlab_incarnation_repository_in_v1
    (
        gitlab_client.put(
            f"/projects/{quote_plus(incarnation_repository)}/repository/files/{quote_plus('README.md')}",
            json={
                "encoding": "base64",
                "content": base64.b64encode(
                    b"test",
                ).decode("utf-8"),
                "commit_message": "Same line in incarnation changed as in template v2",
                "branch": "main",
            },
        )
    ).raise_for_status()

    # WHEN
    response = await foxops_client.put(
        f"/api/incarnations/{incarnation_id}",
        json={
            "template_repository_version": "v2.0.0",
            "template_data": {"name": "Jon", "age": 18},
            "automerge": automerge,
        },
    )
    response.raise_for_status()
    incarnation = response.json()

    # THEN
    assert incarnation["incarnation_repository"] == incarnation_repository
    assert incarnation["target_directory"] == "."
    assert incarnation["status"] == "pending"
    assert incarnation["commit_url"] == mocker.ANY
    assert incarnation["merge_request_url"] == mocker.ANY
    assert incarnation["merge_request_status"] == "open"

    assert_update_merge_request_with_conflicts_exists(
        gitlab_client,
        incarnation_repository,
        files_with_conflicts=["README.md"],
    )


async def test_put_incarnation_fails_if_insufficient_template_data_is_provided(
    foxops_client: AsyncClient,
    gitlab_incarnation_factory: IncarnationFactory,
):
    # GIVEN
    template_config = TemplateConfig(
        variables={
            "name": StringVariableDefinition(description="dummy", default="Amy"),
            "age": StringVariableDefinition(description="dummy"),
        }
    )
    incarnation_repo, incarnation_id = await gitlab_incarnation_factory(
        [
            TemplateVersion(
                version="v1.0.0",
                config=template_config,
                files={
                    "README.md": b"{{ name }} is of age {{ age }}",
                },
            ),
        ],
        {"name": "Jon", "age": 18},
    )

    # WHEN
    response = await foxops_client.put(
        f"/api/incarnations/{incarnation_id}",
        json={
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Jane"},
            "automerge": True,
        },
    )

    # THEN
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "'age' - no value was provided for this required template variable" in response.json()["message"]


async def test_patch_incarnation_returns_error_if_the_previous_one_has_not_been_merged(
    foxops_client: AsyncClient,
    gitlab_incarnation_repository_in_v1: tuple[str, str],
):
    # GIVEN
    incarnation_repository, incarnation_id = gitlab_incarnation_repository_in_v1
    response = await foxops_client.put(
        f"/api/incarnations/{incarnation_id}",
        json={
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Jon", "age": 19},
            "automerge": False,
        },
    )
    response.raise_for_status()

    # WHEN
    response = await foxops_client.patch(
        f"/api/incarnations/{incarnation_id}",
        json={
            "requested_version": "v2.0.0",
            "automerge": False,
        },
    )

    # THEN
    assert response.status_code == HTTPStatus.CONFLICT


async def test_patch_incarnation_creates_merge_requests_for_updated_data(
    foxops_client: AsyncClient,
    gitlab_client: Client,
    gitlab_incarnation_factory: IncarnationFactory,
):
    # GIVEN
    template_config = TemplateConfig(
        variables={
            "name": StringVariableDefinition(description="dummy", default="Amy"),
            "age": StringVariableDefinition(description="dummy"),
        }
    )
    incarnation_repo, incarnation_id = await gitlab_incarnation_factory(
        [
            TemplateVersion(
                version="v1.0.0",
                config=template_config,
                files={
                    "README.md": b"{{ name }} is of age {{ age }}",
                },
            ),
        ],
        {"name": "Jon", "age": 18},
    )

    # WHEN
    response = await foxops_client.patch(
        f"/api/incarnations/{incarnation_id}",
        json={
            "requested_data": {"age": 20},
            "automerge": True,
        },
    )

    # THEN
    assert response.status_code == HTTPStatus.OK

    assert_file_in_repository(
        gitlab_client,
        incarnation_repo,
        "README.md",
        "Jon is of age 20",
    )


async def test_get_incarnations_returns_all_incarnations(
    foxops_client: AsyncClient,
    gitlab_incarnation_repository: str,
    gitlab_template_repository: str,
):
    # GIVEN
    for i in range(2):
        response = await foxops_client.post(
            "/api/incarnations",
            json={
                "incarnation_repository": gitlab_incarnation_repository,
                "target_directory": f"subdir{i}",
                "template_repository": gitlab_template_repository,
                "template_repository_version": "v1.0.0",
                "template_data": {"name": "Jon", "age": 18},
            },
        )
        response.raise_for_status()

    # WHEN
    response = await foxops_client.get("/api/incarnations")
    response.raise_for_status()
    incarnations = response.json()

    # THEN
    assert len(incarnations) == 2

    inc0 = [inc for inc in incarnations if inc["target_directory"] == "subdir0"][0]
    inc1 = [inc for inc in incarnations if inc["target_directory"] == "subdir1"][0]

    assert inc0["id"] is not None
    assert inc0["incarnation_repository"] == gitlab_incarnation_repository
    assert inc0["target_directory"] == "subdir0"

    assert inc0["revision"] == 1
    assert inc0["type"] == "direct"
    assert inc0["requested_version"] == "v1.0.0"
    assert inc0["created_at"] is not None

    assert inc0["commit_sha"] is not None
    assert inc0["commit_url"].startswith("http")
    assert inc0["merge_request_id"] is None
    assert inc0["merge_request_url"] is None

    assert inc1


async def test_get_incarnations_returns_single_incarnation_when_queried(
    foxops_client: AsyncClient,
    gitlab_incarnation_repository: str,
    gitlab_template_repository: str,
):
    # GIVEN
    for i in range(2):
        response = await foxops_client.post(
            "/api/incarnations",
            json={
                "incarnation_repository": gitlab_incarnation_repository,
                "target_directory": f"subdir{i}",
                "template_repository": gitlab_template_repository,
                "template_repository_version": "v1.0.0",
                "template_data": {"name": "Jon", "age": 18},
            },
        )
        response.raise_for_status()

    # WHEN
    response = await foxops_client.get(
        "/api/incarnations",
        params={"incarnation_repository": gitlab_incarnation_repository, "target_directory": "subdir1"},
    )
    response.raise_for_status()

    incarnations = response.json()

    # THEN
    assert len(incarnations) == 1
    assert incarnations[0]["target_directory"] == "subdir1"


async def test_get_incarnations_returns_error_if_given_incarnation_does_not_exist(
    foxops_client: AsyncClient,
):
    # GIVEN
    incarnation_repo = "non-existing"

    # WHEN
    response = await foxops_client.get("/api/incarnations", params={"incarnation_repository": incarnation_repo})

    # THEN
    assert response.status_code == HTTPStatus.NOT_FOUND


async def test_delete_incarnation_removes_incarnation_when_there_are_changes(
    foxops_client: AsyncClient,
    gitlab_client: Client,
    gitlab_incarnation_repository_in_v1: tuple[str, str],
):
    # GIVEN
    incarnation_repository, incarnation_id = gitlab_incarnation_repository_in_v1
    response = await foxops_client.put(
        f"/api/incarnations/{incarnation_id}",
        json={
            "template_repository_version": "v2.0.0",
            "template_data": {"name": "Jon", "age": 18},
            "automerge": True,
        },
    )
    response.raise_for_status()

    # WHEN
    response = await foxops_client.delete(f"/api/incarnations/{incarnation_id}")
    response.raise_for_status()

    # THEN
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert (await foxops_client.get(f"/api/incarnations/{incarnation_id}")).status_code == HTTPStatus.NOT_FOUND


async def test_post_incarnation_reset_creates_merge_request_that_resets_incarnation(
    foxops_client: AsyncClient,
    gitlab_client: Client,
    gitlab_incarnation_repository_in_v1: tuple[str, str],
):
    # GIVEN
    incarnation_repository, incarnation_id = gitlab_incarnation_repository_in_v1
    response = gitlab_client.put(
        f"/projects/{quote_plus(incarnation_repository)}/repository/files/{quote_plus('README.md')}",
        json={
            "encoding": "base64",
            "content": base64.b64encode(
                b"test",
            ).decode("utf-8"),
            "commit_message": "adding a custom file",
            "branch": "main",
        },
    )
    response.raise_for_status()

    # WHEN
    response = await foxops_client.post(f"/api/incarnations/{incarnation_id}/reset")
    response.raise_for_status()

    response_data = response.json()

    # THEN
    assert response.status_code == HTTPStatus.OK
    assert str(response_data["incarnation_id"]) == incarnation_id
    assert response_data["merge_request_id"] is not None
    assert response_data["merge_request_url"].startswith("http")

    response = gitlab_client.get(
        f"/projects/{quote_plus(incarnation_repository)}/merge_requests/{response_data['merge_request_id']}"
    )
    response.raise_for_status()

import base64
from http import HTTPStatus
from urllib.parse import quote_plus

import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture

from tests.e2e.assertions import (
    assert_file_in_repository,
    assert_update_merge_request_exists,
    assert_update_merge_request_with_conflicts_exists,
)

# mark all tests in this module as e2e
pytestmark = [pytest.mark.e2e, pytest.mark.api]


async def should_initialize_incarnation_in_root_of_empty_repository_when_creating_incarnation(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
    mocker: MockFixture,
):
    # GIVEN
    template_repository_version = "v1.0.0"
    template_data = {"name": "Jon", "age": "18"}

    # WHEN
    response = await api_client.post(
        "/incarnations",
        json={
            "incarnation_repository": empty_incarnation_gitlab_repository,
            "template_repository": template_repository,
            "template_repository_version": template_repository_version,
            "template_data": template_data,
        },
    )
    response.raise_for_status()
    incarnation = response.json()

    # THEN
    assert incarnation["incarnation_repository"] == empty_incarnation_gitlab_repository
    assert incarnation["target_directory"] == "."
    assert incarnation["status"] == mocker.ANY
    assert incarnation["template_repository"] == template_repository
    assert incarnation["template_repository_version"] == template_repository_version
    assert incarnation["template_data"] == template_data

    assert incarnation["id"] == mocker.ANY
    assert incarnation["commit_sha"] == mocker.ANY
    assert incarnation["commit_url"] == mocker.ANY
    assert incarnation["merge_request_id"] is None
    assert incarnation["merge_request_url"] == mocker.ANY
    assert incarnation["merge_request_status"] is None
    assert incarnation["template_repository_version_hash"] == mocker.ANY

    await assert_file_in_repository(
        gitlab_test_client,
        empty_incarnation_gitlab_repository,
        "README.md",
        "Jon is of age 18",
    )


async def should_initialize_incarnation_in_root_of_repository_with_fvars_file_when_creating_incarnation(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
    mocker: MockFixture,
):
    # GIVEN
    (
        await gitlab_test_client.post(
            f"/projects/{quote_plus(empty_incarnation_gitlab_repository)}/repository/files/{quote_plus('default.fvars')}",
            json={
                "encoding": "base64",
                "content": base64.b64encode(b"name=Jon").decode("utf-8"),
                "commit_message": "Add fvars file",
                "branch": "main",
            },
        )
    ).raise_for_status()

    # WHEN
    response = await api_client.post(
        "/incarnations",
        json={
            "incarnation_repository": empty_incarnation_gitlab_repository,
            "template_repository": template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"age": 18},
        },
    )
    response.raise_for_status()
    incarnation = response.json()

    # THEN
    assert incarnation["incarnation_repository"] == empty_incarnation_gitlab_repository
    assert incarnation["target_directory"] == "."
    assert incarnation["status"] == mocker.ANY
    assert incarnation["commit_url"] == mocker.ANY
    assert incarnation["merge_request_id"] is None

    await assert_file_in_repository(
        gitlab_test_client,
        empty_incarnation_gitlab_repository,
        "README.md",
        "Jon is of age 18",
    )


async def should_initialize_incarnation_in_root_of_nonempty_incarnation_with_a_direct_commit(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
    mocker: MockFixture,
):
    # GIVEN
    (
        await gitlab_test_client.post(
            f"/projects/{quote_plus(empty_incarnation_gitlab_repository)}/repository/files/{quote_plus('test.md')}",
            json={
                "encoding": "base64",
                "content": base64.b64encode(b"Hello World").decode("utf-8"),
                "commit_message": "Initial commit",
                "branch": "main",
            },
        )
    ).raise_for_status()

    # WHEN
    response = await api_client.post(
        "/incarnations",
        json={
            "incarnation_repository": empty_incarnation_gitlab_repository,
            "template_repository": template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Jon", "age": 18},
        },
    )
    response.raise_for_status()
    incarnation = response.json()

    # THEN
    assert incarnation["incarnation_repository"] == empty_incarnation_gitlab_repository
    assert incarnation["target_directory"] == "."
    assert incarnation["status"] == mocker.ANY
    assert incarnation["commit_url"] == mocker.ANY
    assert incarnation["merge_request_id"] is None
    assert incarnation["merge_request_status"] is None

    await assert_file_in_repository(
        gitlab_test_client,
        empty_incarnation_gitlab_repository,
        "README.md",
        "Jon is of age 18",
    )


async def should_initialize_incarnation_in_root_of_nonempty_repository_with_fvars_file_when_creating_incarnation(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
    mocker: MockFixture,
):
    # GIVEN
    (
        await gitlab_test_client.post(
            f"/projects/{quote_plus(empty_incarnation_gitlab_repository)}/repository/files/{quote_plus('default.fvars')}",
            json={
                "encoding": "base64",
                "content": base64.b64encode(b"name=Jon").decode("utf-8"),
                "commit_message": "Add fvars file",
                "branch": "main",
            },
        )
    ).raise_for_status()
    (
        await gitlab_test_client.post(
            f"/projects/{quote_plus(empty_incarnation_gitlab_repository)}/repository/files/{quote_plus('test.md')}",
            json={
                "encoding": "base64",
                "content": base64.b64encode(b"Hello World").decode("utf-8"),
                "commit_message": "Initial commit",
                "branch": "main",
            },
        )
    ).raise_for_status()

    # WHEN
    response = await api_client.post(
        "/incarnations",
        json={
            "incarnation_repository": empty_incarnation_gitlab_repository,
            "template_repository": template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"age": 18},
        },
    )
    response.raise_for_status()
    incarnation = response.json()

    # THEN
    assert incarnation["incarnation_repository"] == empty_incarnation_gitlab_repository
    assert incarnation["target_directory"] == "."
    assert incarnation["status"] == "success"
    assert incarnation["commit_url"] == mocker.ANY
    assert incarnation["merge_request_url"] == mocker.ANY
    await assert_file_in_repository(
        gitlab_test_client,
        empty_incarnation_gitlab_repository,
        "README.md",
        "Jon is of age 18",
    )


async def should_err_in_initialization_if_variable_is_missing(
    api_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
    mocker: MockFixture,
):
    # WHEN
    response = await api_client.post(
        "/incarnations",
        json={
            "incarnation_repository": empty_incarnation_gitlab_repository,
            "template_repository": template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Jon"},  # missing `age` variable
        },
    )

    # THEN
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert (
        "the template required the variables ['age', 'name'] but the provided template data for the incarnation where ['name']."
        in response.json()["message"]
    )


async def should_initialize_incarnation_in_subdir_of_empty_repository_when_creating_incarnation(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
    mocker: MockFixture,
):
    # WHEN
    response = await api_client.post(
        "/incarnations",
        json={
            "incarnation_repository": empty_incarnation_gitlab_repository,
            "target_directory": "subdir",
            "template_repository": template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Jon", "age": 18},
        },
    )
    response.raise_for_status()
    incarnation = response.json()

    # THEN
    assert incarnation["incarnation_repository"] == empty_incarnation_gitlab_repository
    assert incarnation["target_directory"] == "subdir"
    assert incarnation["status"] == mocker.ANY
    assert incarnation["commit_url"] == mocker.ANY
    assert incarnation["merge_request_url"] == mocker.ANY
    assert incarnation["merge_request_status"] is None

    await assert_file_in_repository(
        gitlab_test_client,
        empty_incarnation_gitlab_repository,
        "subdir/README.md",
        "Jon is of age 18",
    )


async def should_initialize_incarnations_in_subdirs_of_empty_repository_when_creating_incarnation(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
    mocker: MockFixture,
):
    # WHEN
    subdir1_response = await api_client.post(
        "/incarnations",
        json={
            "incarnation_repository": empty_incarnation_gitlab_repository,
            "target_directory": "subdir1",
            "template_repository": template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Jon", "age": 18},
        },
    )
    subdir1_response.raise_for_status()
    subdir1_incarnation = subdir1_response.json()

    subdir2_response = await api_client.post(
        "/incarnations",
        json={
            "incarnation_repository": empty_incarnation_gitlab_repository,
            "target_directory": "subdir2",
            "template_repository": template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Ygritte", "age": 17},
        },
    )
    subdir2_response.raise_for_status()
    subdir2_incarnation = subdir2_response.json()

    # THEN
    assert subdir1_incarnation["id"] == 1
    assert subdir1_incarnation["incarnation_repository"] == empty_incarnation_gitlab_repository
    assert subdir1_incarnation["target_directory"] == "subdir1"
    assert subdir1_incarnation["commit_url"] == mocker.ANY
    assert subdir1_incarnation["merge_request_url"] == mocker.ANY

    assert subdir2_incarnation["id"] == 2
    assert subdir2_incarnation["incarnation_repository"] == empty_incarnation_gitlab_repository
    assert subdir2_incarnation["target_directory"] == "subdir2"
    assert subdir2_incarnation["commit_url"] == mocker.ANY
    assert subdir2_incarnation["merge_request_url"] == mocker.ANY

    await assert_file_in_repository(
        gitlab_test_client,
        empty_incarnation_gitlab_repository,
        "subdir1/README.md",
        "Jon is of age 18",
    )
    await assert_file_in_repository(
        gitlab_test_client,
        empty_incarnation_gitlab_repository,
        "subdir2/README.md",
        "Ygritte is of age 17",
    )


async def should_create_merge_request_when_file_changed_during_update(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    incarnation_gitlab_repository_in_v1: tuple[str, str],
    mocker: MockFixture,
):
    # GIVEN
    incarnation_repository, incarnation_id = incarnation_gitlab_repository_in_v1

    # WHEN
    response = await api_client.put(
        f"/incarnations/{incarnation_id}",
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

    update_branch_name = await assert_update_merge_request_exists(gitlab_test_client, incarnation_repository)
    await assert_file_in_repository(
        gitlab_test_client,
        incarnation_repository,
        "README.md",
        "Hello Jon, age: 18",
        branch=update_branch_name,
    )


async def should_create_merge_request_when_file_changed_with_fvars_during_update(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    incarnation_gitlab_repository_in_v1: tuple[str, str],
    mocker: MockFixture,
):
    # GIVEN
    incarnation_repository, incarnation_id = incarnation_gitlab_repository_in_v1
    (
        await gitlab_test_client.post(
            f"/projects/{quote_plus(incarnation_repository)}/repository/files/{quote_plus('default.fvars')}",
            json={
                "encoding": "base64",
                "content": base64.b64encode(b"name=Jon").decode("utf-8"),
                "commit_message": "Add fvars file",
                "branch": "main",
            },
        )
    ).raise_for_status()

    # WHEN
    response = await api_client.put(
        f"/incarnations/{incarnation_id}",
        json={
            "template_repository_version": "v2.0.0",
            "template_data": {"age": 18},
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

    update_branch_name = await assert_update_merge_request_exists(gitlab_test_client, incarnation_repository)
    await assert_file_in_repository(
        gitlab_test_client,
        incarnation_repository,
        "README.md",
        "Hello Jon, age: 18",
        branch=update_branch_name,
    )


@pytest.mark.parametrize(
    "automerge",
    [True, False],
)
async def should_present_conflict_in_merge_request_when_updating(
    automerge: bool,
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    incarnation_gitlab_repository_in_v1: tuple[str, str],
    mocker: MockFixture,
):
    # GIVEN
    incarnation_repository, incarnation_id = incarnation_gitlab_repository_in_v1
    (
        await gitlab_test_client.put(
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
    response = await api_client.put(
        f"/incarnations/{incarnation_id}",
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

    await assert_update_merge_request_with_conflicts_exists(
        gitlab_test_client,
        incarnation_repository,
        files_with_conflicts=["README.md"],
    )


async def should_automerge_merge_request_when_flag_is_true(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    incarnation_gitlab_repository_in_v1: tuple[str, str],
    mocker: MockFixture,
):
    # GIVEN
    incarnation_repository, incarnation_id = incarnation_gitlab_repository_in_v1

    # WHEN
    response = await api_client.put(
        f"/incarnations/{incarnation_id}",
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

    await assert_file_in_repository(
        gitlab_test_client,
        incarnation_repository,
        "README.md",
        "Hello Jon, age: 18",
    )


async def should_err_initialize_incarnation_if_template_repository_version_does_not_exist(
    api_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
):
    # GIVEN
    template_repository_version = "vNon-existing"
    template_data = {"name": "Jon", "age": "18"}

    # WHEN
    response = await api_client.post(
        "/incarnations",
        json={
            "incarnation_repository": empty_incarnation_gitlab_repository,
            "template_repository": template_repository,
            "template_repository_version": template_repository_version,
            "template_data": template_data,
        },
    )

    # THEN
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Revision 'vNon-existing' not found" in response.json()["message"]


async def test_list_incarnations_should_return_all_incarnations(
    api_client: AsyncClient,
    empty_incarnation_gitlab_repository: str,
    template_repository: str,
):
    # GIVEN
    for i in range(2):
        response = await api_client.post(
            "/incarnations",
            json={
                "incarnation_repository": empty_incarnation_gitlab_repository,
                "target_directory": f"subdir{i}",
                "template_repository": template_repository,
                "template_repository_version": "v1.0.0",
                "template_data": {"name": "Jon", "age": 18},
            },
        )
        response.raise_for_status()

    # WHEN
    response = await api_client.get("/incarnations")
    response.raise_for_status()
    incarnations = response.json()

    # THEN
    assert len(incarnations) == 2

    inc0 = [inc for inc in incarnations if inc["target_directory"] == "subdir0"][0]
    inc1 = [inc for inc in incarnations if inc["target_directory"] == "subdir1"][0]

    assert inc0["id"] is not None
    assert inc0["incarnation_repository"] == empty_incarnation_gitlab_repository
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


async def test_list_incarnations_returns_single_incarnation_when_queried(
    api_client: AsyncClient,
    empty_incarnation_gitlab_repository: str,
    template_repository: str,
):
    # GIVEN
    for i in range(2):
        response = await api_client.post(
            "/incarnations",
            json={
                "incarnation_repository": empty_incarnation_gitlab_repository,
                "target_directory": f"subdir{i}",
                "template_repository": template_repository,
                "template_repository_version": "v1.0.0",
                "template_data": {"name": "Jon", "age": 18},
            },
        )
        response.raise_for_status()

    # WHEN
    response = await api_client.get(
        "/incarnations",
        params={"incarnation_repository": empty_incarnation_gitlab_repository, "target_directory": "subdir1"},
    )
    response.raise_for_status()

    incarnations = response.json()

    # THEN
    assert len(incarnations) == 1
    assert incarnations[0]["target_directory"] == "subdir1"


async def test_list_incarnations_returns_not_found_if_given_incarnation_does_not_exist(
    api_client: AsyncClient,
):
    # GIVEN
    incarnation_repo = "non-existing"

    # WHEN
    response = await api_client.get("/incarnations", params={"incarnation_repository": incarnation_repo})

    # THEN
    assert response.status_code == HTTPStatus.NOT_FOUND


async def test_update_incarnation_should_fail_if_the_previous_one_has_not_been_merged(
    api_client: AsyncClient,
    incarnation_gitlab_repository_in_v1: tuple[str, str],
):
    # GIVEN
    incarnation_repository, incarnation_id = incarnation_gitlab_repository_in_v1
    response = await api_client.put(
        f"/incarnations/{incarnation_id}",
        json={
            "template_data": {"name": "Jon", "age": 19},
            "automerge": False,
        },
    )
    response.raise_for_status()

    # WHEN
    response = await api_client.put(
        f"/incarnations/{incarnation_id}",
        json={
            "template_repository_version": "v2.0.0",
            "automerge": False,
        },
    )

    # THEN
    assert response.status_code == HTTPStatus.CONFLICT


async def test_delete_incarnation_succeeds_when_there_are_changes(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    incarnation_gitlab_repository_in_v1: tuple[str, str],
):
    # GIVEN
    incarnation_repository, incarnation_id = incarnation_gitlab_repository_in_v1
    response = await api_client.put(
        f"/incarnations/{incarnation_id}",
        json={
            "template_repository_version": "v2.0.0",
            "template_data": {"name": "Jon", "age": 18},
            "automerge": True,
        },
    )
    response.raise_for_status()

    # WHEN
    response = await api_client.delete(f"/incarnations/{incarnation_id}")
    response.raise_for_status()

    # THEN
    assert response.status_code == HTTPStatus.NO_CONTENT


async def test_reset_incarnation_succeeds(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    incarnation_gitlab_repository_in_v1: tuple[str, str],
):
    # GIVEN
    incarnation_repository, incarnation_id = incarnation_gitlab_repository_in_v1
    response = await gitlab_test_client.put(
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
    response = await api_client.post(f"/incarnations/{incarnation_id}/reset")
    response.raise_for_status()

    response_data = response.json()

    # THEN
    assert response.status_code == HTTPStatus.OK
    assert str(response_data["incarnation_id"]) == incarnation_id
    assert response_data["merge_request_id"] is not None
    assert response_data["merge_request_url"].startswith("http")

    response = await gitlab_test_client.get(
        f"/projects/{quote_plus(incarnation_repository)}/merge_requests/{response_data['merge_request_id']}"
    )
    response.raise_for_status()

import base64
from http import HTTPStatus
from urllib.parse import quote_plus

import pytest
from httpx import AsyncClient

from .assertions import (
    assert_file_in_repository,
    assert_initialization_merge_request_exists,
    assert_update_merge_request_exists,
    assert_update_merge_request_with_conflicts_exists,
)

# mark all tests in this module as e2e
pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def should_initialize_incarnation_in_root_of_empty_repository_when_creating_incarnation(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
):
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
    assert incarnation["id"] is not None
    await assert_file_in_repository(
        gitlab_test_client,
        empty_incarnation_gitlab_repository,
        "README.md",
        "Jon is of age 18",
    )


@pytest.mark.asyncio
async def should_initialize_incarnation_in_root_of_repository_with_fvars_file_when_creating_incarnation(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
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
    assert incarnation["id"] is not None
    await assert_file_in_repository(
        gitlab_test_client,
        empty_incarnation_gitlab_repository,
        "README.md",
        "Jon is of age 18",
    )


@pytest.mark.asyncio
async def should_initialize_incarnation_in_root_of_nonempty_incarnation_in_a_merge_request(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
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

    # THEN
    merge_request_source_branch = await assert_initialization_merge_request_exists(
        gitlab_test_client, empty_incarnation_gitlab_repository
    )
    await assert_file_in_repository(
        gitlab_test_client,
        empty_incarnation_gitlab_repository,
        "README.md",
        "Jon is of age 18",
        branch=merge_request_source_branch,
    )


@pytest.mark.asyncio
async def should_initialize_incarnation_in_root_of_nonempty_incarnation_in_default_branch_with_automerge(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
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
            "automerge": True,
        },
    )
    response.raise_for_status()

    # THEN
    await assert_file_in_repository(
        gitlab_test_client,
        empty_incarnation_gitlab_repository,
        "README.md",
        "Jon is of age 18",
    )


@pytest.mark.asyncio
async def should_initialize_incarnation_in_root_of_nonempty_repository_with_fvars_file_when_creating_incarnation(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
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

    # THEN
    merge_request_branch_name = await assert_initialization_merge_request_exists(
        gitlab_test_client, empty_incarnation_gitlab_repository
    )
    await assert_file_in_repository(
        gitlab_test_client,
        empty_incarnation_gitlab_repository,
        "README.md",
        "Jon is of age 18",
        branch=merge_request_branch_name,
    )


@pytest.mark.asyncio
async def should_err_in_initialization_if_variable_is_missing(
    api_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
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


@pytest.mark.asyncio
async def should_initialize_incarnation_in_subdir_of_empty_repository_when_creating_incarnation(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
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

    # THEN
    await assert_file_in_repository(
        gitlab_test_client,
        empty_incarnation_gitlab_repository,
        "subdir/README.md",
        "Jon is of age 18",
    )


@pytest.mark.asyncio
async def should_initialize_incarnations_in_subdirs_of_empty_repository_when_creating_incarnation(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    empty_incarnation_gitlab_repository: str,
):
    # WHEN
    (
        await api_client.post(
            "/incarnations",
            json={
                "incarnation_repository": empty_incarnation_gitlab_repository,
                "target_directory": "subdir1",
                "template_repository": template_repository,
                "template_repository_version": "v1.0.0",
                "template_data": {"name": "Jon", "age": 18},
            },
        )
    ).raise_for_status()
    (
        await api_client.post(
            "/incarnations",
            json={
                "incarnation_repository": empty_incarnation_gitlab_repository,
                "target_directory": "subdir2",
                "template_repository": template_repository,
                "template_repository_version": "v1.0.0",
                "template_data": {"name": "Ygritte", "age": 17},
            },
        )
    ).raise_for_status()

    # THEN
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


@pytest.mark.asyncio
async def should_create_merge_request_when_file_changed_during_update(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    incarnation_gitlab_repository_in_v1: tuple[str, str],
):
    # GIVEN
    incarnation_repository, incarnation_id = incarnation_gitlab_repository_in_v1

    # WHEN
    (
        await api_client.put(
            f"/incarnations/{incarnation_id}",
            json={
                "template_repository_version": "v2.0.0",
                "template_data": {"name": "Jon", "age": 18},
                "automerge": False,
            },
        )
    ).raise_for_status()

    # THEN
    update_branch_name = await assert_update_merge_request_exists(gitlab_test_client, incarnation_repository)
    await assert_file_in_repository(
        gitlab_test_client,
        incarnation_repository,
        "README.md",
        "Hello Jon, age: 18",
        branch=update_branch_name,
    )


@pytest.mark.asyncio
async def should_create_merge_request_when_file_changed_with_fvars_during_update(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    incarnation_gitlab_repository_in_v1: tuple[str, str],
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
    (
        await api_client.put(
            f"/incarnations/{incarnation_id}",
            json={
                "template_repository_version": "v2.0.0",
                "template_data": {"age": 18},
                "automerge": False,
            },
        )
    ).raise_for_status()

    # THEN
    update_branch_name = await assert_update_merge_request_exists(gitlab_test_client, incarnation_repository)
    await assert_file_in_repository(
        gitlab_test_client,
        incarnation_repository,
        "README.md",
        "Hello Jon, age: 18",
        branch=update_branch_name,
    )


@pytest.mark.asyncio
async def should_present_conflict_in_merge_request_when_updating(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    incarnation_gitlab_repository_in_v1: tuple[str, str],
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
    (
        await api_client.put(
            f"/incarnations/{incarnation_id}",
            json={
                "template_repository_version": "v2.0.0",
                "template_data": {"name": "Jon", "age": 18},
                "automerge": False,
            },
        )
    ).raise_for_status()

    # THEN
    await assert_update_merge_request_with_conflicts_exists(
        gitlab_test_client,
        incarnation_repository,
        files_with_conflicts=["README.md"],
    )


@pytest.mark.asyncio
async def should_automerge_merge_request_when_flag_is_true(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    incarnation_gitlab_repository_in_v1: tuple[str, str],
):
    # GIVEN
    incarnation_repository, incarnation_id = incarnation_gitlab_repository_in_v1

    # WHEN
    (
        await api_client.put(
            f"/incarnations/{incarnation_id}",
            json={
                "template_repository_version": "v2.0.0",
                "template_data": {"name": "Jon", "age": 18},
                "automerge": True,
            },
        )
    ).raise_for_status()

    # THEN
    await assert_file_in_repository(
        gitlab_test_client,
        incarnation_repository,
        "README.md",
        "Hello Jon, age: 18",
    )

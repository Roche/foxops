import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture

from tests.e2e.assertions import (
    assert_file_in_repository,
    assert_update_merge_request_exists,
)


async def test_can_update_legacy_incarnation_without_automerge(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    mocker: MockFixture,
    legacy_incarnation_gitlab_repository_in_v1: tuple[str, str],
):
    # GIVEN
    incarnation_repository, incarnation_id = legacy_incarnation_gitlab_repository_in_v1

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
    assert incarnation["merge_request_status"] == "open"

    branch = await assert_update_merge_request_exists(gitlab_test_client, incarnation_repository)
    await assert_file_in_repository(
        gitlab_test_client,
        incarnation_repository,
        "README.md",
        "Hello Jon, age: 18",
        branch=branch,
    )


async def test_can_update_legacy_incarnation_with_automerge(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    template_repository: str,
    mocker: MockFixture,
    legacy_incarnation_gitlab_repository_in_v1: tuple[str, str],
):
    # GIVEN
    incarnation_repository, incarnation_id = legacy_incarnation_gitlab_repository_in_v1

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

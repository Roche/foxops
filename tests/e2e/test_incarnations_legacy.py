from http import HTTPStatus

import pytest
from httpx import AsyncClient
from pytest_mock import MockFixture

from tests.e2e.assertions import (
    assert_file_in_repository,
    assert_update_merge_request_exists,
)

pytestmark = [pytest.mark.e2e, pytest.mark.api]


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


async def test_delete_incarnation_succeeds_on_legacy_incarnation(
    api_client: AsyncClient,
    gitlab_test_client: AsyncClient,
    legacy_incarnation_gitlab_repository_in_v1: tuple[str, str],
):
    # GIVEN
    incarnation_repository, incarnation_id = legacy_incarnation_gitlab_repository_in_v1

    # WHEN
    response = await api_client.delete(f"/incarnations/{incarnation_id}")
    response.raise_for_status()

    # THEN
    assert response.status_code == HTTPStatus.NO_CONTENT


async def test_upgrade_all_incarnations(
    api_client: AsyncClient,
    gitlab_project_factory,
    gitlab_test_client: AsyncClient,
    template_repository: str,
):
    # GIVEN
    # 3 legacy incarnations, of which one is no longer existing on Gitlab
    # 1 incarnation that is already upgraded

    incarnation_ids = []
    for i in range(3):
        project = await gitlab_project_factory(f"incarnation-{i}")
        response = await api_client.post(
            "/incarnations/legacy",
            json={
                "incarnation_repository": project["path_with_namespace"],
                "template_repository": template_repository,
                "template_repository_version": "v1.0.0",
                "template_data": {"name": "Jon", "age": 18},
            },
        )
        response.raise_for_status()
        incarnation = response.json()

        incarnation_ids.append(incarnation["id"])

        # if this is the first incarnation we created, let's delete the corresponding gitlab project
        if i == 0:
            response = await gitlab_test_client.delete(f"/projects/{project['id']}")
            response.raise_for_status()

    # create one new-style incarnation
    project = await gitlab_project_factory("incarnation-new")
    await api_client.post(
        "/incarnations",
        json={
            "incarnation_repository": project["path_with_namespace"],
            "target_directory": "subdir1",
            "template_repository": template_repository,
            "template_repository_version": "v1.0.0",
            "template_data": {"name": "Jon", "age": 18},
        },
    )

    # WHEN
    response = await api_client.post("/incarnations/upgrade-all")
    response.raise_for_status()
    run_1 = response.json()

    response = await api_client.post("/incarnations/upgrade-all", params={"delete_nonexisting": "true"})
    response.raise_for_status()

    run_2 = response.json()

    # THEN
    assert len(run_1["failed_upgrades"]) == 1
    assert run_1["failed_upgrades"][0][0] == incarnation_ids[0]
    assert len(run_1["successful_upgrades"]) == 2
    assert set([incarnation[0] for incarnation in run_1["successful_upgrades"]]) == set(incarnation_ids[1:])

    # the previously failed upgrade should still fail. otherwise, nothing should be done anymore
    assert len(run_2["failed_upgrades"]) == 0
    assert run_2["failed_upgrades"][0][0] == incarnation_ids[0]
    assert len(run_2["successful_upgrades"]) == 0
    assert len(run_2["deleted_incarnations"]) == 0

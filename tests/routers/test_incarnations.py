import json
from datetime import datetime
from http import HTTPStatus
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from pytest_mock import MockFixture

from foxops.database.repositories.change.repository import ChangeRepository
from foxops.database.repositories.incarnation.errors import IncarnationNotFoundError
from foxops.database.repositories.incarnation.repository import IncarnationRepository
from foxops.dependencies import get_change_service
from foxops.models.change import Change
from foxops.services.change import ChangeService, IncarnationAlreadyExists

pytestmark = [pytest.mark.api]


MOCK_DIFF_OUTPUT = """diff --git a/home/foxops/templating/NewFile b/home/foxops/templating/NewFile
new file mode 100644
index 0000000..29b8f23
--- /dev/null
+++ b/home/foxops/templating/NewFile
@@ -0,0 +1 @@
+Hello, World!
diff --git a/home/foxops/templating/script.py b/home/foxops/templating/script.py
index 636af66..336f590 100644
"""


class ChangeServiceMock(Mock):
    def __init__(self):
        super().__init__(spec=ChangeService)

    async def create_incarnation(
        self,
        incarnation_repository: str,
        template_repository: str,
        template_repository_version: str,
        template_data: dict[str, str],
        target_directory: str = ".",
    ) -> Change:
        return Change(
            id=1,
            incarnation_id=1,
            revision=1,
            requested_version_hash="template_commit_sha",
            requested_version=template_repository_version,
            requested_data=template_data,
            template_data_full=template_data,
            created_at=datetime.now(),
            commit_sha="commit_sha",
        )


@pytest.fixture
def change_service_mock(app: FastAPI):
    change_service = ChangeServiceMock()

    app.dependency_overrides[get_change_service] = lambda: change_service

    return change_service


@pytest.fixture
def incarnation_repository_mock(app: FastAPI):
    incarnation_repository = Mock(spec=IncarnationRepository)

    app.dependency_overrides[IncarnationRepository] = lambda: incarnation_repository

    return incarnation_repository


async def test_api_get_incarnations_returns_empty_list_for_empty_incarnation_inventory(
    api_client: AsyncClient,
):
    # WHEN
    response = await api_client.get("/incarnations")

    # THEN
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


async def test_api_get_incarnations_returns_incarnations_from_inventory(
    api_client: AsyncClient,
    change_repository: ChangeRepository,
    mocker: MockFixture,
):
    # GIVEN
    await change_repository.create_incarnation_with_first_change(
        incarnation_repository="test",
        target_directory="test",
        template_repository="template",
        commit_sha="commit_sha",
        requested_version="v1.0",
        requested_version_hash="template_commit_sha",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
    )

    # WHEN
    response = await api_client.get("/incarnations")

    # THEN
    assert response.status_code == HTTPStatus.OK
    assert response.json() == [
        {
            "id": 1,
            "incarnation_repository": "test",
            "target_directory": "test",
            "commit_sha": "commit_sha",
            "commit_url": mocker.ANY,
            "merge_request_id": None,
            "merge_request_url": None,
            "created_at": mocker.ANY,
            "template_repository": "template",
            "requested_version": "v1.0",
            "revision": 1,
            "type": "direct",
        }
    ]


async def test_api_create_incarnation(
    api_client: AsyncClient,
    app: FastAPI,
    mocker: MockFixture,
    change_service_mock: ChangeService,
):
    # GIVEN
    requested_incarnation = {
        "incarnation_repository": "test",
        "target_directory": "test",
        "template_repository": "template",
        "template_repository_version": "test",
        "template_data": {"foo": "bar"},
    }
    change_service_mock.get_incarnation_with_details = mocker.AsyncMock(return_value="dummy-object")  # type: ignore

    # WHEN
    response = await api_client.post(
        "/incarnations",
        json=requested_incarnation,
    )

    # THEN
    assert response.status_code == HTTPStatus.CREATED


async def test_api_create_incarnation_returns_conflict_when_incarnation_already_exists(
    api_client: AsyncClient,
    mocker: MockFixture,
    change_service_mock: ChangeService,
):
    # GIVEN
    change_service_mock.create_incarnation = mocker.AsyncMock(side_effect=IncarnationAlreadyExists)  # type: ignore

    # WHEN
    response = await api_client.post(
        "/incarnations",
        json={
            "incarnation_repository": "test",
            "target_directory": "test",
            "template_repository": "test",
            "template_repository_version": "test",
            "template_data": {"foo": "bar"},
        },
    )

    # THEN
    assert response.status_code == HTTPStatus.CONFLICT


async def test_api_delete_incarnation_removes_incarnation_from_inventory(
    api_client: AsyncClient,
    incarnation_repository: IncarnationRepository,
):
    # GIVEN
    incarnation = await incarnation_repository.create(
        incarnation_repository="test",
        target_directory="test",
        template_repository="template_repo",
    )

    # WHEN
    response = await api_client.delete(f"/incarnations/{incarnation.id}")

    # THEN
    assert response.status_code == HTTPStatus.NO_CONTENT

    assert len([i async for i in incarnation_repository.list()]) == 0


async def test_api_get_diff_returns_diff_for_incarnation(
    api_client: AsyncClient,
    change_service_mock: ChangeService,
    mocker: MockFixture,
):
    change_service_mock.diff_incarnation = mocker.AsyncMock(return_value=MOCK_DIFF_OUTPUT)  # type: ignore

    response = await api_client.get("/incarnations/1/diff")

    assert response.status_code == HTTPStatus.OK
    assert response.text == MOCK_DIFF_OUTPUT

    assert change_service_mock.diff_incarnation.call_count == 1  # type: ignore
    assert change_service_mock.diff_incarnation.call_args == mocker.call(1)  # type: ignore


async def test_api_get_diff_of_non_existing_incarnation_returns_not_found(
    api_client: AsyncClient,
    incarnation_repository_mock: IncarnationRepository,
    mocker: MockFixture,
):
    incarnation_repository_mock.get_by_id = mocker.AsyncMock(side_effect=IncarnationNotFoundError)  # type: ignore

    response = await api_client.get("/incarnations/1/diff")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"message": "could not find incarnation in DB with id: 1"}

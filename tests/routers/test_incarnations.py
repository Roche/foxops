from datetime import datetime
from http import HTTPStatus
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy import text

from foxops.database import DAL
from foxops.dependencies import get_change_service, get_hoster
from foxops.models.change import Change
from foxops.services.change import ChangeService, IncarnationAlreadyExists

pytestmark = [pytest.mark.api]


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
            created_at=datetime.now(),
            commit_sha="commit_sha",
        )


@pytest.fixture
def change_service_mock(app: FastAPI):
    change_service = ChangeServiceMock()

    app.dependency_overrides[get_change_service] = lambda: change_service

    return change_service


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
    dal: DAL,
):
    # GIVEN
    async with dal.connection() as conn:
        await conn.execute(text("INSERT INTO incarnation VALUES (1, 'test', 'test', 'commit_sha', 'merge_request_id')"))
        await conn.commit()

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
            "commit_url": "https://nonsense.com/test/-/commit/commit_sha",
            "merge_request_id": "merge_request_id",
            "merge_request_url": "https://nonsense.com/test/-/merge_requests/merge_request_id",
        }
    ]


async def test_api_create_incarnation(
    api_client: AsyncClient,
    app: FastAPI,
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
    change_service_mock.get_incarnation_with_details.return_value = "dummy-object"

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


async def test_api_create_incarnation_fails_when_called_with_allow_import(
    api_client: AsyncClient,
):
    # WHEN
    response = await api_client.post(
        "/incarnations",
        params={"allow_import": "true"},
        json={
            "incarnation_repository": "test",
            "target_directory": "test",
            "template_repository": "test",
            "template_repository_version": "test",
            "template_data": {"foo": "bar"},
        },
    )

    # THEN
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_api_delete_incarnation_removes_incarnation_from_inventory(
    api_client: AsyncClient,
    dal: DAL,
):
    # GIVEN
    async with dal.connection() as conn:
        await conn.execute(text("INSERT INTO incarnation VALUES (1, 'test', 'test', 'commit_sha', 'merge_request_id')"))
        await conn.commit()

    # WHEN
    response = await api_client.delete("/incarnations/1")

    # THEN
    assert response.status_code == HTTPStatus.NO_CONTENT
    async with dal.connection() as conn:
        actual_incarnations = await conn.execute(text("SELECT 1 FROM incarnation"))
    assert actual_incarnations.scalar_one_or_none() is None

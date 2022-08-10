from http import HTTPStatus

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from pytest_mock import MockFixture
from sqlalchemy import text

from foxops.database import DAL
from foxops.dependencies import get_hoster
from foxops.errors import IncarnationAlreadyInitializedError
from foxops.routers.incarnations import get_reconciliation


@pytest.mark.asyncio
async def test_api_get_incarnations_returns_empty_list_for_empty_incarnation_inventory(
    api_client: AsyncClient,
):
    # WHEN
    response = await api_client.get("/incarnations")

    # THEN
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


@pytest.mark.asyncio
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
        }
    ]


@pytest.mark.asyncio
async def test_api_create_incarnation_adds_new_incarnation_to_inventory(
    api_client: AsyncClient,
    api_app: FastAPI,
    mocker: MockFixture,
):
    # GIVEN
    reconciliation_mock = mocker.AsyncMock()
    reconciliation_mock.initialize_incarnation.return_value = "commit_sha", "merge_request_id"
    hoster_mock = mocker.AsyncMock()
    hoster_mock.get_reconciliation_status.return_value = "success"

    api_app.dependency_overrides[get_reconciliation] = lambda: reconciliation_mock
    api_app.dependency_overrides[get_hoster] = lambda: hoster_mock

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
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        "id": 1,
        "incarnation_repository": "test",
        "target_directory": "test",
        "status": "success",
    }


@pytest.mark.asyncio
async def test_api_create_incarnation_already_exists_without_allowing_import(
    api_client: AsyncClient,
    api_app: FastAPI,
    dal: DAL,
    mocker: MockFixture,
):
    # GIVEN
    async with dal.connection() as conn:
        await conn.execute(text("INSERT INTO incarnation VALUES (1, 'test', 'test', 'commit_sha', 'merge_request_id')"))
        await conn.commit()

    reconciliation_mock = mocker.AsyncMock()
    reconciliation_mock.initialize_incarnation.side_effect = IncarnationAlreadyInitializedError(
        "test",
        "test",
        "fake-commit_sha",
        has_mismatch=False,
    )

    api_app.dependency_overrides[get_reconciliation] = lambda: reconciliation_mock

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
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_api_create_incarnation_already_exists_allowing_import_without_a_mismatch(
    api_client: AsyncClient,
    api_app: FastAPI,
    dal: DAL,
    mocker: MockFixture,
):
    # GIVEN
    async with dal.connection() as conn:
        await conn.execute(text("INSERT INTO incarnation VALUES (1, 'test', 'test', 'commit_sha', 'merge_request_id')"))
        await conn.commit()

    reconciliation_mock = mocker.AsyncMock()
    reconciliation_mock.initialize_incarnation.side_effect = IncarnationAlreadyInitializedError(
        "test",
        "test",
        "fake-commit_sha",
        has_mismatch=False,
    )

    hoster_mock = mocker.AsyncMock()
    hoster_mock.get_reconciliation_status.return_value = "success"

    api_app.dependency_overrides[get_reconciliation] = lambda: reconciliation_mock
    api_app.dependency_overrides[get_hoster] = lambda: hoster_mock

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
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "id": 1,
        "incarnation_repository": "test",
        "target_directory": "test",
        "status": "success",
    }


@pytest.mark.asyncio
async def test_api_create_incarnation_already_exists_allowing_import_with_a_mismatch(
    api_client: AsyncClient,
    api_app: FastAPI,
    dal: DAL,
    mocker: MockFixture,
):
    # GIVEN
    async with dal.connection() as conn:
        await conn.execute(text("INSERT INTO incarnation VALUES (1, 'test', 'test', 'commit_sha', 'merge_request_id')"))
        await conn.commit()

    reconciliation_mock = mocker.AsyncMock()
    reconciliation_mock.initialize_incarnation.side_effect = IncarnationAlreadyInitializedError(
        "test",
        "test",
        "fake-commit_sha",
        has_mismatch=True,
    )

    hoster_mock = mocker.AsyncMock()
    hoster_mock.get_reconciliation_status.return_value = "success"

    api_app.dependency_overrides[get_reconciliation] = lambda: reconciliation_mock
    api_app.dependency_overrides[get_hoster] = lambda: hoster_mock

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
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {
        "id": 1,
        "incarnation_repository": "test",
        "target_directory": "test",
        "status": "success",
    }


@pytest.mark.asyncio
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

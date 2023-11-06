from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from foxops.dependencies import get_change_service
from foxops.hosters.types import MergeRequestStatus
from foxops.models.change import Change, ChangeWithMergeRequest
from foxops.services.change import ChangeService


@pytest.fixture
def change_service_mock(app: FastAPI):
    change_service = Mock(spec_set=ChangeService)

    app.dependency_overrides[get_change_service] = lambda: change_service

    return change_service


async def test_create_change(api_client: AsyncClient, change_service_mock: ChangeService):
    # GIVEN
    change_service_mock.create_change_direct = AsyncMock(  # type: ignore
        return_value=Change(
            id=1,
            incarnation_id=1,
            revision=2,
            requested_version="1.0.0",
            requested_version_hash="template_commit_sha",
            requested_data={},
            template_data_full={},
            created_at=datetime.now(timezone.utc),
            commit_sha="commit_sha",
        )
    )

    # WHEN
    response = await api_client.post(
        "/incarnations/1/changes", json={"change_type": "direct", "requested_version": "1.0.0"}
    )

    # THEN
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["revision"] == 2


async def test_list_changes(api_client: AsyncClient, change_service_mock: ChangeService):
    # GIVEN
    change_service_mock.list_changes = AsyncMock(  # type: ignore
        return_value=[
            ChangeWithMergeRequest(
                id=1,
                incarnation_id=1,
                revision=2,
                requested_version="1.1.0",
                requested_version_hash="template_commit_sha",
                requested_data={},
                template_data_full={},
                created_at=datetime.now(timezone.utc),
                commit_sha="commit_sha",
                merge_request_id="1",
                merge_request_branch_name="branch_name",
                merge_request_status=MergeRequestStatus.OPEN,
            ),
            Change(
                id=1,
                incarnation_id=1,
                revision=1,
                requested_version="1.0.0",
                requested_version_hash="template_commit_sha",
                requested_data={},
                template_data_full={},
                created_at=datetime.now(timezone.utc),
                commit_sha="commit_sha",
            ),
        ]
    )

    # WHEN
    response = await api_client.get("/incarnations/1/changes")
    data = response.json()

    # THEN
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 2

    assert data[0]["revision"] == 2
    assert data[0]["type"] == "merge_request"
    assert data[0]["merge_request_id"] == "1"
    assert data[0]["merge_request_status"] == "open"

    assert data[1]["revision"] == 1

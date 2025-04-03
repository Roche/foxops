import json

import pytest
from fastapi import status
from httpx import AsyncClient
from pytest_mock import MockFixture

from foxops.database.repositories.change.repository import ChangeRepository
from foxops.database.repositories.group.repository import GroupRepository
from foxops.database.repositories.incarnation.repository import IncarnationRepository
from foxops.database.repositories.user.errors import UserNotFoundError
from foxops.database.repositories.user.repository import UserRepository
from foxops.database.schema import Permission
from foxops.models.group import Group
from foxops.models.incarnation import UserPermission
from foxops.models.user import User, UserWithGroups

pytestmark = [pytest.mark.api]


@pytest.fixture
async def test_user(user_repository: UserRepository) -> User:
    user = await user_repository.create(
        username="test_user",
        is_admin=False,
    )
    return User.model_validate(user)


@pytest.fixture
async def test_group(group_repository: GroupRepository) -> Group:
    group = await group_repository.create(
        system_name="test_group",
        display_name="test_group",
    )
    return Group.model_validate(group)


async def test_user_and_group_get_created_on_request(
    unauthenticated_client: AsyncClient,
    static_api_token: str,
    user_repository: UserRepository,
    mocker: MockFixture,
    group_repository: GroupRepository,
):
    with pytest.raises(UserNotFoundError):
        # The user should not exist yet
        await user_repository.get_by_username("user1")

    unauthenticated_client.headers["Authorization"] = f"Bearer {static_api_token}"
    unauthenticated_client.headers["User"] = "user1"
    unauthenticated_client.headers["Groups"] = "group1,group2"

    response = await unauthenticated_client.get("/auth/test")

    assert response.status_code == status.HTTP_200_OK

    response_model = response.json()

    assert response_model == {
        "id": mocker.ANY,
        "username": "user1",
        "groups": [
            {
                "id": mocker.ANY,
                "system_name": "group1",
                "display_name": "group1",
            },
            {
                "id": mocker.ANY,
                "system_name": "group2",
                "display_name": "group2",
            },
        ],
        "is_admin": False,
    }

    db_user = await user_repository.get_by_username("user1")

    response_user = UserWithGroups.model_validate(response_model)

    assert db_user.id == response_user.id
    assert db_user.username == "user1"
    assert db_user.is_admin is False

    db_groups = await group_repository.get_by_userid(db_user.id)

    assert len(db_groups) == 2

    assert {"group1", "group2"} == {group.system_name for group in db_groups}
    assert {"group1", "group2"} == {group.system_name for group in response_user.groups}


@pytest.mark.parametrize(
    "method,endpoint",
    [
        ("GET", "/user"),
        ("GET", "/user/1"),
        ("PATCH", "/user/1"),
        ("DELETE", "/user/1"),
        ("GET", "/group"),
        ("GET", "/group/1"),
        ("PATCH", "/group/1"),
        ("DELETE", "/group/1"),
    ],
)
async def test_unpriviliged_user_cant_access_group_and_user_endpoints(
    method: str,
    endpoint: str,
    unprivileged_api_client: AsyncClient,
):
    response = await unprivileged_api_client.request(method, endpoint)

    assert response.status_code == status.HTTP_403_FORBIDDEN, response.json()
    assert response.json() == {"message": "Only administrators are allowed to access this endpoint"}


@pytest.mark.parametrize(
    "method,endpoint,body,expected_status",
    [
        ("GET", "/user", None, status.HTTP_200_OK),
        ("GET", "/user/{user_id}", None, status.HTTP_200_OK),
        ("PATCH", "/user/{user_id}", {"is_admin": True}, status.HTTP_200_OK),
        ("DELETE", "/user/{user_id}", None, status.HTTP_204_NO_CONTENT),
        ("GET", "/group", None, status.HTTP_200_OK),
        ("GET", "/group/{group_id}", None, status.HTTP_200_OK),
        ("PATCH", "/group/{group_id}", {"display_name": "new_display_name"}, status.HTTP_200_OK),
        ("DELETE", "/group/{group_id}", None, status.HTTP_204_NO_CONTENT),
    ],
)
async def test_priviliged_user_can_access_group_and_user_endpoints(
    method: str,
    endpoint: str,
    api_client: AsyncClient,
    test_user: User,
    test_group: Group,
    body: dict,
    expected_status: int,
):
    response = await api_client.request(
        method, endpoint.format(user_id=test_user.id, group_id=test_group.id), json=body or {}
    )

    assert response.status_code == expected_status


async def test_cant_update_owner_field_with_write_permissions(
    unprivileged_api_client: AsyncClient,
    change_repository: ChangeRepository,
    unprivileged_api_user: User,
    incarnation_repository: IncarnationRepository,
    priviliged_api_user: User,
):
    incarnation = await change_repository.create_incarnation_with_first_change(
        incarnation_repository="incarnation",
        target_directory=".",
        template_repository="template",
        commit_sha="commit_sha",
        requested_version="v1.0",
        requested_version_hash="template_commit_sha",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
        owner_id=priviliged_api_user.id,
    )

    await incarnation_repository.set_user_permissions(
        incarnation.id,
        [
            UserPermission(user=unprivileged_api_user, type=Permission.WRITE),
        ],
    )
    response = await unprivileged_api_client.patch(f"/incarnations/{incarnation.id}", json={"owner_id": 2})

    assert response.status_code == status.HTTP_403_FORBIDDEN, response.request.content

import pytest

from foxops.database.repositories.group.repository import GroupRepository
from foxops.database.repositories.user.errors import UserAlreadyExistsError
from foxops.database.repositories.user.repository import UserRepository


async def test_cant_create_two_users_with_the_same_username(
    user_repository: UserRepository,
):
    await user_repository.create(
        username="user1",
        is_admin=False,
    )

    with pytest.raises(UserAlreadyExistsError) as excinfo:
        await user_repository.create(
            username="user1",
            is_admin=False,
        )

    assert str(excinfo.value) == "User with username 'user1' already exists."


async def test_default_admin_user_exists(
    user_repository: UserRepository,
):
    user = await user_repository.get_by_username("root")

    assert user is not None
    assert user.username == "root"
    assert user.is_admin is True


async def test_user_can_join_group(
    user_repository: UserRepository,
    group_repository: GroupRepository,
):
    user = await user_repository.create(
        username="user1",
        is_admin=False,
    )

    group = await group_repository.create(
        system_name="group1",
        display_name="group1",
    )

    user_groups = await group_repository.get_by_userid(user.id)

    assert len(user_groups) == 0

    await user_repository.join_groups(
        user_id=user.id,
        group_ids=[group.id],
    )

    user_groups = await group_repository.get_by_userid(user.id)

    assert len(user_groups) == 1

    assert user_groups[0].id == group.id
    assert user_groups[0].system_name == group.system_name
    assert user_groups[0].display_name == group.display_name


async def test_user_can_be_promoted_to_administrator(
    user_repository: UserRepository,
):
    user = await user_repository.create(
        username="user1",
        is_admin=False,
    )

    assert user.is_admin is False

    db_user = await user_repository.get_by_id(user.id)

    assert db_user.is_admin is False

    await user_repository.set_is_admin(
        user_id=user.id,
        is_admin=True,
    )

    db_user = await user_repository.get_by_id(user.id)

    assert db_user.is_admin is True
    assert db_user.username == user.username
    assert db_user.id == user.id

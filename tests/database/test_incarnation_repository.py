from pytest import fixture, raises

from foxops.database.repositories.change.repository import ChangeRepository
from foxops.database.repositories.incarnation.errors import (
    IncarnationAlreadyExistsError,
    IncarnationNotFoundError,
)
from foxops.database.repositories.incarnation.model import IncarnationInDB
from foxops.database.repositories.incarnation.repository import IncarnationRepository
from foxops.database.repositories.user.repository import UserRepository
from foxops.models.user import User


@fixture
async def user(user_repository: UserRepository):
    return await user_repository.create(
        username="test",
        is_admin=False,
    )


@fixture(scope="function", name="incarnation_id")
async def create_incarnation(incarnation_repository: IncarnationRepository, user: User) -> int:
    new_incarnation = await incarnation_repository.create(
        incarnation_repository="incarnation_repo",
        target_directory="test",
        template_repository="template_repo",
        owner_id=user.id,
    )
    return new_incarnation.id


async def test_create_adds_new_incarnation_to_inventory(incarnation_repository: IncarnationRepository, user: User):
    # WHEN
    new_incarnation = await incarnation_repository.create(
        incarnation_repository="incarnation_repo",
        target_directory="test",
        template_repository="template_repo",
        owner_id=user.id,
    )

    # THEN
    assert new_incarnation.id > 0

    actual_incarnations = [i async for i in incarnation_repository.list()]
    assert len(actual_incarnations) == 1


async def test_create_raises_exception_when_same_incarnation_exists_already(
    incarnation_repository: IncarnationRepository, user: User
):
    # GIVEN
    await incarnation_repository.create(
        incarnation_repository="incarnation_repo",
        target_directory="test",
        template_repository="template_repo",
        owner_id=user.id,
    )

    # THEN
    with raises(IncarnationAlreadyExistsError):
        await incarnation_repository.create(
            incarnation_repository="incarnation_repo",
            target_directory="test",
            template_repository="template_repo2",
            owner_id=user.id,
        )


async def test_get_by_id_returns_existing_incarnation(
    incarnation_repository: IncarnationRepository, incarnation_id: int, user: User
):
    # WHEN
    actual_incarnation = await incarnation_repository.get_by_id(incarnation_id)

    # THEN
    assert actual_incarnation == IncarnationInDB(
        id=incarnation_id,
        incarnation_repository="incarnation_repo",
        target_directory="test",
        template_repository="template_repo",
        owner=user.id,
    )


async def test_get_by_id_raises_exception_when_incarnation_does_not_exist(
    incarnation_repository: IncarnationRepository,
):
    # THEN
    with raises(IncarnationNotFoundError):
        await incarnation_repository.get_by_id(1)


async def test_list_returns_empty_list_for_empty_incarnation_inventory(incarnation_repository: IncarnationRepository):
    # WHEN
    actual_incarnations = [i async for i in incarnation_repository.list()]

    # THEN
    assert actual_incarnations == []


async def test_list_returns_existing_incarnations(incarnation_repository: IncarnationRepository, incarnation_id: int):
    # WHEN
    actual_incarnations = [i async for i in incarnation_repository.list()]

    # THEN
    assert len(actual_incarnations) == 1
    assert actual_incarnations[0].id == incarnation_id


async def test_delete_by_id_returns_none_when_deleting_existing_incarnation(
    incarnation_repository: IncarnationRepository, change_repository: ChangeRepository, incarnation_id: int
):
    # WHEN
    await incarnation_repository.delete_by_id(incarnation_id)

    # THEN
    assert len(await change_repository.list_changes(incarnation_id)) == 0
    with raises(IncarnationNotFoundError):
        await incarnation_repository.get_by_id(incarnation_id)


async def test_delete_by_id_raises_exception_when_deleting_non_existing_incarnation(
    incarnation_repository: IncarnationRepository,
):
    # THEN
    with raises(IncarnationNotFoundError):
        await incarnation_repository.delete_by_id(1)

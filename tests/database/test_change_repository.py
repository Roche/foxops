import json

import pytest
from pytest import fixture

from foxops.database.repositories.change.errors import (
    ChangeCommitAlreadyPushedError,
    ChangeConflictError,
    ChangeNotFoundError,
    IncarnationHasNoChangesError,
)
from foxops.database.repositories.change.model import ChangeType
from foxops.database.repositories.change.repository import ChangeRepository
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


@fixture(scope="function")
async def incarnation(incarnation_repository: IncarnationRepository, user: User) -> IncarnationInDB:
    return await incarnation_repository.create(
        incarnation_repository="test", target_directory="test", template_repository="test", owner_id=user.id
    )


async def test_create_change_persists_all_data(change_repository: ChangeRepository, incarnation: IncarnationInDB):
    # WHEN
    change = await change_repository.create_change(
        incarnation_id=incarnation.id,
        revision=1,
        change_type=ChangeType.DIRECT,
        commit_sha="dummy sha",
        commit_pushed=True,
        requested_version_hash="dummy template sha",
        requested_version="v99",
        requested_data="dummy data (should be json)",
        template_data_full="dummy data (should be json)",
        merge_request_id="123",
        merge_request_branch_name="mybranch",
    )

    assert change.id is not None
    assert change.type == ChangeType.DIRECT
    assert change.template_data_full == "dummy data (should be json)"


async def test_create_change_rejects_double_revision(change_repository: ChangeRepository, incarnation: IncarnationInDB):
    # GIVEN
    await change_repository.create_change(
        incarnation_id=incarnation.id,
        revision=1,
        change_type=ChangeType.DIRECT,
        requested_version_hash="dummy template sha",
        requested_version="v2",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
        commit_sha="dummy sha",
        commit_pushed=False,
    )

    # THEN
    with pytest.raises(ChangeConflictError):
        await change_repository.create_change(
            incarnation_id=incarnation.id,
            revision=1,
            change_type=ChangeType.DIRECT,
            requested_version_hash="dummy template sha2",
            requested_version="v3",
            requested_data=json.dumps({"foo": "bar"}),
            template_data_full=json.dumps({"foo": "bar"}),
            commit_sha="dummy sha",
            commit_pushed=False,
        )


async def test_get_change_throws_exception_when_not_found(change_repository: ChangeRepository):
    # WHEN
    with pytest.raises(ChangeNotFoundError):
        await change_repository.get_change(123)


async def test_get_latest_change_for_incarnation_succeeds(
    change_repository: ChangeRepository, incarnation: IncarnationInDB
):
    # GIVEN
    await change_repository.create_change(
        incarnation_id=incarnation.id,
        revision=1,
        change_type=ChangeType.DIRECT,
        commit_sha="dummy sha",
        commit_pushed=True,
        requested_version_hash="dummy template sha",
        requested_version="v1",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
    )
    await change_repository.create_change(
        incarnation_id=incarnation.id,
        revision=2,
        change_type=ChangeType.DIRECT,
        commit_sha="dummy sha2",
        commit_pushed=False,
        requested_version_hash="dummy template sha2",
        requested_version="v2",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
    )

    # WHEN
    change = await change_repository.get_latest_change_for_incarnation(incarnation.id)

    # THEN
    assert change.revision == 2


async def test_list_changes(change_repository: ChangeRepository, incarnation: IncarnationInDB):
    # GIVEN
    await change_repository.create_change(
        incarnation_id=incarnation.id,
        revision=1,
        change_type=ChangeType.DIRECT,
        commit_sha="dummy sha",
        commit_pushed=True,
        requested_version_hash="dummy template sha",
        requested_version="v1",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
    )
    await change_repository.create_change(
        incarnation_id=incarnation.id,
        revision=2,
        change_type=ChangeType.DIRECT,
        commit_sha="dummy sha2",
        commit_pushed=False,
        requested_version_hash="dummy template sha2",
        requested_version="v2",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
    )

    # WHEN
    changes = [x for x in await change_repository.list_changes(incarnation.id)]

    # THEN
    assert len(changes) == 2
    assert changes[0].revision == 2
    assert changes[1].revision == 1


async def test_get_change_by_revision(change_repository: ChangeRepository, incarnation: IncarnationInDB):
    # GIVEN
    await change_repository.create_change(
        incarnation_id=incarnation.id,
        revision=1,
        change_type=ChangeType.DIRECT,
        commit_sha="dummy sha",
        commit_pushed=True,
        requested_version_hash="dummy template sha",
        requested_version="v1",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
    )

    # WHEN
    change = await change_repository.get_change_by_revision(incarnation.id, 1)

    # THEN
    assert change.incarnation_id == incarnation.id
    assert change.revision == 1


async def test_get_latest_change_for_incarnation_throws_exception_when_no_change_exists(
    change_repository: ChangeRepository, incarnation: IncarnationInDB
):
    # WHEN
    with pytest.raises(IncarnationHasNoChangesError):
        await change_repository.get_latest_change_for_incarnation(incarnation.id)


async def test_list_incarnations_with_change_summary_returns_all_incarnations_with_latest_change_data(
    change_repository: ChangeRepository, user: User
):
    # GIVEN
    incarnation1_change1 = await change_repository.create_incarnation_with_first_change(
        incarnation_repository="test",
        target_directory="test",
        template_repository="test-template",
        commit_sha="dummy sha",
        requested_version_hash="dummy template sha",
        requested_version="v1",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
        owner_id=user.id,
    )
    incarnation1_change2 = await change_repository.create_change(
        incarnation_id=incarnation1_change1.id,
        revision=2,
        change_type=ChangeType.MERGE_REQUEST,
        commit_sha="dummy sha2",
        commit_pushed=True,
        requested_version_hash="dummy template sha2",
        requested_version="v2",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
        merge_request_id="123",
        merge_request_branch_name="mybranch",
    )

    incarnation2_change1 = await change_repository.create_incarnation_with_first_change(
        incarnation_repository="test2",
        target_directory="test",
        template_repository="test-template",
        commit_sha="dummy sha",
        requested_version_hash="dummy template sha",
        requested_version="v1",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
        owner_id=user.id,
    )

    # WHEN
    incarnations = [x async for x in change_repository.list_incarnations_with_changes_summary()]

    # THEN
    assert len(incarnations) == 2
    assert incarnations[0].id == incarnation1_change1.incarnation_id
    assert incarnations[0].revision == 2
    assert incarnations[0].commit_sha == incarnation1_change2.commit_sha
    assert incarnations[0].requested_version == incarnation1_change2.requested_version
    assert incarnations[0].type == incarnation1_change2.type
    assert incarnations[0].merge_request_id == incarnation1_change2.merge_request_id

    assert incarnations[1].id == incarnation2_change1.incarnation_id
    assert incarnations[1].revision == 1
    assert incarnations[1].type == incarnation2_change1.type
    assert incarnations[1].commit_sha == incarnation2_change1.commit_sha


async def test_update_change_commit_pushed_succeeds(change_repository: ChangeRepository, incarnation: IncarnationInDB):
    # GIVEN
    change = await change_repository.create_change(
        incarnation_id=incarnation.id,
        revision=1,
        change_type=ChangeType.DIRECT,
        commit_sha="dummy sha",
        commit_pushed=False,
        requested_version_hash="dummy template sha",
        requested_version="v1",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
    )

    # WHEN
    await change_repository.update_commit_pushed(change.id, True)

    # THEN
    updated_change = await change_repository.get_change(change.id)
    assert updated_change.commit_pushed is True


async def test_update_change_commit_sha_succeeds(change_repository: ChangeRepository, incarnation: IncarnationInDB):
    # GIVEN
    change = await change_repository.create_change(
        incarnation_id=incarnation.id,
        revision=1,
        change_type=ChangeType.DIRECT,
        commit_sha="dummy sha",
        commit_pushed=False,
        requested_version_hash="dummy template sha",
        requested_version="v1",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
    )

    # WHEN
    await change_repository.update_commit_sha(change.id, "new sha")

    # THEN
    updated_change = await change_repository.get_change(change.id)
    assert updated_change.commit_sha == "new sha"


async def test_update_change_commit_sha_fails_when_commit_is_already_pushed(
    change_repository: ChangeRepository, incarnation: IncarnationInDB
):
    # GIVEN
    change = await change_repository.create_change(
        incarnation_id=incarnation.id,
        revision=1,
        change_type=ChangeType.DIRECT,
        commit_sha="dummy sha",
        commit_pushed=True,
        requested_version_hash="dummy template sha",
        requested_version="v1",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
    )

    # WHEN
    with pytest.raises(ChangeCommitAlreadyPushedError):
        await change_repository.update_commit_sha(change.id, "new sha")


async def test_delete_change_succeeds_in_deleting(change_repository: ChangeRepository, incarnation: IncarnationInDB):
    # GIVEN
    change = await change_repository.create_change(
        incarnation_id=incarnation.id,
        revision=1,
        change_type=ChangeType.DIRECT,
        commit_sha="dummy sha",
        commit_pushed=False,
        requested_version_hash="dummy template sha",
        requested_version="v1",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
    )

    # WHEN
    await change_repository.delete_change(change.id)

    # THEN
    with pytest.raises(ChangeNotFoundError):
        await change_repository.get_change(change.id)


async def test_delete_change_raises_exception_when_not_found(change_repository: ChangeRepository):
    # WHEN
    with pytest.raises(ChangeNotFoundError):
        await change_repository.delete_change(123)


async def test_create_incarnation_with_first_change(change_repository: ChangeRepository, user: User):
    # WHEN
    change = await change_repository.create_incarnation_with_first_change(
        incarnation_repository="incarnation",
        target_directory=".",
        template_repository="template",
        commit_sha="commit_sha",
        requested_version_hash="dummy template sha",
        requested_version="v1",
        requested_data=json.dumps({"foo": "bar"}),
        owner_id=user.id,
        template_data_full=json.dumps({"foo": "bar"}),
    )

    # THEN
    assert change.id is not None
    assert change.incarnation_id is not None
    assert change.type == ChangeType.DIRECT
    assert change.revision == 1
    assert change.requested_version == "v1"
    assert json.loads(change.requested_data) == {"foo": "bar"}
    assert json.loads(change.template_data_full) == {"foo": "bar"}
    assert change.commit_sha == "commit_sha"
    assert change.commit_pushed is False


async def test_delete_incarnation_also_deletes_associated_changes(change_repository: ChangeRepository, user: User):
    # GIVEN
    change = await change_repository.create_incarnation_with_first_change(
        incarnation_repository="incarnation",
        target_directory=".",
        template_repository="template",
        commit_sha="commit_sha",
        requested_version_hash="dummy template sha",
        requested_version="v1",
        requested_data=json.dumps({"foo": "bar"}),
        template_data_full=json.dumps({"foo": "bar"}),
        owner_id=user.id,
    )
    incarnation_id = change.incarnation_id

    # WHEN
    await change_repository.delete_incarnation(incarnation_id)

    # THEN
    with pytest.raises(ChangeNotFoundError):
        await change_repository.get_change(change.id)

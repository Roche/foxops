import json

import pytest
from pytest import fixture

from foxops.database import DAL
from foxops.database.repositories.change import (
    ChangeConflictError,
    ChangeNotFoundError,
    ChangeRepository,
    ChangeType,
    IncarnationHasNoChangesError,
)
from foxops.models import DesiredIncarnationState, Incarnation


@fixture(scope="function")
async def incarnation(dal: DAL) -> Incarnation:
    return await dal.create_incarnation(
        desired_incarnation_state=DesiredIncarnationState(
            incarnation_repository="test",
            target_directory="test",
            template_repository="test",
            template_repository_version="test",
            template_data={},
        ),
        commit_sha="dummy sha",
        merge_request_id=None,
    )


async def test_create_change_persists_all_data(change_repository: ChangeRepository, incarnation: Incarnation):
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
        merge_request_id="123",
        merge_request_branch_name="mybranch",
    )

    assert change.id is not None
    assert change.type == ChangeType.DIRECT


async def test_create_change_rejects_double_revision(change_repository: ChangeRepository, incarnation: Incarnation):
    # GIVEN
    await change_repository.create_change(
        incarnation_id=incarnation.id,
        revision=1,
        change_type=ChangeType.DIRECT,
        requested_version_hash="dummy template sha",
        requested_version="v2",
        requested_data=json.dumps({"foo": "bar"}),
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
            commit_sha="dummy sha",
            commit_pushed=False,
        )


async def test_get_change_throws_exception_when_not_found(change_repository: ChangeRepository):
    # WHEN
    with pytest.raises(ChangeNotFoundError):
        await change_repository.get_change(123)


async def test_get_latest_change_for_incarnation_succeeds(
    change_repository: ChangeRepository, incarnation: Incarnation
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
    )

    # WHEN
    change = await change_repository.get_latest_change_for_incarnation(incarnation.id)

    # THEN
    assert change.revision == 2


async def test_get_latest_change_for_incarnation_throws_exception_when_no_change_exists(
    change_repository: ChangeRepository, incarnation: Incarnation
):
    # WHEN
    with pytest.raises(IncarnationHasNoChangesError):
        await change_repository.get_latest_change_for_incarnation(incarnation.id)


async def test_update_change_commit_pushed_succeeds(change_repository: ChangeRepository, incarnation: Incarnation):
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
    )

    # WHEN
    await change_repository.update_commit_pushed(change.id, True)

    # THEN
    updated_change = await change_repository.get_change(change.id)
    assert updated_change.commit_pushed is True


async def test_delete_change_succeeds_in_deleting(change_repository: ChangeRepository, incarnation: Incarnation):
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


async def test_create_incarnation_with_first_change(change_repository: ChangeRepository):
    # WHEN
    change = await change_repository.create_incarnation_with_first_change(
        incarnation_repository="incarnation",
        target_directory=".",
        commit_sha="commit_sha",
        requested_version_hash="dummy template sha",
        requested_version="v1",
        requested_data=json.dumps({"foo": "bar"}),
    )

    # THEN
    assert change.id is not None
    assert change.incarnation_id is not None
    assert change.type == ChangeType.DIRECT
    assert change.revision == 1
    assert change.requested_version == "v1"
    assert json.loads(change.requested_data) == {"foo": "bar"}
    assert change.commit_sha == "commit_sha"
    assert change.commit_pushed is False


async def test_delete_incarnation_also_deletes_associated_changes(change_repository: ChangeRepository):
    # GIVEN
    change = await change_repository.create_incarnation_with_first_change(
        incarnation_repository="incarnation",
        target_directory=".",
        commit_sha="commit_sha",
        requested_version_hash="dummy template sha",
        requested_version="v1",
        requested_data=json.dumps({"foo": "bar"}),
    )
    incarnation_id = change.incarnation_id

    # WHEN
    await change_repository.delete_incarnation(incarnation_id)

    # THEN
    with pytest.raises(ChangeNotFoundError):
        await change_repository.get_change(change.id)
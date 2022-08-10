import pytest
from sqlalchemy import text

from foxops.database import DAL
from foxops.models import Incarnation
from foxops.models.desired_incarnation_state import DesiredIncarnationState


@pytest.mark.asyncio
async def test_get_incarnations_returns_empty_list_for_empty_incarnation_inventory(
    dal: DAL,
):
    # WHEN
    actual_incarnations = [i async for i in dal.get_incarnations()]

    # THEN
    assert actual_incarnations == []


@pytest.mark.asyncio
async def test_create_incarnation_should_add_new_incarnation_to_incarnation_inventory(
    dal: DAL,
):
    # GIVEN
    new_incarnation = DesiredIncarnationState(
        incarnation_repository="test",
        target_directory="test",
        template_repository="test",
        template_repository_version="test",
        template_data={},
    )

    # WHEN
    await dal.create_incarnation(new_incarnation, commit_sha="commit_sha", merge_request_id="merge_request_id")

    # THEN
    async with dal.connection() as conn:
        actual_incarnations = await conn.execute(text("SELECT 1 FROM incarnation"))
    assert actual_incarnations.scalar_one() == 1


@pytest.mark.asyncio
async def test_get_incarnations_returns_items_in_incarnation_inventory(dal: DAL):
    # GIVEN
    async with dal.connection() as conn:
        await conn.execute(text("INSERT INTO incarnation VALUES (1, 'test', 'test', 'commit_sha', 'merge_request_id')"))
        await conn.commit()

    # WHEN
    actual_incarnations = [i async for i in dal.get_incarnations()]

    # THEN
    assert actual_incarnations == [
        Incarnation(
            id=1,
            incarnation_repository="test",
            target_directory="test",
            commit_sha="commit_sha",
            merge_request_id="merge_request_id",
        )
    ]


@pytest.mark.asyncio
async def test_get_incarnation_in_incarnation_inventory(dal: DAL):
    # GIVEN
    async with dal.connection() as conn:
        await conn.execute(text("INSERT INTO incarnation VALUES (1, 'test', 'test', 'commit_sha', 'merge_request_id')"))
        await conn.commit()

    # WHEN
    incarnation = await dal.get_incarnation(1)

    # THEN
    assert incarnation == Incarnation(
        id=1,
        incarnation_repository="test",
        target_directory="test",
        commit_sha="commit_sha",
        merge_request_id="merge_request_id",
    )


@pytest.mark.asyncio
async def test_update_incarnation_in_inventory(dal: DAL):
    # GIVEN
    async with dal.connection() as conn:
        await conn.execute(text("INSERT INTO incarnation VALUES (1, 'test', 'test', 'commit_sha', 'merge_request_id')"))
        await conn.commit()

    # WHEN
    updated_incarnation = await dal.update_incarnation(1, "new_commit_sha", "new_merge_request_id")

    # THEN
    assert updated_incarnation == Incarnation(
        id=1,
        incarnation_repository="test",
        target_directory="test",
        commit_sha="new_commit_sha",
        merge_request_id="new_merge_request_id",
    )


@pytest.mark.asyncio
async def test_delete_incarnation_from_inventory(dal: DAL):
    # GIVEN
    async with dal.connection() as conn:
        await conn.execute(text("INSERT INTO incarnation VALUES (1, 'test', 'test', 'commit_sha', 'merge_request_id')"))
        await conn.commit()

    # WHEN
    await dal.delete_incarnation(id=1)

    # THEN
    async with dal.connection() as conn:
        actual_incarnations = await conn.execute(text("SELECT * FROM incarnation"))

    assert actual_incarnations.scalar_one_or_none() is None

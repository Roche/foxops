from pathlib import Path

import pytest
from pytest import fixture
from sqlalchemy.ext.asyncio import AsyncEngine

from foxops import reconciliation
from foxops.database import DAL
from foxops.database.repositories.change import ChangeRepository
from foxops.hosters.local import LocalHoster
from foxops.models import DesiredIncarnationState, DesiredIncarnationStatePatch
from foxops.models.change import ChangeWithDirectCommit
from foxops.reconciliation import initialize_incarnation
from foxops.services.change import ChangeFailed, ChangeService


@fixture(scope="function")
async def incarnation_repository(test_async_engine: AsyncEngine) -> DAL:
    dal = DAL(test_async_engine)
    await dal.initialize_db()

    return dal


@fixture(scope="function")
def local_hoster(tmp_path) -> LocalHoster:
    return LocalHoster(Path(tmp_path))


@fixture(scope="function")
async def git_repo_template(local_hoster: LocalHoster) -> str:
    repo_name = "template"
    await local_hoster.create_repository(repo_name)

    async with local_hoster.cloned_repository(repo_name) as repo:
        (repo.directory / "README.md").write_text("Hello, world!")
        await repo.commit_all("Initial commit")
        await repo.tag("v1.0.0")

        (repo.directory / "README.md").write_text("Hello, world2!")
        await repo.commit_all("update")
        await repo.tag("v1.1.0")

        await repo.push(tags=True)

    return repo_name


@fixture(scope="function")
async def initialized_legacy_incarnation_id(
    local_hoster: LocalHoster, incarnation_repository: DAL, git_repo_template: str
) -> int:
    repo_name = "incarnation_initialized"
    await local_hoster.create_repository(repo_name)

    desired_incarnation_state = DesiredIncarnationState(
        incarnation_repository=repo_name,
        target_directory=".",
        template_repository=git_repo_template,
        template_repository_version="v1.0.0",
        template_data={},
        automerge=True,
    )
    commit_sha, merge_request_id = await initialize_incarnation(local_hoster, desired_incarnation_state)
    incarnation = await incarnation_repository.create_incarnation(
        desired_incarnation_state, commit_sha, merge_request_id
    )

    return incarnation.id


@fixture(scope="function")
async def change_service(
    test_async_engine: AsyncEngine, incarnation_repository: DAL, local_hoster: LocalHoster
) -> ChangeService:
    change_repository = ChangeRepository(test_async_engine)

    return ChangeService(
        hoster=local_hoster,
        incarnation_repository=incarnation_repository,
        change_repository=change_repository,
    )


async def test_initialize_legacy_incarnation(change_service: ChangeService, initialized_legacy_incarnation_id: int):
    # WHEN
    change = await change_service.initialize_legacy_incarnation(initialized_legacy_incarnation_id)

    # THEN
    assert isinstance(change, ChangeWithDirectCommit)
    assert change.revision == 1
    assert change.incarnation_id == initialized_legacy_incarnation_id
    assert change.commit_sha is not None


async def test_initialize_legacy_incarnation_fails_if_already_initialized(
    change_service: ChangeService, initialized_legacy_incarnation_id: int
):
    # GIVEN
    await change_service.initialize_legacy_incarnation(initialized_legacy_incarnation_id)

    # WHEN
    with pytest.raises(ChangeFailed, match="already initialized"):
        await change_service.initialize_legacy_incarnation(initialized_legacy_incarnation_id)


async def test_initialize_legacy_incarnation_fails_if_incarnation_has_incomplete_update(
    change_service: ChangeService, initialized_legacy_incarnation_id: int
):
    # GIVEN
    incarnation = await change_service._incarnation_repository.get_incarnation(initialized_legacy_incarnation_id)
    update = await reconciliation.update_incarnation(
        change_service._hoster,
        incarnation,
        DesiredIncarnationStatePatch(
            template_repository_version="v1.1.0",
            template_data={},
            automerge=False,
        ),
    )

    if update is not None:
        incarnation = await change_service._incarnation_repository.update_incarnation(
            incarnation.id, commit_sha=update[0], merge_request_id=update[1]
        )
    assert incarnation.merge_request_id is not None

    # WHEN
    with pytest.raises(ChangeFailed, match="pending merge request"):
        await change_service.initialize_legacy_incarnation(initialized_legacy_incarnation_id)


async def test_create_change_direct(change_service: ChangeService, initialized_legacy_incarnation_id: int):
    # GIVEN
    await change_service.initialize_legacy_incarnation(initialized_legacy_incarnation_id)

    # WHEN
    change = await change_service.create_change_direct(initialized_legacy_incarnation_id, requested_version="v1.1.0")

    # THEN
    assert change.incarnation_id == initialized_legacy_incarnation_id
    assert change.revision == 2
    assert change.commit_sha is not None
    assert change.requested_version == "v1.1.0"

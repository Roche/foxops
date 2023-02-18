import inspect
from pathlib import Path

import pytest
from pytest import fixture
from sqlalchemy.ext.asyncio import AsyncEngine

from foxops import reconciliation
from foxops.database import DAL
from foxops.database.repositories.change import ChangeRepository
from foxops.engine import load_incarnation_state
from foxops.hosters.local import LocalHoster
from foxops.models import (
    DesiredIncarnationState,
    DesiredIncarnationStatePatch,
    Incarnation,
)
from foxops.models.change import Change
from foxops.reconciliation import initialize_incarnation
from foxops.services.change import (
    ChangeFailed,
    ChangeService,
    IncarnationAlreadyExists,
    _construct_merge_request_conflict_description,
)


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
        (repo.directory / "template").mkdir()
        (repo.directory / "template" / "README.md").write_text("Hello, world!")
        await repo.commit_all("Initial commit")
        await repo.tag("v1.0.0")

        (repo.directory / "template" / "README.md").write_text("Hello, world2!")
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
async def initialized_incarnation(
    local_hoster: LocalHoster, git_repo_template: str, change_service: ChangeService
) -> Incarnation:
    repo_name = "incarnation_initialized"
    await local_hoster.create_repository(repo_name)

    change = await change_service.create_incarnation(
        incarnation_repository=repo_name,
        template_repository=git_repo_template,
        template_repository_version="v1.0.0",
        template_data={},
    )

    return Incarnation(
        id=change.incarnation_id,
        incarnation_repository=repo_name,
        target_directory=".",
        commit_sha="dummy",
    )


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


async def test_create_incarnation_succeeds_when_creating_incarnation_in_root_folder(
    change_service: ChangeService, git_repo_template: str, local_hoster: LocalHoster
):
    # GIVEN
    incarnation_repo_name = "incarnation"
    await local_hoster.create_repository(incarnation_repo_name)

    # WHEN
    change = await change_service.create_incarnation(
        incarnation_repository=incarnation_repo_name,
        target_directory=".",
        template_repository=git_repo_template,
        template_repository_version="v1.0.0",
        template_data={},
    )

    # THEN
    assert change.incarnation_id is not None
    assert change.requested_version == "v1.0.0"
    assert change.commit_sha is not None

    async with local_hoster.cloned_repository(incarnation_repo_name) as repo:
        assert (repo.directory / "README.md").read_text() == "Hello, world!"
        assert await repo.head() == change.commit_sha


async def test_create_incarnation_succeeds_when_creating_incarnation_in_subfolder(
    change_service: ChangeService, git_repo_template: str, local_hoster: LocalHoster
):
    # GIVEN
    incarnation_repo_name = "incarnation"
    await local_hoster.create_repository(incarnation_repo_name)

    # WHEN
    change = await change_service.create_incarnation(
        incarnation_repository=incarnation_repo_name,
        target_directory="subdir",
        template_repository=git_repo_template,
        template_repository_version="v1.0.0",
        template_data={},
    )

    # THEN
    assert change.incarnation_id is not None
    assert change.requested_version == "v1.0.0"
    assert change.commit_sha is not None

    async with local_hoster.cloned_repository(incarnation_repo_name) as repo:
        assert (repo.directory / "subdir" / "README.md").read_text() == "Hello, world!"
        assert await repo.head() == change.commit_sha


async def test_create_incarnation_fails_if_there_is_already_one_at_the_target(
    change_service: ChangeService, git_repo_template: str, local_hoster: LocalHoster
):
    # GIVEN
    incarnation_repo_name = "incarnation"
    await local_hoster.create_repository(incarnation_repo_name)
    await change_service.create_incarnation(
        incarnation_repository=incarnation_repo_name,
        template_repository=git_repo_template,
        template_repository_version="v1.0.0",
        template_data={},
    )

    # THEN
    with pytest.raises(IncarnationAlreadyExists):
        await change_service.create_incarnation(
            incarnation_repository=incarnation_repo_name,
            template_repository=git_repo_template,
            template_repository_version="v1.1.0",
            template_data={},
        )


async def test_initialize_legacy_incarnation_succeeds_when_given_a_legacy_incarnation(
    change_service: ChangeService, initialized_legacy_incarnation_id: int
):
    # WHEN
    change = await change_service.initialize_legacy_incarnation(initialized_legacy_incarnation_id)

    # THEN
    assert isinstance(change, Change)
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


async def test_create_change_direct_succeeds_when_updating_the_template_version(
    change_service: ChangeService, incarnation_repository: DAL, initialized_incarnation: Incarnation
):
    # WHEN
    change = await change_service.create_change_direct(initialized_incarnation.id, requested_version="v1.1.0")

    # THEN
    assert change.incarnation_id == initialized_incarnation.id
    assert change.revision == 2
    assert change.commit_sha is not None
    assert change.requested_version == "v1.1.0"

    async with change_service._hoster.cloned_repository(initialized_incarnation.incarnation_repository) as repo:
        assert (repo.directory / "README.md").read_text() == "Hello, world2!"

        incarnation_state = load_incarnation_state(repo.directory / ".fengine.yaml")
        assert incarnation_state.template_repository_version == "v1.1.0"


async def test_construct_merge_request_conflict_description_with_conflicts():
    # GIVEN
    conflict_files = [Path("README.md")]

    # WHEN
    description = _construct_merge_request_conflict_description(conflict_files, None)

    # THEN
    assert description == inspect.cleandoc(
        """
    Foxops couldn't automatically apply the changes from the template in this incarnation

    The following files were updated in the template repository - and at the same time - also
    **modified** in the incarnation repository. Please resolve the conflicts manually:

    - README.md
    """
    )


async def test_construct_merge_request_conflict_description_with_conflicts_and_deletions():
    # GIVEN
    conflict_files = [Path("README.md")]
    deleted_files = [Path("CONTRIBUTING.md")]

    # WHEN
    description = _construct_merge_request_conflict_description(conflict_files, deleted_files)

    # THEN
    assert description == inspect.cleandoc(
        """
    Foxops couldn't automatically apply the changes from the template in this incarnation

    The following files were updated in the template repository - and at the same time - also
    **modified** in the incarnation repository. Please resolve the conflicts manually:

    - README.md

    The following files were updated in the template repository but are **no longer
    present** in this incarnation repository. Please resolve the conflicts manually:

    - CONTRIBUTING.md
    """
    )

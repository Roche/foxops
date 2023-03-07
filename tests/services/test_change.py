import inspect
from pathlib import Path

import pytest
from pytest import fixture
from sqlalchemy.ext.asyncio import AsyncEngine

from foxops import reconciliation
from foxops.database import DAL
from foxops.database.repositories.change import ChangeRepository
from foxops.engine import load_incarnation_state
from foxops.errors import IncarnationNotFoundError
from foxops.hosters import ReconciliationStatus
from foxops.hosters.local import LocalHoster
from foxops.hosters.types import MergeRequestStatus
from foxops.models import (
    DesiredIncarnationState,
    DesiredIncarnationStatePatch,
    Incarnation,
)
from foxops.models.change import Change, ChangeWithMergeRequest
from foxops.reconciliation import initialize_incarnation
from foxops.services.change import (
    ChangeFailed,
    ChangeRejectedDueToNoChanges,
    ChangeService,
    IncarnationAlreadyExists,
    IncarnationAlreadyUpgraded,
    _construct_merge_request_conflict_description,
    delete_all_files_in_local_git_repository,
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

        (repo.directory / "template" / "README.md").write_text("Hello, world3!")
        await repo.commit_all("update")
        await repo.tag("v1.2.0")

        await repo.push(tags=True)

    return repo_name


@fixture(scope="function")
async def initialized_legacy_incarnation_id(
    local_hoster: LocalHoster, incarnation_repository: DAL, git_repo_template: str
) -> int:
    repo_name = "incarnation_initialized_legacy"
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
        template_repository=git_repo_template,
        commit_sha="dummy",
    )


@fixture(scope="function")
async def initialized_incarnation_with_customizations(
    local_hoster: LocalHoster, initialized_incarnation: Incarnation
) -> Incarnation:
    async with local_hoster.cloned_repository(initialized_incarnation.incarnation_repository) as repo:
        (repo.directory / "README.md").write_text("Hello, world customized!")
        (repo.directory / "CONTRIBUTING.md").write_text("more files with content")
        await repo.commit_all("some customizations")
        await repo.push()

    return initialized_incarnation


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
    with pytest.raises(IncarnationAlreadyUpgraded):
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


async def test_create_change_direct_succeeds_when_updating_to_the_same_branch_name(
    change_service: ChangeService,
    incarnation_repository: DAL,
    local_hoster: LocalHoster,
    initialized_incarnation: Incarnation,
    git_repo_template: str,
):
    # GIVEN
    initial_change = await change_service.create_change_direct(initialized_incarnation.id, requested_version="main")
    async with local_hoster.cloned_repository(git_repo_template) as repo:
        (repo.directory / "template" / "README.md").write_text("Hello, world - even more!")
        await repo.commit_all("update2")
        await repo.push()

    # WHEN
    new_change = await change_service.create_change_direct(initialized_incarnation.id)

    # THEN
    assert new_change.revision > initial_change.revision
    assert new_change.commit_sha != initial_change.commit_sha
    assert new_change.requested_version == "main"

    async with change_service._hoster.cloned_repository(initialized_incarnation.incarnation_repository) as repo:
        assert (repo.directory / "README.md").read_text() == "Hello, world - even more!"

        incarnation_state = load_incarnation_state(repo.directory / ".fengine.yaml")
        assert incarnation_state.template_repository_version == "main"


async def test_create_change_direct_succeeds_when_the_previous_change_was_not_merged(
    change_service: ChangeService,
    initialized_incarnation: Incarnation,
    local_hoster: LocalHoster,
):
    # GIVEN
    unmerged_change = await change_service.create_change_merge_request(
        incarnation_id=initialized_incarnation.id,
        requested_version="v1.1.0",
        automerge=False,
    )
    async with local_hoster.cloned_repository(initialized_incarnation.incarnation_repository) as repo:
        previous_commit_sha = await repo.head()

    # WHEN
    local_hoster.close_merge_request(initialized_incarnation.incarnation_repository, unmerged_change.merge_request_id)
    change = await change_service.create_change_direct(initialized_incarnation.id, requested_version="v1.2.0")

    # THEN
    assert change.commit_sha != previous_commit_sha


async def test_create_change_merge_request_succeeds_when_updating_the_template_version_without_automerge(
    change_service: ChangeService, incarnation_repository: DAL, initialized_incarnation: Incarnation
):
    # WHEN
    change = await change_service.create_change_merge_request(
        initialized_incarnation.id, requested_version="v1.1.0", automerge=False
    )

    # THEN
    assert change.incarnation_id == initialized_incarnation.id
    assert change.revision == 2
    assert change.commit_sha is not None
    assert change.requested_version == "v1.1.0"
    assert change.merge_request_id is not None
    assert change.merge_request_status == MergeRequestStatus.OPEN

    async with change_service._hoster.cloned_repository(
        initialized_incarnation.incarnation_repository, refspec=change.merge_request_branch_name
    ) as repo:
        assert (repo.directory / "README.md").read_text() == "Hello, world2!"

        incarnation_state = load_incarnation_state(repo.directory / ".fengine.yaml")
        assert incarnation_state.template_repository_version == "v1.1.0"


async def test_create_change_merge_request_succeeds_when_updating_the_template_version_with_automerge(
    change_service: ChangeService, incarnation_repository: DAL, initialized_incarnation: Incarnation
):
    # WHEN
    change = await change_service.create_change_merge_request(
        initialized_incarnation.id, requested_version="v1.1.0", automerge=True
    )

    # THEN
    assert change.incarnation_id == initialized_incarnation.id
    assert change.revision == 2
    assert change.commit_sha is not None
    assert change.requested_version == "v1.1.0"
    assert change.merge_request_id is not None
    assert change.merge_request_status == MergeRequestStatus.MERGED

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


async def test_get_incarnation_with_details_succeeds_for_legacy_incarnation(
    change_service: ChangeService, initialized_legacy_incarnation_id: int
):
    # WHEN
    incarnation = await change_service.get_incarnation_with_details(initialized_legacy_incarnation_id)

    # THEN
    assert incarnation.id == initialized_legacy_incarnation_id
    assert incarnation.incarnation_repository == "incarnation_initialized_legacy"
    assert incarnation.target_directory == "."
    assert incarnation.commit_sha is not None
    assert incarnation.commit_url.endswith(incarnation.commit_sha)
    assert incarnation.merge_request_id is None
    assert incarnation.merge_request_url is None
    assert incarnation.merge_request_status is None
    assert incarnation.status == ReconciliationStatus.SUCCESS
    assert incarnation.template_repository == "template"
    assert incarnation.template_repository_version == "v1.0.0"
    assert incarnation.template_data == {}


async def test_reset_incarnation_returns_change_and_does_not_modify_main_branch(
    local_hoster: LocalHoster, change_service: ChangeService, initialized_incarnation_with_customizations: Incarnation
):
    # WHEN
    change = await change_service.reset_incarnation(initialized_incarnation_with_customizations.id)

    # THEN
    assert change.merge_request_status == MergeRequestStatus.OPEN
    assert change.id > 1
    assert change.requested_version == "v1.0.0"

    async with change_service._hoster.cloned_repository(
        initialized_incarnation_with_customizations.incarnation_repository
    ) as repo:
        assert (repo.directory / "README.md").read_text() == "Hello, world customized!"
        assert (repo.directory / "CONTRIBUTING.md").read_text() == "more files with content"


async def test_reset_incarnation_succeeds_and_removes_customizations_on_merge_request_branch(
    local_hoster: LocalHoster, change_service: ChangeService, initialized_incarnation_with_customizations: Incarnation
):
    # WHEN
    change = await change_service.reset_incarnation(initialized_incarnation_with_customizations.id)

    # THEN
    assert change.revision > 1
    assert isinstance(change, ChangeWithMergeRequest)

    async with change_service._hoster.cloned_repository(
        initialized_incarnation_with_customizations.incarnation_repository,
        refspec=change.merge_request_branch_name,
    ) as repo:
        assert (repo.directory / "README.md").read_text() == "Hello, world!"
        assert not (repo.directory / "CONTRIBUTING.md").exists()


async def test_reset_incarnation_succeeds_when_overriding_version_and_data(
    local_hoster: LocalHoster, change_service: ChangeService, initialized_incarnation_with_customizations: Incarnation
):
    # WHEN
    change = await change_service.reset_incarnation(
        initialized_incarnation_with_customizations.id, override_version="v1.1.0", override_data={"foo": "bar"}
    )

    # THEN
    merge_request = local_hoster.get_merge_request(
        initialized_incarnation_with_customizations.incarnation_repository, change.merge_request_id
    )

    async with change_service._hoster.cloned_repository(
        initialized_incarnation_with_customizations.incarnation_repository,
        refspec=merge_request.source_branch,
    ) as repo:
        assert (repo.directory / "README.md").read_text() == "Hello, world2!"
        assert not (repo.directory / "CONTRIBUTING.md").exists()

        incarnation_state = load_incarnation_state(repo.directory / ".fengine.yaml")
        assert incarnation_state.template_repository_version == "v1.1.0"
        assert incarnation_state.template_data == {"foo": "bar"}


async def test_reset_incarnation_fails_when_no_customizations_were_made(
    change_service: ChangeService, initialized_incarnation: Incarnation
):
    # THEN
    with pytest.raises(ChangeRejectedDueToNoChanges):
        await change_service.reset_incarnation(initialized_incarnation.id)


async def test_reset_incarnation_fails_when_incarnation_does_not_exist(change_service: ChangeService):
    # WHEN
    with pytest.raises(IncarnationNotFoundError):
        await change_service.reset_incarnation(123456789)


def test_delete_all_files_in_local_git_repository_removes_hidden_directories_and_files(tmp_path):
    # GIVEN
    (tmp_path / ".dummy_folder").mkdir()
    (tmp_path / "dummy_folder2").mkdir()
    (tmp_path / "dummy_folder2" / ".myfile").write_text("Hello, world!")
    (tmp_path / ".config").write_text("Hello, world!")

    # WHEN
    delete_all_files_in_local_git_repository(tmp_path)

    # THEN
    assert not (tmp_path / ".dummy_folder").exists()
    assert not (tmp_path / "dummy_folder2" / ".myfile").exists()
    assert not (tmp_path / ".config").exists()


def test_delete_all_files_in_local_git_repository_does_not_delete_git_directory_in_root_folder(tmp_path):
    # GIVEN
    (tmp_path / ".git").mkdir()
    (tmp_path / "subfolder").mkdir()
    (tmp_path / "subfolder" / ".git").mkdir()
    (tmp_path / "README.md").write_text("Hello, world!")

    # WHEN
    delete_all_files_in_local_git_repository(tmp_path)

    # THEN
    assert (tmp_path / ".git").exists()
    assert not (tmp_path / "subfolder" / ".git").exists()
    assert not (tmp_path / "README.md").exists()

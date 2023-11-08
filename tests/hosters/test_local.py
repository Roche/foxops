from pathlib import Path

import pytest
from pytest import fixture

from foxops.engine import IncarnationState
from foxops.hosters.local import LocalHoster
from foxops.hosters.types import MergeRequestStatus


@fixture(scope="function")
def local_hoster(tmp_path: Path) -> LocalHoster:
    return LocalHoster(tmp_path)


async def test_create_repository(local_hoster):
    # GIVEN
    repo_name = "test-repository"

    # WHEN
    await local_hoster.create_repository(repo_name)

    # THEN
    async with local_hoster.cloned_repository(repo_name) as repo:
        assert not await repo.has_any_commits()


async def test_cloned_repository_checks_out_refspec_when_given_one(local_hoster):
    # GIVEN
    repo_name = "test-repository"
    await local_hoster.create_repository(repo_name)
    async with local_hoster.cloned_repository(repo_name) as repo:
        (repo.directory / "README.md").write_text("Hello, world!")
        await repo.commit_all("Initial commit")
        await repo.push()

        await repo.create_and_checkout_branch("feature")
        (repo.directory / "README.md").write_text("Hello, world2!")
        await repo.commit_all("update")
        await repo.push()

    # WHEN
    async with local_hoster.cloned_repository(repo_name, refspec="main") as repo:
        assert (repo.directory / "README.md").read_text() == "Hello, world!"

    # THEN
    async with local_hoster.cloned_repository(repo_name, refspec="feature") as repo:
        assert (repo.directory / "README.md").read_text() == "Hello, world2!"


async def test_can_push_to_repository(local_hoster):
    # GIVEN
    repo_name = "test-repository"
    await local_hoster.create_repository(repo_name)

    # WHEN
    async with local_hoster.cloned_repository(repo_name) as repo:
        (repo.directory / "README.md").write_text("Hello, world!")
        await repo.commit_all("Initial commit")
        await repo.push()

    # THEN
    async with local_hoster.cloned_repository(repo_name) as repo:
        assert await repo.has_any_commits()
        assert (repo.directory / "README.md").read_text() == "Hello, world!"


async def test_does_commit_exist_returns_true_for_existing_commit(local_hoster):
    # GIVEN
    repo_name = "test-repository"
    await local_hoster.create_repository(repo_name)
    async with local_hoster.cloned_repository(repo_name) as repo:
        (repo.directory / "README.md").write_text("Hello, world!")
        await repo.commit_all("Initial commit")
        await repo.push()
        commit_sha = await repo.head()

    # WHEN
    exists = await local_hoster.does_commit_exist(repo_name, commit_sha)

    # THEN
    assert exists


async def test_does_commit_exist_returns_false_for_non_existing_commit(local_hoster):
    # GIVEN
    repo_name = "test-repository"
    await local_hoster.create_repository(repo_name)
    async with local_hoster.cloned_repository(repo_name) as repo:
        (repo.directory / "README.md").write_text("Hello, world!")
        await repo.commit_all("Initial commit")
        await repo.push()
        commit_sha = await repo.head()

    # WHEN
    exists = await local_hoster.does_commit_exist(repo_name, "a" * len(commit_sha))

    # THEN
    assert not exists


async def test_has_pending_incarnation_branch_returns_commit_id_for_existing_branch(local_hoster):
    # GIVEN
    repo_name = "test-repository"
    await local_hoster.create_repository(repo_name)
    async with local_hoster.cloned_repository(repo_name) as repo:
        (repo.directory / "README.md").write_text("Hello, world!")
        await repo.commit_all("Initial commit")
        await repo.push()
        commit_sha = await repo.head()

    # WHEN
    result = await local_hoster.has_pending_incarnation_branch(repo_name, "main")

    # THEN
    assert result == commit_sha


async def test_has_pending_incarnation_branch_returns_none_for_non_existing_branch(local_hoster):
    # GIVEN
    repo_name = "test-repository"
    await local_hoster.create_repository(repo_name)
    async with local_hoster.cloned_repository(repo_name) as repo:
        (repo.directory / "README.md").write_text("Hello, world!")
        await repo.commit_all("Initial commit")
        await repo.push()

    # WHEN
    result = await local_hoster.has_pending_incarnation_branch(repo_name, "dummy-branch")

    # THEN
    assert result is None


async def test_merge_request_returns_commit_id_of_source_branch(local_hoster):
    # GIVEN
    repo_name = "test-repository"
    change_branch = "dummy-branch"

    await local_hoster.create_repository(repo_name)
    async with local_hoster.cloned_repository(repo_name) as repo:
        (repo.directory / "README.md").write_text("Hello, world!")
        await repo.commit_all("Initial commit")
        await repo.push()

        await repo.create_and_checkout_branch(change_branch)
        (repo.directory / "README.md").write_text("Hello, world - modified!")
        await repo.commit_all("Modified README")
        await repo.push()

        commit_sha = await repo.head()

    # WHEN
    mr_commit_sha, mr_id = await local_hoster.merge_request(
        incarnation_repository=repo_name,
        source_branch=change_branch,
        title="Dummy title",
        description="Dummy description",
        with_automerge=False,
    )

    # THEN
    assert mr_commit_sha == commit_sha
    assert mr_id == "1"

    assert await local_hoster.get_merge_request_status(repo_name, mr_id) == MergeRequestStatus.OPEN


async def test_merge_request_supports_automerge(local_hoster):
    # GIVEN
    repo_name = "test-repository"
    change_branch = "dummy-branch"

    await local_hoster.create_repository(repo_name)
    async with local_hoster.cloned_repository(repo_name) as repo:
        (repo.directory / "README.md").write_text("Hello, world!")
        await repo.commit_all("Initial commit")
        await repo.push()

        await repo.create_and_checkout_branch(change_branch)
        (repo.directory / "README.md").write_text("Hello, world - modified!")
        await repo.commit_all("Modified README")
        await repo.push()

        commit_sha = await repo.head()

    # WHEN
    mr_commit_sha, mr_id = await local_hoster.merge_request(
        incarnation_repository=repo_name,
        source_branch=change_branch,
        title="Dummy title",
        description="Dummy description",
        with_automerge=True,
    )

    # THEN
    assert mr_commit_sha == commit_sha
    assert mr_id == "1"

    assert await local_hoster.get_merge_request_status(repo_name, mr_id) == MergeRequestStatus.MERGED
    async with local_hoster.cloned_repository(repo_name) as repo:
        assert (repo.directory / "README.md").read_text() == "Hello, world - modified!"
        assert await repo.head() == commit_sha


async def test_merge_request_fails_if_source_branch_does_not_exist(local_hoster):
    # GIVEN
    repo_name = "test-repository"

    await local_hoster.create_repository(repo_name)
    async with local_hoster.cloned_repository(repo_name) as repo:
        (repo.directory / "README.md").write_text("Hello, world!")
        await repo.commit_all("Initial commit")
        await repo.push()

    # THEN
    with pytest.raises(ValueError, match="does not exist"):
        await local_hoster.merge_request(
            incarnation_repository=repo_name,
            source_branch="does_not_exist",
            title="Dummy title",
            description="Dummy description",
            with_automerge=False,
        )


async def test_get_incarnation_state_returns_state_of_incarnation_in_subdirectory(local_hoster):
    # GIVEN
    repo_name = "test-repository"
    subdir = "subdir"

    dummy_incarnation_state = IncarnationState(
        template_repository="template-repository",
        template_repository_version="template-repository-version",
        template_repository_version_hash="abcdef12",
        template_data={
            "foo": "bar",
        },
        template_data_full={
            "foo": "bar",
        },
    )

    await local_hoster.create_repository(repo_name)
    async with local_hoster.cloned_repository(repo_name) as repo:
        (repo.directory / subdir).mkdir()
        dummy_incarnation_state.save(repo.directory / subdir / ".fengine.yaml")
        await repo.commit_all("Initial commit")
        await repo.push()

        commit_sha = await repo.head()

    # WHEN
    result = await local_hoster.get_incarnation_state(repo_name, subdir)

    # THEN
    assert result[0] == commit_sha
    assert result[1] == dummy_incarnation_state


async def test_get_incarnation_state_returns_none_if_incarnation_does_not_exist(local_hoster):
    # GIVEN
    repo_name = "test-repository"
    await local_hoster.create_repository(repo_name)

    # WHEN
    state = await local_hoster.get_incarnation_state(repo_name, ".")

    # THEN
    assert state is None

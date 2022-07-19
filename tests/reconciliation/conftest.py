from pathlib import Path

import pytest

import foxops.engine as fengine
from foxops.external.git import GitRepository, git_exec
from foxops.models import DesiredIncarnationState, Incarnation


@pytest.fixture(name="test_dis")
def create_test_desired_incarnation_state():
    return DesiredIncarnationState(
        incarnation_repository="any-incarnation-repository",
        target_directory=".",
        template_repository="any-template-repository",
        template_repository_version="v1.0.0",
        template_data={"name": "any-name", "something_optional": "any-value"},
    )


@pytest.fixture(name="test_template_repository")
async def create_test_local_template_repository(tmp_path: Path):
    git_directory = tmp_path / "template-repository"
    await git_exec("init", str(git_directory), cwd=tmp_path)
    (git_directory / "fengine.yaml").write_text(
        """
variables:
    name:
        type: str
        description: "Just the name for the incarnation"
    something_optional:
        type: str
        description: "Something optional"
        default: "any-default-value"
        """
    )
    template_directory = git_directory / "template"
    template_directory.mkdir()
    (template_directory / "README.md").write_text(
        """
# Incarnation {{ name }}

We may have gotten some optional data: {{ something_optional }}.

        """
    )
    repo = GitRepository(git_directory)
    await repo.commit_all("Initial commit")
    await git_exec("tag", "v1.0.0", cwd=git_directory)
    yield repo


@pytest.fixture(name="test_empty_incarnation_repository")
async def create_test_empty_incarnation_repository(tmp_path: Path):
    git_directory = tmp_path / "empty-incarnation-repository"
    await git_exec("init", str(git_directory), cwd=tmp_path)
    repo = GitRepository(git_directory)
    # NOTE: we don't want it to push anything and return the current commit sha,
    #       like the normal `push` does.
    repo.push = repo.head  # type: ignore
    yield repo


@pytest.fixture(name="test_non_empty_incarnation_repository")
async def create_test_non_empty_incarnation_repository(
    test_empty_incarnation_repository: GitRepository,
):
    (test_empty_incarnation_repository.directory / "muted.txt").touch()
    await test_empty_incarnation_repository.commit_all("Initial commit")

    yield test_empty_incarnation_repository


@pytest.fixture(name="test_initialized_incarnation")
async def create_test_initialized_incarnation(
    test_template_repository: GitRepository,
    test_dis: DesiredIncarnationState,
    test_empty_incarnation_repository: GitRepository,
):
    incarnation_state = await fengine.initialize_incarnation(
        template_root_dir=test_template_repository.directory,
        template_repository=test_dis.template_repository,
        template_repository_version=test_dis.template_repository_version,
        template_data=test_dis.template_data,
        incarnation_root_dir=(
            test_empty_incarnation_repository.directory / test_dis.target_directory
        ),
    )
    incarnation = Incarnation(
        id=1,
        incarnation_repository=test_dis.incarnation_repository,
        target_directory=test_dis.target_directory,
        status="tbd",
        revision=incarnation_state.template_repository_version_hash,
    )
    yield incarnation, incarnation_state, test_dis, test_empty_incarnation_repository

import pytest

from foxops.external.git import (
    GitError,
    GitRepository,
    add_authentication_to_git_clone_url,
    git_exec,
)


@pytest.mark.asyncio
async def test_git_exec_throws_exception_on_nonzero_exit_code():
    # WHEN
    git_args = ["--invalid-flag"]

    # THEN
    with pytest.raises(GitError):
        await git_exec(*git_args)


@pytest.mark.asyncio
async def test_has_any_commits_returns_false_if_there_are_no_commits(tmp_path, logger):
    # GIVEN
    repo = GitRepository(tmp_path, logger=logger)
    await repo._run("init")

    # WHEN
    result = await repo.has_any_commits()

    # THEN
    assert result is False


@pytest.mark.asyncio
async def test_has_any_commits_returns_true_if_there_are_commits(tmp_path, logger):
    # GIVEN
    (tmp_path / "testfile").write_text("hello")

    repo = GitRepository(tmp_path, logger=logger)
    await repo._run("init")
    await repo._run("config", "user.name", "Test User")
    await repo._run("config", "user.email", "testuser@local")
    await repo.commit_all("initial commit")

    # WHEN
    result = await repo.has_any_commits()

    # THEN
    assert result is True


def test_add_authentication_to_git_clone_url_includes_username_password_in_output():
    # GIVEN
    source = "https://myrepo/test.git"
    username = "us:er"
    password = "p@ssword"

    # WHEN
    result = add_authentication_to_git_clone_url(source, username, password)

    # THEN
    assert result == "https://us%3Aer:p%40ssword@myrepo/test.git"

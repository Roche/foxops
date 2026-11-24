import tempfile
from pathlib import Path

import pytest

from foxops.external.git import (
    GitError,
    GitRepository,
    InvalidRefspecError,
    RevisionNotFoundError,
    add_authentication_to_git_clone_url,
    git_exec,
    shallow_checkout_refspec,
)


async def test_git_exec_throws_exception_on_nonzero_exit_code():
    # WHEN
    git_args = ["--invalid-flag"]

    # THEN
    with pytest.raises(GitError):
        await git_exec(*git_args)


async def test_has_any_commits_returns_false_if_there_are_no_commits(tmp_path):
    # GIVEN
    repo = GitRepository(tmp_path)
    await repo._run("init")

    # WHEN
    result = await repo.has_any_commits()

    # THEN
    assert result is False


async def test_has_any_commits_returns_true_if_there_are_commits(tmp_path):
    # GIVEN
    (tmp_path / "testfile").write_text("hello")

    repo = GitRepository(tmp_path)
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


def _write_to_file(file, content):
    with open(file, "w") as f:
        f.write(content)


async def test_diff_doesn_t_show_any_differences_if_non_exist():
    with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
        _write_to_file(f"{dir1}/file1", "Hello, World!")
        _write_to_file(f"{dir2}/file1", "Hello, World!")

        diff = await GitRepository.diff_directory(dir1, dir2)

        assert diff == ""


async def test_diff_shows_difference_if_exist():
    with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
        _write_to_file(f"{dir1}/file1", "Hello, World!")
        _write_to_file(f"{dir2}/file1", "Hallo, Welt!")

        diff = await GitRepository.diff_directory(dir1, dir2)

        EXPECTED_GIT_DIFF = f"""diff --git a{dir1}/file1 b{dir2}/file1
index b45ef6f..33607d0 100644
--- a{dir1}/file1
+++ b{dir2}/file1
@@ -1 +1 @@
-Hello, World!
\\ No newline at end of file
+Hallo, Welt!
\\ No newline at end of file
"""

        assert diff == EXPECTED_GIT_DIFF


async def test_diff_shows_difference_if_multiple_files_exist():
    with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
        _write_to_file(f"{dir1}/file1", "Hello, World!")
        _write_to_file(f"{dir2}/file1", "Hallo, Welt!")
        _write_to_file(f"{dir1}/file2", "Hello, World!")
        _write_to_file(f"{dir2}/file2", "Hello, World!")

        diff = await GitRepository.diff_directory(dir1, dir2)

        EXPECTED_GIT_DIFF = f"""diff --git a{dir1}/file1 b{dir2}/file1
index b45ef6f..33607d0 100644
--- a{dir1}/file1
+++ b{dir2}/file1
@@ -1 +1 @@
-Hello, World!
\\ No newline at end of file
+Hallo, Welt!
\\ No newline at end of file
"""

        assert diff == EXPECTED_GIT_DIFF


async def test_diff_show_new_file():
    with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
        _write_to_file(f"{dir2}/file1", "Hello, World!")

        diff = await GitRepository.diff_directory(dir1, dir2)

        EXPECTED_GIT_DIFF = f"""diff --git a{dir2}/file1 b{dir2}/file1
new file mode 100644
index 0000000..b45ef6f
--- /dev/null
+++ b{dir2}/file1
@@ -0,0 +1 @@
+Hello, World!
\\ No newline at end of file
"""

        assert diff == EXPECTED_GIT_DIFF


async def test_diff_show_deleted_file():
    with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
        _write_to_file(f"{dir1}/file1", "Hello, World!")

        diff = await GitRepository.diff_directory(dir1, dir2)

        EXPECTED_GIT_DIFF = f"""diff --git a{dir1}/file1 b{dir1}/file1
deleted file mode 100644
index b45ef6f..0000000
--- a{dir1}/file1
+++ /dev/null
@@ -1 +0,0 @@
-Hello, World!
\\ No newline at end of file
"""

        assert diff == EXPECTED_GIT_DIFF


@pytest.fixture
async def repo_with_origin(tmp_path) -> GitRepository:
    await git_exec("init", "--bare", "remote", cwd=tmp_path)
    await git_exec("init", "local", cwd=tmp_path)
    repo = GitRepository(tmp_path / "local")
    await repo._run("remote", "add", "origin", tmp_path / "remote")
    return repo


@pytest.fixture
def upload_pack_payload(tmp_path) -> tuple[Path, Path]:
    marker = tmp_path / "pwned"
    payload = tmp_path / "upload-pack.sh"
    payload.write_text(f'#!/bin/sh\ntouch {marker}\nexec git-upload-pack "$@"\n')
    payload.chmod(0o755)
    return payload, marker


async def test_fetch_rejects_refspec_that_looks_like_a_git_option(repo_with_origin, upload_pack_payload):
    # GIVEN
    payload, marker = upload_pack_payload

    # THEN
    with pytest.raises(InvalidRefspecError):
        await repo_with_origin.fetch(f"--upload-pack={payload}")
    assert not marker.exists()


async def test_fetch_does_not_run_upload_pack_if_validation_is_bypassed(repo_with_origin, upload_pack_payload, mocker):
    # GIVEN
    payload, marker = upload_pack_payload
    mocker.patch("foxops.external.git.validate_refspec", side_effect=lambda refspec: refspec)

    # THEN
    with pytest.raises(RevisionNotFoundError):
        await repo_with_origin.fetch(f"--upload-pack={payload}")
    assert not marker.exists()


async def test_shallow_checkout_refspec_rejects_refspec_that_looks_like_a_git_option(
    repo_with_origin, upload_pack_payload
):
    # GIVEN
    payload, marker = upload_pack_payload

    # THEN
    with pytest.raises(InvalidRefspecError):
        await shallow_checkout_refspec(repo_with_origin.directory, f"--upload-pack={payload}")
    assert not marker.exists()


async def test_shallow_checkout_refspec_does_not_run_upload_pack_if_validation_is_bypassed(
    repo_with_origin, upload_pack_payload, mocker
):
    # GIVEN
    payload, marker = upload_pack_payload
    mocker.patch("foxops.external.git.validate_refspec", side_effect=lambda refspec: refspec)

    # THEN
    with pytest.raises(RevisionNotFoundError):
        await shallow_checkout_refspec(repo_with_origin.directory, f"--upload-pack={payload}")
    assert not marker.exists()

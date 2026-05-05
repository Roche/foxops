"""Regression tests for issue #571: unbounded git subprocess spawning exhausts file descriptors.

Each test asserts desired behaviour (all concurrent operations succeed). Without a concurrency
cap on `cloned_repository()` they currently fail with `OSError(24): Too many open files`.

The mechanism: every `git` subprocess is launched with `stdout=PIPE, stderr=PIPE`
(`utils.check_call`), which holds two file descriptors open for the subprocess's
lifetime. With no semaphore on `cloned_repository()`, N concurrent API requests can
accumulate N×2 FDs simultaneously, exhausting the container limit.
"""
import asyncio
import resource
from pathlib import Path

import pytest

from foxops.hosters.local import LocalHoster


# Peak FD usage without a semaphore: CONCURRENCY × 2 pipe FDs per git subprocess
# plus OS base FDs (~15-20). FD_LIMIT is set below this peak so that the operations
# fail in current code; once a concurrency cap is in place they succeed.
_CONCURRENCY = 30
_FD_LIMIT = 64  # well below _CONCURRENCY×2 + base (~75 FDs)


@pytest.fixture
async def hoster_with_repo(tmp_path: Path) -> tuple[LocalHoster, str]:
    hoster = LocalHoster(tmp_path)
    repo_name = "test-repo"
    await hoster.create_repository(repo_name)
    async with hoster.cloned_repository(repo_name) as repo:
        (repo.directory / "README.md").write_text("hello")
        await repo.commit_all("initial commit")
        await repo.push()
    return hoster, repo_name


async def test_concurrent_cloned_repository_does_not_exhaust_file_descriptors(
    hoster_with_repo: tuple[LocalHoster, str],
) -> None:
    """Concurrent cloned_repository() calls must not raise OSError due to FD exhaustion.

    Without a concurrency cap, N concurrent callers each hold 2 pipe FDs for the
    lifetime of their underlying git subprocess. At moderate concurrency this
    accumulates past the OS file-descriptor limit (here simulated with setrlimit).
    """
    hoster, repo_name = hoster_with_repo

    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (_FD_LIMIT, hard))

    errors: list[OSError] = []

    async def clone_once() -> None:
        try:
            async with hoster.cloned_repository(repo_name):
                pass
        except OSError as exc:
            errors.append(exc)

    try:
        await asyncio.gather(*[clone_once() for _ in range(_CONCURRENCY)])
    finally:
        resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))

    assert not errors, (
        f"{len(errors)}/{_CONCURRENCY} concurrent cloned_repository() calls failed with "
        f"OSError — unbounded git subprocess spawning exhausts file descriptors "
        f"(FD limit: {_FD_LIMIT}, peak without semaphore: ~{_CONCURRENCY * 2 + 20} FDs)."
    )

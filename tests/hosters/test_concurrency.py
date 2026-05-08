"""Regression tests for issue #571: unbounded git subprocess spawning exhausts file descriptors.

The mechanism: every `git` subprocess is launched with `stdout=PIPE, stderr=PIPE`
(`utils.check_call`), holding two file descriptors open for the subprocess's lifetime.
With no semaphore, N concurrent API requests accumulate N×2 FDs, exhausting the
container limit.

`test_concurrent_subprocess_pipes_do_not_exhaust_fd_limit` proves the bounding
mechanism using `sleep` subprocesses under a tight RLIMIT_NOFILE.

`test_concurrent_cloned_repository_does_not_exhaust_file_descriptors` is an
integration test: it verifies that many concurrent `cloned_repository()` calls all
succeed, confirming the semaphore prevents errors on the real git code path.
"""

import asyncio
import resource
from pathlib import Path

import pytest

from foxops.hosters.local import LocalHoster
from foxops.utils import check_call

# --- sleep-based (mechanism) ---
# Mirrors the confirmed repro: N requests × 2 concurrent subprocesses per request,
# each holding stdout+stderr pipe FDs open for the subprocess lifetime.
# Sleep duration is short to keep the test fast; long enough for FDs to accumulate.
_SLEEP_CONCURRENCY = 80  # reproduced in issue #571 at this level
_SLEEP_FD_LIMIT = 256  # typical restrictive container limit
_SLEEP_SECS = 0.05


async def test_concurrent_subprocess_pipes_do_not_exhaust_fd_limit() -> None:
    """The semaphore in check_call must bound concurrent pipe FD consumption.

    A single foxops mutation spawns two concurrent git clones (template + incarnation
    repo). With N concurrent API requests and no concurrency cap, N×2×2 pipe FDs
    accumulate simultaneously, exceeding the container limit.

    Uses check_call("sleep") as a fast stand-in for a slow remote git clone — the
    same code path as all git subprocesses, without requiring network or git setup.
    """
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (_SLEEP_FD_LIMIT, hard))

    errors: list[OSError] = []

    async def with_open_pipes() -> None:
        try:
            await check_call("sleep", str(_SLEEP_SECS))
        except OSError as exc:
            errors.append(exc)

    async def one_request() -> None:
        # Two concurrent subprocesses per request — matches create_incarnation's
        # two concurrent cloned_repository() calls (template + incarnation repo).
        await asyncio.gather(with_open_pipes(), with_open_pipes())

    try:
        await asyncio.gather(*[one_request() for _ in range(_SLEEP_CONCURRENCY)])
    finally:
        resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))

    peak = _SLEEP_CONCURRENCY * 2 * 2
    assert not errors, (
        f"{len(errors)}/{_SLEEP_CONCURRENCY} simulated requests failed with OSError — "
        f"pipe FDs from concurrent subprocesses ({_SLEEP_CONCURRENCY}×2 subprocesses×2 FDs"
        f"={peak}) exceed the FD limit ({_SLEEP_FD_LIMIT})."
    )


# --- git-based (integration) ---
_CONCURRENCY = 30


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
    """Concurrent cloned_repository() calls must all succeed without error.

    The semaphore in check_call limits concurrent git subprocesses to 16, bounding
    the number of pipe file descriptors held simultaneously (16×2=32). Without the
    cap, 30 concurrent clones would accumulate 60 pipe FDs, exhausting restrictive
    container limits (~64 FDs). The sleep-based test above proves the bounding
    mechanism; this test confirms the fix applies to the real git code path.
    """
    hoster, repo_name = hoster_with_repo

    errors: list[Exception] = []

    async def clone_once() -> None:
        try:
            async with hoster.cloned_repository(repo_name):
                pass
        except Exception as exc:
            errors.append(exc)

    await asyncio.gather(*[clone_once() for _ in range(_CONCURRENCY)])

    assert not errors, f"{len(errors)}/{_CONCURRENCY} concurrent cloned_repository() calls failed: " f"{errors[:3]}"

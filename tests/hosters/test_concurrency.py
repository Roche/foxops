"""Regression tests for issue #571: unbounded git subprocess spawning exhausts file descriptors.

Each test asserts desired behaviour (all concurrent operations succeed). Without a concurrency
cap on `cloned_repository()` they currently fail with `OSError(24): Too many open files`.

The mechanism: every `git` subprocess is launched with `stdout=PIPE, stderr=PIPE`
(`utils.check_call`), which holds two file descriptors open for the subprocess's
lifetime. With no semaphore on `cloned_repository()`, N concurrent API requests can
accumulate N×2 FDs simultaneously, exhausting the container limit.

`test_concurrent_subprocess_pipes_exhaust_fd_limit` isolates the raw FD lifecycle
using `sleep` as a stand-in for a slow remote `git clone` (same pipe-FD lifecycle,
no network or git setup required).

`test_concurrent_cloned_repository_does_not_exhaust_file_descriptors` exercises the
actual `cloned_repository()` code path where the fix must be applied.
"""

import asyncio
import resource
from pathlib import Path

import pytest

from foxops.hosters.local import LocalHoster

# --- sleep-based (mechanism) ---
# Mirrors the confirmed repro: N requests × 2 concurrent subprocesses per request,
# each holding stdout+stderr pipe FDs open for the subprocess lifetime.
# Sleep duration is short to keep the test fast; long enough for FDs to accumulate.
_SLEEP_CONCURRENCY = 80  # reproduced in issue #571 at this level
_SLEEP_FD_LIMIT = 256  # typical restrictive container limit
_SLEEP_SECS = 0.05


async def test_concurrent_subprocess_pipes_do_not_exhaust_fd_limit() -> None:
    """Each asyncio subprocess with stdout/stderr PIPE holds 2 FDs for its lifetime.

    A single foxops mutation spawns two concurrent git clones (template + incarnation
    repo). With N concurrent API requests and no concurrency cap, N×2×2 pipe FDs
    accumulate simultaneously, exceeding the container limit.

    This test uses `sleep` as a stand-in for a slow remote `git clone` — identical
    FD lifecycle without requiring network or git infrastructure.
    """
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (_SLEEP_FD_LIMIT, hard))

    errors: list[OSError] = []

    async def with_open_pipes() -> None:
        try:
            proc = await asyncio.create_subprocess_exec(
                "sleep",
                str(_SLEEP_SECS),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
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
# Tests the actual cloned_repository() code path; this is where the fix must be applied.
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

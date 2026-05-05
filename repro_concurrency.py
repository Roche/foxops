"""
Repro for issue #571: unbounded git subprocess spawning exhausts file descriptors.

Demonstrates the failure mode directly: N concurrent asyncio subprocesses with
stdout+stderr PIPEs, combined with a realistic container FD limit.

In production each `git clone` against a remote GitLab holds its pipe FDs open
for the duration of the clone (seconds to tens of seconds). With no semaphore
on cloned_repository(), all N concurrent API requests can accumulate their
subprocess FDs simultaneously.

Each subprocess contributes at least 2 FDs (stdout+stderr read-ends held by
asyncio's StreamReader). The process itself also needs FDs for stdin(0),
stdout(1), stderr(2), the event loop, DB connections, etc. Under a typical
container limit of 1024 this is exhausted quickly at moderate concurrency.

We use a `sleep` subprocess as a stand-in for a slow `git clone` — same FD
lifecycle, no network required. We lower the FD limit with resource.setrlimit
to match container conditions.

Usage:
    poetry run python repro_concurrency.py [concurrency]
"""

import asyncio
import resource
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from foxops.hosters.local import LocalHoster
import foxops.engine as fengine

CONCURRENCY = int(sys.argv[1]) if len(sys.argv) > 1 else 80
N_TEMPLATE_FILES = 20
FD_LIMIT = 256          # typical restrictive container limit
SIMULATED_CLONE_SECS = 2.0  # how long each "git clone" holds its pipe FDs open


async def _subprocess_with_open_pipes(duration: float) -> None:
    """Spawn a process that runs for `duration` seconds, holding its pipes open."""
    proc = await asyncio.create_subprocess_exec(
        "sleep", str(duration),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.wait()


async def simulate_one_request(i: int) -> tuple[str, float]:
    """
    Simulate the subprocess FD lifecycle of one foxops mutation request.
    A create_incarnation spawns ~2 concurrent clones, each holding pipes open
    for the clone duration, then several fast git commands (add/commit/push).
    """
    start = time.monotonic()
    try:
        # Two concurrent clones (template + incarnation repos), each holding
        # stdout+stderr pipes open for SIMULATED_CLONE_SECS.
        await asyncio.gather(
            _subprocess_with_open_pipes(SIMULATED_CLONE_SECS),
            _subprocess_with_open_pipes(SIMULATED_CLONE_SECS),
        )
        elapsed = time.monotonic() - start
        return ("ok", elapsed)
    except OSError as e:
        elapsed = time.monotonic() - start
        return (f"OSError({e.errno}): {e.strerror}", elapsed)
    except Exception as e:
        elapsed = time.monotonic() - start
        return (f"{type(e).__name__}: {e}", elapsed)


async def main():
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (FD_LIMIT, hard))
    print(
        f"FD limit: {FD_LIMIT}  |  simulated clone duration: {SIMULATED_CLONE_SECS}s  "
        f"|  concurrency: {CONCURRENCY}"
    )
    print(
        f"Peak pipe FDs expected: {CONCURRENCY} requests × 2 clones × 2 pipes "
        f"= {CONCURRENCY * 2 * 2} FDs  (limit: {FD_LIMIT})"
    )

    try:
        t0 = time.monotonic()
        results = await asyncio.gather(
            *[simulate_one_request(i) for i in range(CONCURRENCY)],
            return_exceptions=True,
        )
        total = time.monotonic() - t0
    finally:
        resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))

    unwrapped = []
    for r in results:
        if isinstance(r, Exception):
            unwrapped.append((f"{type(r).__name__}: {r}", 0.0))
        else:
            unwrapped.append(r)

    ok = [(s, e) for s, e in unwrapped if s == "ok"]
    errors = [(s, e) for s, e in unwrapped if s != "ok"]
    latencies = sorted(e for _, e in ok)

    print(f"\nCompleted in {total:.1f}s")
    print(f"  Success : {len(ok)}/{CONCURRENCY}")
    print(f"  Errors  : {len(errors)}/{CONCURRENCY}")
    if latencies:
        p50 = latencies[len(latencies) // 2]
        p99 = latencies[min(int(len(latencies) * 0.99), len(latencies) - 1)]
        print(f"  Latency : p50={p50:.2f}s  p99={p99:.2f}s  max={max(latencies):.2f}s")
    if errors:
        print("\nErrors:")
        seen: dict[str, list[float]] = {}
        for msg, elapsed in errors:
            kind = msg.split(":")[0]
            seen.setdefault(kind, []).append(elapsed)
        for kind, times in seen.items():
            print(f"  {kind} × {len(times)}")
        print(f"\nFirst error: {errors[0][0]}")


asyncio.run(main())

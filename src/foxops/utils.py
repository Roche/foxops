import asyncio
import subprocess

from .errors import FoxopsError
from .logger import get_logger

logger = get_logger("utils")


class CalledProcessError(subprocess.CalledProcessError, FoxopsError):
    """Error raised when copier fails."""

    def __str__(self):
        """Extend so that the string prints stdout and stderr by default."""
        return f"{super().__str__()} with stdout '{self.stdout}' and stderr '{self.stderr}'"


async def check_call(
    program: str,
    *args,
    expected_returncodes: frozenset = frozenset({0}),
    timeout: int | float | None = None,
    **kwargs,
) -> asyncio.subprocess.Process:
    """Execute the given executable and raise error on non-zero exit code.

    This function is simply wrapping `asyncio.create_subprocess_exec()`
    and raises and exception in case the exit code is non-zero,
    similar to what `subprocess.check_call()` does.

    The timeout parameter can be used to specify a maximum wait time in seconds. If the timeout expires before the
    called process completes, the subprocess will be killed.
    -> Setting the timeout to None (default) will allow the child process to take forever.
    """
    proc = await asyncio.create_subprocess_exec(
        program,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **kwargs,
    )

    try:
        await asyncio.wait_for(proc.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        stdout_buffer = None if proc.stdout is None else bytes(proc.stdout._buffer)  # type: ignore
        stderr_buffer = None if proc.stderr is None else bytes(proc.stderr._buffer)  # type: ignore

        logger.error(
            "killed process as it exceeded the timeout",
            stdout_buffer=stdout_buffer,
            stderr_buffer=stderr_buffer,
        )
        raise

    if proc.returncode is not None and proc.returncode not in expected_returncodes:
        raise CalledProcessError(
            proc.returncode,
            [program] + list(args),
            await proc.stdout.read() if proc.stdout else None,
            await proc.stderr.read() if proc.stderr else None,
        )

    return proc

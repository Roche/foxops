import asyncio
import re
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

from foxops.errors import FoxopsError, FoxopsUserError, RetryableError
from foxops.utils import CalledProcessError, check_call


class GitError(FoxopsError):
    """Error raised when a call to git fails."""

    def __init__(self, message=None):
        super().__init__(f"Git failed with an unexpected non-zero exit code: '{message}'")


class RebaseRequiredError(GitError, RetryableError):
    """Error raised when a git fails due to a rebase being required."""

    def __init__(self):
        super().__init__("Rebase is required. Retrying may resolve the issue.")


class RevisionNotFoundError(GitError, FoxopsUserError):
    """Error raised when a git fails due to a revision not being found."""

    def __init__(self, ref: bytes):
        super().__init__(f"Revision '{ref.decode('utf-8')}' not found.")


GIT_ERROR_ORACLE = {
    re.compile(
        rb"hint: Updates were rejected because the remote contains work that you do\n" rb"hint: not have locally."
    ): RebaseRequiredError,
    re.compile(rb"fatal: couldn't find remote ref (?P<ref>.*?)\n"): RevisionNotFoundError,
}


async def git_exec(*args, **kwargs) -> asyncio.subprocess.Process:
    try:
        return await check_call("git", *args, **kwargs)
    except CalledProcessError as exc:
        if oracle_hit_exc := next(
            (e(**m.groupdict()) for p, e in GIT_ERROR_ORACLE.items() if (m := p.search(exc.stderr))), None
        ):
            raise oracle_hit_exc from exc

        raise GitError(message=exc.stderr) from exc


def add_authentication_to_git_clone_url(source: str, username: str, password: str):
    if not source.startswith(("http://", "https://")):
        raise ValueError("only http:// and https:// repository URLs are allowed")

    url_parts = urlparse(source)
    if url_parts.username is not None or url_parts.password is not None:
        raise ValueError(
            f"the repository URL ({source}) must not contain a username/password. "
            "pass them in as separate variables instead."
        )

    netloc = f"{quote(username, safe='')}:{quote(password, safe='')}@{url_parts.netloc}"
    url_parts = url_parts._replace(netloc=netloc)

    return urlunparse(url_parts)


class GitRepository:
    def __init__(self, directory: Path):
        if not directory.exists():
            raise ValueError("the given path doesn't exist")
        if not directory.is_dir():
            raise ValueError("the given path is not a directory")

        self.directory = directory

    async def _run(self, *args, timeout: int | float | None = 30, **kwargs) -> asyncio.subprocess.Process:
        return await git_exec(*args, cwd=self.directory, timeout=timeout, **kwargs)

    async def has_any_commits(self) -> bool:
        result = await self._run("rev-list", "-n", "1", "--all")
        stdout = await result.stdout.read() if result.stdout is not None else b""

        return len(stdout.strip()) > 0

    async def create_and_checkout_branch(self, branch: str, exist_ok=False):
        try:
            await self._run("checkout", "-b", branch)
        except GitError:
            if exist_ok:
                await self._run("checkout", branch)
            else:
                raise

    async def commit_all(self, message: str):
        await self._run("add", ".")
        return await self._run("commit", "-m", message)

    async def diff(self, ref_old: str, ref_new: str) -> str:
        cmdline = f"git --no-pager diff {ref_old}..{ref_new}".split()
        proc = await asyncio.create_subprocess_exec(
            *cmdline,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            cwd=str(self.directory),
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode not in {0, 1}:
            raise CalledProcessError(
                proc.returncode if proc.returncode is not None else -1,
                cmdline,
                stdout,
                stderr,
            )

        return stdout.decode()

    async def current_branch(self) -> str:
        proc = await self._run("branch", "--show-current")
        if proc.stdout is None:
            raise GitError("unable to determine the current git branch")

        return (await proc.stdout.read()).strip().decode()

    async def push(self) -> str:
        current_branch = await self.current_branch()

        proc = await self._run("push", "--porcelain", "-u", "origin", current_branch)
        if proc.stderr is None:
            stderr = ""
        else:
            stderr = (await proc.stderr.read()).decode()

        # exclude remote messages from stderr
        stderr_non_remote_lines = list(filter(lambda line: not line.startswith("remote:"), stderr.splitlines()))
        if len(stderr_non_remote_lines) > 0:
            raise GitError()

        return await self.head()

    async def head(self) -> str:
        proc = await self._run("rev-parse", "HEAD")
        if proc.stdout is None:
            raise GitError("unable to determine the current git HEAD")
        return (await proc.stdout.read()).decode().strip()

    async def fetch(self, refspec: str) -> None:
        await self._run("fetch", "origin", refspec)

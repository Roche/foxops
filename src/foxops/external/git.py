import asyncio
import re
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

from foxops.errors import FoxopsError, FoxopsUserError, RetryableError
from foxops.logger import get_logger
from foxops.utils import CalledProcessError, check_call

logger = get_logger("git")


class GitError(FoxopsError):
    """Error raised when a call to git fails."""

    def __init__(self, message: str):
        self.message = message
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
        rb"hint: Updates were rejected because the remote contains work that you do.*not.*have locally.",
        re.DOTALL,
    ): RebaseRequiredError,
    re.compile(rb"hint: Updates were rejected because the tip of your current branch is behind"): RebaseRequiredError,
    re.compile(rb"error: cannot lock ref '.*': is at [a-f0-9]+ but expected [a-f0-9]+"): RebaseRequiredError,
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

        raise GitError(message=exc.stderr.decode()) from exc


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
    def __init__(self, directory: Path, push_delay_seconds: int = 0):
        """
        :param directory: the path to the git repository
        :param push_delay_seconds: the number of seconds to wait before pushing changes to the remote. This is
            especially useful for testing the behavior of foxops when two incarnations in one repo are modified
            concurrently.
        """

        if not directory.exists():
            raise ValueError("the given path doesn't exist")
        if not directory.is_dir():
            raise ValueError("the given path is not a directory")

        self.directory = directory
        self.push_delay_seconds = push_delay_seconds

    async def _run(self, *args, timeout: int | float | None = 30, **kwargs) -> asyncio.subprocess.Process:
        return await git_exec(*args, cwd=self.directory, timeout=timeout, **kwargs)

    async def has_commit(self, commit_sha: str) -> bool:
        try:
            await self._run("cat-file", "-e", commit_sha)
            return True
        except GitError:
            return False

    async def has_any_commits(self) -> bool:
        result = await self._run("rev-list", "-n", "1", "--all")
        stdout = await result.stdout.read() if result.stdout is not None else b""

        return len(stdout.strip()) > 0

    async def checkout_branch(self, branch: str):
        await self._run("checkout", branch)

    async def create_and_checkout_branch(self, branch: str, exist_ok=False):
        try:
            await self._run("checkout", "-b", branch)
        except GitError:
            if exist_ok:
                await self._run("checkout", branch)
            else:
                raise

    async def has_uncommitted_changes(self) -> bool:
        result = await self._run("status", "--porcelain")
        stdout = await result.stdout.read() if result.stdout is not None else b""

        return len(stdout.strip()) > 0

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

    async def origin_default_branch(self) -> str | None:
        """Returns "main" if the remote repo is empty."""
        try:
            proc = await self._run("symbolic-ref", "refs/remotes/origin/HEAD", "--short")
        except GitError as e:
            if e.message.startswith("fatal: ref refs/remotes/origin/HEAD is not a symbolic ref"):
                return None
            raise

        if proc.stdout is None:
            raise GitError("unable to determine the default git branch")

        return (await proc.stdout.read()).strip().decode()

    async def current_branch(self) -> str:
        proc = await self._run("branch", "--show-current")
        if proc.stdout is None:
            raise GitError("unable to determine the current git branch")

        return (await proc.stdout.read()).strip().decode()

    async def merge(self, branch: str, ff_only: bool = False):
        ff_only_args = ["--ff-only"] if ff_only else []
        await self._run("merge", *ff_only_args, branch)

    async def push(self, tags: bool = False) -> str:
        if self.push_delay_seconds > 0:
            await asyncio.sleep(self.push_delay_seconds)

        current_branch = await self.current_branch()

        additional_args = []
        if tags:
            additional_args.append("--tags")

        proc = await self._run("push", "--porcelain", "-u", "origin", *additional_args, current_branch)
        if proc.stderr is None:
            stderr = ""
        else:
            stderr = (await proc.stderr.read()).decode()

        # exclude remote messages from stderr
        stderr_non_remote_lines = list(filter(lambda line: not line.startswith("remote:"), stderr.splitlines()))
        if len(stderr_non_remote_lines) > 0:
            raise GitError("\n".join(stderr_non_remote_lines))

        return await self.head()

    async def pull(self, rebase: bool = True):
        if rebase:
            await self._run("pull", "--rebase")
        else:
            await self._run("pull", "--no-rebase")

    async def head(self) -> str:
        proc = await self._run("rev-parse", "HEAD")
        if proc.stdout is None:
            raise GitError("unable to determine the current git HEAD")
        return (await proc.stdout.read()).decode().strip()

    async def fetch(self, refspec: str | None = None) -> None:
        args = []
        if refspec is not None:
            args.append(refspec)

        await self._run("fetch", "origin", *args)

    async def rebase(self, branch: str | None = None) -> None:
        if branch is None:
            branch = await self.origin_default_branch()

        logger.debug("rebasing", current_branch=await self.current_branch(), onto_branch=branch)
        await self._run("rebase", branch)

    async def tag(self, tag: str):
        await self._run("tag", tag)

    async def last_commit_id_that_changed_file(self, path: str) -> str:
        proc = await self._run("log", "-1", "--format=%H", "--", path)
        if proc.stdout is None:
            raise GitError("unable to determine the last commit that changed a file")

        return (await proc.stdout.read()).decode().strip()

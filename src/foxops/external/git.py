import asyncio
import shutil
from pathlib import Path
from tempfile import mkdtemp
from urllib.parse import quote, urlparse, urlunparse

from structlog.stdlib import BoundLogger

from foxops.errors import FoxopsError, RetryableError
from foxops.settings import Settings
from foxops.utils import CalledProcessError, check_call

GIT_REBASE_REQUIRED_ERROR_MESSAGE = (
    b"hint: Updates were rejected because the remote contains work that you do\n"
    b"hint: not have locally."
)


class GitError(FoxopsError):
    """Error raised when a call to git fails."""

    def __init__(self, message=None):
        super().__init__(
            message if message else "Git failed with an unexpected non-zero exit code."
        )


async def git_exec(*args, **kwargs) -> asyncio.subprocess.Process:
    try:
        return await check_call("git", *args, **kwargs)
    except CalledProcessError as exc:
        raise GitError() from exc


def add_authentication_to_git_clone_url(source: str, username: str, password: str):
    if not source.startswith("https://"):
        raise ValueError("only https:// repository URLs are allowed")

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
    def __init__(self, directory: Path, logger: BoundLogger):
        if not directory.exists():
            raise ValueError("the given path doesn't exist")
        if not directory.is_dir():
            raise ValueError("the given path is not a directory")

        self.directory = directory
        self.logger = logger.bind(directory=directory.name)

    async def _run(
        self, *args, timeout: int | float | None = 10, **kwargs
    ) -> asyncio.subprocess.Process:
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
        proc = await self._run(
            "--no-pager",
            "diff",
            f"{ref_old}..{ref_new}",
            expected_returncodes=frozenset({0, 1}),
            timeout=30,
        )

        output = ""
        if proc.stdout is not None:
            output = (await proc.stdout.read()).decode()

        return output

    async def push(self):
        proc = await self._run("branch", "--show-current")
        current_branch = (await proc.stdout.read()).strip()

        self.logger.debug("pushing branch", current_branch=current_branch)

        proc = await self._run("push", "--porcelain", "-u", "origin", current_branch)
        stderr = (await proc.stderr.read()).decode()

        # exclude remote messages from stderr
        stderr_non_remote_lines = list(
            filter(lambda line: not line.startswith("remote:"), stderr.splitlines())
        )
        if len(stderr_non_remote_lines) > 0:
            self.logger.error(
                "got unexpected error output while reading branch", stderr=stderr
            )
            raise GitError()

        self.logger.debug("push output", stdout=await proc.stdout.read())

    async def push_with_potential_retry(self) -> None:
        try:
            await self.push()
        except GitError as exc:
            if isinstance(exc.__cause__, CalledProcessError):
                if GIT_REBASE_REQUIRED_ERROR_MESSAGE in exc.__cause__.stderr:
                    raise RetryableError(
                        "new commits on the target branch, need to retry"
                    ) from exc
            raise exc

    async def head(self) -> str:
        proc = await self._run("rev-parse", "HEAD")
        if proc.stdout is None:
            raise GitError("unable to determine the current git HEAD")
        return (await proc.stdout.read()).decode().strip()

    async def fetch(self, refspec: str) -> None:
        await self._run("fetch", "origin", refspec)


class TemporaryGitRepository:
    GIT_HISTORY_DEPTH = 1

    def __init__(
        self,
        logger: BoundLogger,
        source: str,
        username: str,
        password: str,
        refspec: str | None = None,
    ):
        self.settings = Settings()
        self.logger = logger
        self.source = add_authentication_to_git_clone_url(source, username, password)
        self.refspec = refspec

        self.tempdir: Path | None = None

    async def __aenter__(self) -> GitRepository:
        self.tempdir = Path(mkdtemp())

        if self.refspec is None:
            await git_exec(
                "clone",
                f"--depth={self.GIT_HISTORY_DEPTH}",
                self.source,
                self.tempdir,
                cwd=Path.home(),
            )
        else:
            # NOTE(TF): this only works for git hosters which have enabled `uploadpack.allowReachableSHA1InWant` on the server side.
            #           It seems to be the case for GitHub and GitLab.
            #           In addition it seems that if the refspec is a tag, it won't be created locally and we later on
            #           cannot address it in e.g. a `switch`. So we need to fetch all tag refs, which should be fine.
            await git_exec("init", self.tempdir, cwd=Path.home())
            await git_exec("remote", "add", "origin", self.source, cwd=self.tempdir)
            await git_exec(
                "fetch",
                f"--depth={self.GIT_HISTORY_DEPTH}",
                "origin",
                "--tags",
                self.refspec,
                cwd=self.tempdir,
            )
            await git_exec("reset", "--hard", "FETCH_HEAD", cwd=self.tempdir)

        # NOTE(TF): set author data
        await git_exec(
            "config",
            "user.name",
            self.settings.git_commit_author_name,
            cwd=self.tempdir,
        )
        await git_exec(
            "config",
            "user.email",
            self.settings.git_commit_author_email,
            cwd=self.tempdir,
        )

        return GitRepository(self.tempdir, logger=self.logger)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.tempdir)

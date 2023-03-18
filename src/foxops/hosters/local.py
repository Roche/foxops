import re
import tempfile
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from typing import AsyncIterator

from pydantic import BaseModel

from foxops.engine import IncarnationState, load_incarnation_state
from foxops.external.git import GitError, GitRepository, git_exec
from foxops.hosters import GitSha, Hoster, MergeRequestId, ReconciliationStatus
from foxops.hosters.types import MergeRequestStatus, RepositoryMetadata


class MergeRequest(BaseModel):
    id: int

    title: str
    description: str

    source_branch: str
    target_branch: str

    status: MergeRequestStatus


class LocalHoster(Hoster):
    def __init__(self, directory: Path, push_delay_seconds: int = 0):
        self.directory = directory

        self._merge_requests: dict[str, list[MergeRequest]] = defaultdict(list)
        self.push_delay_seconds = push_delay_seconds

    async def validate(self) -> None:
        if not self.directory.exists():
            raise ValueError("Directory does not exist")
        if not self.directory.is_dir():
            raise ValueError("Path is not a directory")

    async def create_repository(self, repository: str) -> None:
        if not re.fullmatch(r"^[a-z0-9-_]+$", repository):
            raise ValueError("Invalid repository name, must only contain lowercase letters, numbers and dashes.")

        git_directory = self.directory / repository
        git_directory.mkdir(parents=False, exist_ok=False)

        # we're creating a bare repository because "clients" of this hoster will be cloning and pushing to it
        # git doesn't allow pushing to the checked-out branch of a repository
        await git_exec("init", "--bare", cwd=git_directory)

    async def get_incarnation_state(
        self, incarnation_repository: str, target_directory: str
    ) -> tuple[GitSha, IncarnationState] | None:
        async with self.cloned_repository(incarnation_repository) as repo:
            fengine_path = Path(repo.directory, target_directory, ".fengine.yaml")

            if not fengine_path.exists():
                return None

            commit_id = await repo.last_commit_id_that_changed_file(str(fengine_path))
            incarnation_state = load_incarnation_state(fengine_path)

        return commit_id, incarnation_state

    async def merge_request(
        self, *, incarnation_repository: str, source_branch: str, title: str, description: str, with_automerge=False
    ) -> tuple[GitSha, MergeRequestId]:
        existing_merge_requests = self._merge_requests[incarnation_repository]

        new_merge_request = MergeRequest(
            id=len(existing_merge_requests),
            title=title,
            description=description,
            source_branch=source_branch,
            target_branch="main",
            status=MergeRequestStatus.OPEN,
        )

        commit_id = await self.has_pending_incarnation_branch(incarnation_repository, source_branch)
        if commit_id is None:
            raise ValueError("Branch does not exist")

        existing_merge_requests.append(new_merge_request)

        if with_automerge:
            await self.merge_merge_request(incarnation_repository, str(new_merge_request.id))

        return commit_id, str(new_merge_request.id)

    def get_merge_request(self, incarnation_repository: str, merge_request_id: str) -> MergeRequest:
        return self._merge_requests[incarnation_repository][int(merge_request_id)]

    def close_merge_request(self, incarnation_repository: str, merge_request_id: str) -> None:
        mr = self.get_merge_request(incarnation_repository, merge_request_id)
        mr.status = MergeRequestStatus.CLOSED

    async def merge_merge_request(self, incarnation_repository: str, merge_request_id: str):
        mr = self.get_merge_request(incarnation_repository, merge_request_id)

        async with self.cloned_repository(incarnation_repository) as repo:
            await repo.fetch(mr.source_branch)
            await repo.merge(f"origin/{mr.source_branch}", ff_only=False)
            await repo.push()

        mr.status = MergeRequestStatus.MERGED

    @asynccontextmanager
    async def cloned_repository(
        self, repository: str, *, refspec: str | None = None, bare: bool = False
    ) -> AsyncIterator[GitRepository]:
        repo_path = (self.directory / repository).absolute()
        if not Path(repo_path).is_dir():
            raise ValueError("Repository does not exist")

        with tempfile.TemporaryDirectory() as tmpdir:
            if refspec is None:
                depth_args = ["--bare"] if bare else ["--depth=1", "--no-single-branch"]
                await git_exec(
                    "clone",
                    *depth_args,
                    repo_path,
                    ".",
                    cwd=tmpdir,
                )
            else:
                await git_exec("init", cwd=tmpdir)
                await git_exec("remote", "add", "origin", repo_path, cwd=tmpdir)
                await git_exec("fetch", "--depth=1", "origin", "--tags", refspec, cwd=tmpdir)
                await git_exec("reset", "--hard", "FETCH_HEAD", cwd=tmpdir)

            # set author data
            await git_exec("config", "user.name", "foxops", cwd=tmpdir)
            await git_exec("config", "user.email", "noreply@foxops.io", cwd=tmpdir)

            yield GitRepository(Path(tmpdir), push_delay_seconds=self.push_delay_seconds)

    async def has_pending_incarnation_branch(self, project_identifier: str, branch: str) -> GitSha | None:
        try:
            result = await git_exec("rev-parse", f"refs/heads/{branch}", cwd=self.directory / project_identifier)
        except GitError as e:
            if e.message.index("unknown revision or path not in the working tree") >= 0:
                return None

            raise

        if result.stdout is None:
            raise RuntimeError("git rev-parse did not return any output")
        stdout = await result.stdout.read()

        return stdout.strip().decode()

    async def has_pending_incarnation_merge_request(
        self, project_identifier: str, branch: str
    ) -> MergeRequestId | None:
        raise NotImplementedError

    async def get_repository_metadata(self, project_identifier: str) -> RepositoryMetadata:
        return {
            "default_branch": "main",
            "http_url": "http://does-not-exist-for-local-hoster",
        }

    async def get_reconciliation_status(
        self,
        incarnation_repository: str,
        target_directory: str,
        commit_sha: GitSha,
        merge_request_id: str | None,
        pipeline_timeout: timedelta | None = None,
    ) -> ReconciliationStatus:
        return ReconciliationStatus.SUCCESS

    async def does_commit_exist(self, incarnation_repository: str, commit_sha: GitSha) -> bool:
        try:
            result = await git_exec("cat-file", "commit", commit_sha, cwd=self.directory / incarnation_repository)
        except GitError as e:
            if e.message.index("bad file") >= 0:
                return False

            raise

        if result.returncode == 0:
            return True
        raise RuntimeError(f"Unexpected return code from git cat-file: {result.returncode}")

    async def get_commit_url(self, incarnation_repository: str, commit_sha: GitSha) -> str:
        return f"{self.directory / incarnation_repository}:commit/{commit_sha}"

    async def get_merge_request_url(self, incarnation_repository: str, merge_request_id: str) -> str:
        return f"{self.directory / incarnation_repository}:merge_requests/{merge_request_id}"

    async def get_merge_request_status(self, incarnation_repository: str, merge_request_id: str) -> MergeRequestStatus:
        merge_request_index = int(merge_request_id)

        existing_merge_requests = self._merge_requests[incarnation_repository]
        if merge_request_index >= len(existing_merge_requests):
            raise ValueError("Merge request does not exist")

        return existing_merge_requests[merge_request_index].status

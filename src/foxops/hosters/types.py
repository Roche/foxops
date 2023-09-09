from datetime import timedelta
from enum import Enum
from typing import AsyncContextManager, Protocol, TypedDict

from foxops.engine import IncarnationState
from foxops.external.git import GitRepository


class RepositoryMetadata(TypedDict):
    default_branch: str
    http_url: str


GitSha = str
MergeRequestId = str


class ReconciliationStatus(Enum):
    UNKNOWN = "unknown"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class MergeRequestStatus(Enum):
    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class Hoster(Protocol):
    async def validate(self) -> None:
        ...

    async def get_incarnation_state(
        self, incarnation_repository: str, target_directory: str
    ) -> tuple[GitSha, IncarnationState] | None:
        ...

    async def merge_request(
        self, *, incarnation_repository: str, source_branch: str, title: str, description: str, with_automerge=False
    ) -> tuple[GitSha, MergeRequestId]:
        ...

    def cloned_repository(
        self, repository: str, *, refspec: str | None = None, bare: bool = False
    ) -> AsyncContextManager[GitRepository]:
        ...

    async def has_pending_incarnation_branch(self, project_identifier: str, branch: str) -> GitSha | None:
        ...

    async def has_pending_incarnation_merge_request(
        self, project_identifier: str, branch: str
    ) -> MergeRequestId | None:
        ...

    async def get_repository_metadata(self, project_identifier: str) -> RepositoryMetadata:
        ...

    async def get_reconciliation_status(
        self,
        incarnation_repository: str,
        target_directory: str,
        commit_sha: GitSha,
        merge_request_id: str | None,
        pipeline_timeout: timedelta | None = None,
    ) -> ReconciliationStatus:
        ...

    async def does_commit_exist(self, incarnation_repository: str, commit_sha: GitSha) -> bool:
        ...

    async def get_commit_url(self, incarnation_repository: str, commit_sha: GitSha) -> str:
        ...

    async def get_merge_request_url(self, incarnation_repository: str, merge_request_id: str) -> str:
        ...

    async def get_merge_request_status(self, incarnation_repository: str, merge_request_id: str) -> MergeRequestStatus:
        ...

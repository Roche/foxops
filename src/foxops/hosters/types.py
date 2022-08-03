from typing import AsyncContextManager, Protocol, TypedDict

from foxops.engine import IncarnationState
from foxops.external.git import GitRepository


class RepositoryMetadata(TypedDict):
    default_branch: str
    http_url: str


GitSha = str


class Hoster(Protocol):
    async def validate(self) -> None:
        ...

    async def get_incarnation_state(
        self, incarnation_repository: str, target_directory: str
    ) -> IncarnationState | None:
        ...

    async def merge_request(
        self,
        *,
        incarnation_repository: str,
        source_branch: str,
        title: str,
        description: str,
        with_automerge=False
    ) -> GitSha:
        ...

    def cloned_repository(
        self, repository: str, *, refspec: str | None = None, bare: bool = False
    ) -> AsyncContextManager[GitRepository]:
        ...

    async def has_pending_incarnation_branch(
        self, project_identifier: str, branch: str
    ) -> GitSha | None:
        ...

    async def get_repository_metadata(
        self, project_identifier: str
    ) -> RepositoryMetadata:
        ...

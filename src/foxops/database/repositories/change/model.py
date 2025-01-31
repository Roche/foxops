import enum
from datetime import datetime, timezone
from typing import Self

from pydantic import BaseModel, ConfigDict


class ChangeType(enum.Enum):
    DIRECT = "direct"
    MERGE_REQUEST = "merge_request"


class ChangeInDB(BaseModel):
    id: int

    incarnation_id: int
    revision: int

    commit_sha: str
    commit_pushed: bool

    type: ChangeType
    created_at: datetime

    requested_version_hash: str
    requested_version: str
    requested_data: str

    template_data_full: str

    merge_request_id: str | None
    merge_request_branch_name: str | None
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_database_row(cls, obj) -> Self:
        change_in_db = cls.model_validate(obj)
        change_in_db.created_at = change_in_db.created_at.replace(tzinfo=timezone.utc)

        return change_in_db


class IncarnationWithChangesSummary(BaseModel):
    """Represents an incarnation combined with information about its latest change."""

    id: int

    incarnation_repository: str
    target_directory: str
    template_repository: str

    revision: int
    type: ChangeType
    commit_sha: str
    requested_version: str
    merge_request_id: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

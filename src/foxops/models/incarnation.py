from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from foxops.database.repositories.change.model import ChangeType
from foxops.database.schema import Permission
from foxops.engine import TemplateData
from foxops.hosters import ReconciliationStatus
from foxops.hosters.types import MergeRequestStatus
from foxops.models.group import Group
from foxops.models.user import User


class Incarnation(BaseModel):
    """An Incarnation represents a single incarnation instance in the inventory."""

    id: int
    incarnation_repository: str
    target_directory: str
    template_repository: str | None
    commit_sha: str
    merge_request_id: str | None
    owner: User | None
    model_config = ConfigDict(from_attributes=True)


class IncarnationBasic(BaseModel):
    id: int
    incarnation_repository: str
    target_directory: str

    commit_sha: str
    commit_url: str

    merge_request_id: str | None
    merge_request_url: str | None

    model_config = ConfigDict(from_attributes=True)


class UserPermission(BaseModel):
    user: User
    type: Permission

    model_config = ConfigDict(from_attributes=True)


class GroupPermission(BaseModel):
    group: Group
    type: Permission

    model_config = ConfigDict(from_attributes=True)


class UnresolvedUserPermissions(BaseModel):
    user_id: int
    type: Permission

    model_config = ConfigDict(from_attributes=True)


class UnresolvedGroupPermissions(BaseModel):
    group_id: int
    type: Permission

    model_config = ConfigDict(from_attributes=True)


class IncarnationWithDetails(IncarnationBasic):
    status: ReconciliationStatus = Field(description="DEPRECATED. Use the 'merge_request_status' field instead.")
    owner: User
    user_permissions: list[UserPermission]
    group_permissions: list[GroupPermission]

    merge_request_status: MergeRequestStatus | None
    revision: int | None

    template_repository: str | None
    template_repository_version: str | None
    template_repository_version_hash: str | None
    template_data: TemplateData | None
    template_data_full: TemplateData | None

    model_config = ConfigDict(from_attributes=True)


class IncarnationWithLatestChangeDetails(BaseModel):
    id: int
    incarnation_repository: str
    target_directory: str
    template_repository: str

    revision: int
    type: ChangeType
    requested_version: str
    created_at: datetime

    commit_sha: str
    commit_url: str
    owner: User

    merge_request_id: str | None
    merge_request_url: str | None

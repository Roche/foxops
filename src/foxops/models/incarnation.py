from typing import Mapping

from pydantic import BaseModel, ConfigDict, Field

from foxops.engine.models import TemplateDataValue
from foxops.hosters import ReconciliationStatus
from foxops.hosters.types import MergeRequestStatus


class Incarnation(BaseModel):
    """An Incarnation represents a single incarnation instance in the inventory."""

    id: int
    incarnation_repository: str
    target_directory: str
    template_repository: str | None
    commit_sha: str
    merge_request_id: str | None

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


class IncarnationWithDetails(IncarnationBasic):
    status: ReconciliationStatus = Field(description="DEPRECATED. Use the 'merge_request_status' field instead.")
    merge_request_status: MergeRequestStatus | None

    template_repository: str | None
    template_repository_version: str | None
    template_repository_version_hash: str | None
    template_data: Mapping[str, TemplateDataValue] | None

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel

from foxops.engine.models import TemplateDataValue
from foxops.hosters import ReconciliationStatus


class Incarnation(BaseModel):
    """An Incarnation represents a single incarnation instance in the inventory."""

    id: int
    incarnation_repository: str
    target_directory: str
    commit_sha: str
    merge_request_id: str | None

    class Config:
        orm_mode = True


class IncarnationBasic(BaseModel):
    id: int
    incarnation_repository: str
    target_directory: str
    commit_url: str
    merge_request_url: str | None

    class Config:
        orm_mode = True


class IncarnationWithDetails(IncarnationBasic):
    status: ReconciliationStatus

    template_repository: str | None
    template_repository_version: str | None
    template_repository_version_hash: str | None
    template_data: dict[str, TemplateDataValue] | None

    class Config:
        orm_mode = True

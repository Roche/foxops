from pydantic import BaseModel

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

    class Config:
        orm_mode = True


class IncarnationWithDetails(IncarnationBasic):
    status: ReconciliationStatus

    class Config:
        orm_mode = True

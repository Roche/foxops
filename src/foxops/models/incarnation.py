from pydantic import BaseModel


class Incarnation(BaseModel):
    """An Incarnation represents a single incarnation instance in the inventory."""

    id: int
    incarnation_repository: str
    target_directory: str
    status: str
    revision: str | None

    class Config:
        orm_mode = True

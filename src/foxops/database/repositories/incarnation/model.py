from pydantic import BaseModel


class IncarnationInDB(BaseModel):
    id: int
    incarnation_repository: str
    target_directory: str
    template_repository: str

    class Config:
        orm_mode = True

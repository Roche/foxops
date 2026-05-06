from pydantic import BaseModel, ConfigDict


class IncarnationInDB(BaseModel):
    id: int
    incarnation_repository: str
    target_directory: str
    template_repository: str
    auto_update_interval_seconds: int
    model_config = ConfigDict(from_attributes=True)

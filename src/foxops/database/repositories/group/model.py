from pydantic import BaseModel, ConfigDict


class GroupInDB(BaseModel):
    id: int
    system_name: str
    display_name: str
    model_config = ConfigDict(from_attributes=True)

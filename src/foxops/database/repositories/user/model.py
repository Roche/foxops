from pydantic import BaseModel, ConfigDict


class UserInDB(BaseModel):
    id: int
    username: str
    is_admin: bool
    model_config = ConfigDict(from_attributes=True)

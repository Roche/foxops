from pydantic import BaseModel


class ApiError(BaseModel):
    message: str

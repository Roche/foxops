from pydantic import BaseModel


class ApiError(BaseModel):
    message: str
    documentation: str | None = None

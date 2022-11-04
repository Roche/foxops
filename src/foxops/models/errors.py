from pydantic import BaseModel


class ApiError(BaseModel):
    message: str


class AuthError(BaseModel):
    detail: str

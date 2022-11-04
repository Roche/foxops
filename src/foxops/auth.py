from typing import ClassVar, Optional

from aiocache import Cache  # type: ignore
from fastapi import Depends, Header, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel, EmailStr, SecretStr, ValidationError

from foxops.jwt import (
    JWTError,
    JWTSettings,
    JWTTokenData,
    decode_jwt_token,
    get_jwt_settings,
)
from foxops.models import User


class AuthHTTPException(HTTPException):
    """Authorization HTTP exception"""

    def __init__(self, **kwargs):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Bearer"}, **kwargs)


class AuthData(BaseModel):
    """This class represent the authorization data.
    It contains the user information (out of oidc, minimum email_address)
    and host access token (auth & refresh)
    Data is cached locally, user email address is used as key
    It is necessary to avoid exposing hoster token
    """

    cache: ClassVar[Optional[Cache]] = None

    user: User
    hoster_token: Optional[SecretStr] = None
    refresh_token: Optional[SecretStr] = None

    @classmethod
    def initialize(cls, cache: Cache) -> Cache:
        cls.cache = cache
        return cls.cache

    @classmethod
    async def register(cls, data: "AuthData") -> Optional["AuthData"]:
        ret = None
        if cls.cache:
            ret = await cls.cache.set(data.user.email, data)  # type: ignore
        return ret

    @classmethod
    async def get(cls, user: User) -> Optional["AuthData"]:
        data = None
        if cls.cache:
            data = await cls.cache.get(user.email)  # type: ignore
        return data


async def get_auth_data(
    *,
    authorization: str = Header(None, include_in_schema=False),
    jwt_settings: JWTSettings = Depends(get_jwt_settings),
) -> AuthData:
    """extracts user email from JWT token and use it as key to get authorization data"""
    if not authorization:
        raise AuthHTTPException(detail="Missing Authorization header")
    scheme, token = get_authorization_scheme_param(authorization)
    if scheme.lower() != "bearer":
        raise AuthHTTPException(detail="Token scheme must be Bearer")
    if token == "":
        raise AuthHTTPException(detail="Missing token")
    try:
        token_data: Optional[JWTTokenData] = decode_jwt_token(jwt_settings, token)
        if not token_data:
            raise AuthHTTPException(detail="Unable to decode jwt token")
        auth_data: Optional[AuthData] = await AuthData.get(User(email=EmailStr(token_data.sub)))
    except (ValidationError, JWTError) as e:
        raise AuthHTTPException(detail=f"{e}")

    if not auth_data:
        raise AuthHTTPException(detail=f"User {token_data.sub} not found")

    return auth_data

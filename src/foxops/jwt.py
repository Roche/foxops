import secrets
from datetime import datetime, timedelta
from functools import cache
from typing import Any, List, Optional, Union

from jose import jwt  # type: ignore
from jose.exceptions import JWTError as JWTError  # type: ignore # noqa: F401
from pydantic import BaseModel, BaseSettings, SecretStr


class JWTSettings(BaseSettings):
    """JWT token specific settings"""

    secret_key: SecretStr = SecretStr(secrets.token_hex(32))
    algorithm: str = "HS256"
    token_expire: int = 100  # 100min - a bit less than hoster(Gitlab) token expiration (7200s=120min)

    class Config:
        env_prefix = "foxops_jwt_"
        secrets_dir = "/var/run/secrets/foxops"


@cache
def get_jwt_settings() -> JWTSettings:
    return JWTSettings()  # type: ignore


class JWTTokenData(BaseModel):
    """JWT token model"""

    sub: str
    scopes: List[str] = []


def create_jwt_token(
    settings: JWTSettings, data: JWTTokenData, expiration: Union[datetime, timedelta, None] = None
) -> str:
    """returns encoded JWT token"""
    to_encode: dict = data.dict().copy()
    if expiration:
        if isinstance(expiration, datetime):
            expire: datetime = expiration
        elif isinstance(expiration, timedelta):
            expire = datetime.utcnow() + expiration
        else:  # should not be there
            raise ValueError("wrong data type for expiration")
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.token_expire)
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, settings.secret_key.get_secret_value(), settings.algorithm)
    return encoded_jwt


def decode_jwt_token(settings: JWTSettings, token: str) -> Optional[JWTTokenData]:
    """decodes JWT token. Signature is verified"""
    payload: dict[str, Any] = jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=[settings.algorithm])
    return JWTTokenData(**payload)

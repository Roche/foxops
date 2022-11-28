from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import SecurityScopes
from fastapi.security.api_key import APIKeyHeader
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

import foxops.reconciliation as reconciliation
from foxops.auth import AuthData, AuthHTTPException, get_auth_data
from foxops.database import DAL
from foxops.hosters import Hoster, HosterSettings
from foxops.hosters.gitlab import (
    GitLab,
    GitLabSettings,
    get_gitlab_auth_router,
    get_gitlab_settings,
)
from foxops.models import User
from foxops.settings import DatabaseSettings, Settings

# NOTE: Yes, you may absolutely use proper dependency injection at some point.

#: Holds a singleton of the database engine
async_engine: AsyncEngine | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore


@lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()


@lru_cache
def get_hoster_settings() -> HosterSettings:
    return GitLabSettings()  # type: ignore


def get_dal(settings: DatabaseSettings = Depends(get_database_settings)) -> DAL:
    global async_engine

    if async_engine is None:
        async_engine = create_async_engine(settings.url.get_secret_value(), future=True, echo=False, pool_pre_ping=True)

    return DAL(async_engine)


async def get_hoster_token(*, auth_data: AuthData = Depends(get_auth_data)) -> Optional[SecretStr]:
    """returns hoster authoization token"""
    return auth_data.hoster_token


def get_hoster(
    *,
    settings: HosterSettings = Depends(get_gitlab_settings),
    hoster_token: SecretStr = Depends(get_hoster_token),
) -> Hoster:
    # this assert makes mypy happy
    assert isinstance(settings, GitLabSettings)
    return GitLab(settings, hoster_token)


async def get_current_user(
    *, security_scopes: SecurityScopes, auth_data: AuthData = Depends(get_auth_data)
) -> Optional[User]:
    """current user - check if she has enough permissions (scopes)"""
    user = auth_data.user
    for scope in security_scopes.scopes:
        if scope not in user.scopes:
            raise AuthHTTPException(detail=f"not enough permissions (missing scope={scope})")
    return user


def get_hoster_auth_router() -> APIRouter:
    return get_gitlab_auth_router()


def get_reconciliation():
    return reconciliation


class HosterTokenHeaderAuth(APIKeyHeader):
    def __init__(self):
        super().__init__(name="Authorization")

    async def __call__(self, request: Request) -> Optional[str]:
        authorization_header: Optional[str] = await super().__call__(request)
        if not authorization_header:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Authorization header")

        if not authorization_header.startswith("Bearer ") or not authorization_header.removeprefix("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization header must start with 'Bearer ' followed by the token",
            )
        return authorization_header


hoster_token_auth_scheme: HosterTokenHeaderAuth = HosterTokenHeaderAuth()

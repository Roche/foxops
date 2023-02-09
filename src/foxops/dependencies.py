from functools import lru_cache

from fastapi import Depends, HTTPException, Request, status
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.base import SecurityBase
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

import foxops.reconciliation as reconciliation
from foxops.database import DAL
from foxops.hosters import Hoster, HosterSettings
from foxops.hosters.gitlab import GitLab, GitLabSettings, get_gitlab_settings
from foxops.services.change import ChangeService
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


def get_hoster(settings: HosterSettings = Depends(get_gitlab_settings)) -> Hoster:
    # this assert makes mypy happy
    assert isinstance(settings, GitLabSettings)
    return GitLab(
        address=settings.address,
        token=settings.token.get_secret_value(),
    )


def get_change_service(hoster: Hoster = Depends(get_hoster)) -> ChangeService:
    return ChangeService(hoster=hoster)


def get_reconciliation():
    return reconciliation


class StaticTokenHeaderAuth(SecurityBase):
    def __init__(self):
        self.model = APIKey(**{"in": APIKeyIn.header}, name="Authorization")
        self.scheme_name = self.__class__.__name__

    async def __call__(self, request: Request, settings: Settings = Depends(get_settings)) -> None:
        authorization_header: str | None = request.headers.get("Authorization")
        if not authorization_header:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Authorization header")

        if not authorization_header.startswith("Bearer ") or not (
            token := authorization_header.removeprefix("Bearer ")
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization header must start with 'Bearer ' followed by the token",
            )

        if settings.static_token.get_secret_value() != token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid")


static_token_auth_scheme = StaticTokenHeaderAuth()

from functools import lru_cache

from fastapi import Depends, HTTPException, Request, status
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.base import SecurityBase
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

import foxops.reconciliation as reconciliation
from foxops.database import DAL
from foxops.hosters import GitLab, Hoster
from foxops.settings import Settings

# NOTE: Yes, you may absolutely use proper dependency injection at some point.

#: Holds a singleton of the database engine
async_engine: AsyncEngine | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_dal(settings: Settings = Depends(get_settings)) -> DAL:
    global async_engine

    if async_engine is None:
        async_engine = create_async_engine(
            settings.database_url.get_secret_value(), future=True, echo=False, pool_pre_ping=True
        )

    return DAL(async_engine)


def get_hoster(settings: Settings = Depends(get_settings)) -> Hoster:
    return GitLab(
        address=settings.gitlab_address,
        token=settings.gitlab_token.get_secret_value(),
    )


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

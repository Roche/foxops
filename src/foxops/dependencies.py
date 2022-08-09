from functools import lru_cache

from fastapi import Depends
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
        async_engine = create_async_engine(settings.database_url, future=True, echo=False, pool_pre_ping=True)

    return DAL(async_engine)


def get_hoster(settings: Settings = Depends(get_settings)) -> Hoster:
    return GitLab(
        address=settings.gitlab_address,
        token=settings.gitlab_token.get_secret_value(),
    )


def get_reconciliation():
    return reconciliation

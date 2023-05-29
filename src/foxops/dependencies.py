from functools import lru_cache

from fastapi import Depends, HTTPException, Request, status
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.base import SecurityBase
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from foxops.database.repositories.change import ChangeRepository
from foxops.database.repositories.incarnation.repository import IncarnationRepository
from foxops.hosters import Hoster, HosterSettings
from foxops.hosters.gitlab import GitLab, GitLabSettings, get_gitlab_settings
from foxops.services.change import ChangeService
from foxops.services.incarnation import IncarnationService
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


def get_database_engine(settings: DatabaseSettings = Depends(get_database_settings)) -> AsyncEngine:
    global async_engine

    if async_engine is None:
        async_engine = create_async_engine(settings.url.get_secret_value(), future=True, echo=False, pool_pre_ping=True)

    return async_engine


def get_incarnation_repository(database_engine: AsyncEngine = Depends(get_database_engine)) -> IncarnationRepository:
    return IncarnationRepository(database_engine)


def get_change_repository(database_engine: AsyncEngine = Depends(get_database_engine)) -> ChangeRepository:
    return ChangeRepository(database_engine)


def get_hoster(settings: HosterSettings = Depends(get_gitlab_settings)) -> Hoster:
    # this assert makes mypy happy
    assert isinstance(settings, GitLabSettings)
    return GitLab(
        address=settings.address,
        token=settings.token.get_secret_value(),
    )


def get_incarnation_service(
    incarnation_repository: IncarnationRepository = Depends(get_incarnation_repository),
    hoster: Hoster = Depends(get_hoster),
) -> IncarnationService:
    return IncarnationService(incarnation_repository=incarnation_repository, hoster=hoster)


def get_change_service(
    hoster: Hoster = Depends(get_hoster),
    change_repository: ChangeRepository = Depends(get_change_repository),
    incarnation_repository: IncarnationRepository = Depends(get_incarnation_repository),
) -> ChangeService:
    return ChangeService(
        hoster=hoster, incarnation_repository=incarnation_repository, change_repository=change_repository
    )


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

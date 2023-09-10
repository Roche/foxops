from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.base import SecurityBase
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from foxops.database.repositories.change import ChangeRepository
from foxops.database.repositories.incarnation.repository import IncarnationRepository
from foxops.hosters import Hoster
from foxops.hosters.gitlab import GitlabHoster
from foxops.hosters.local import LocalHoster
from foxops.logger import get_logger
from foxops.services.change import ChangeService
from foxops.services.incarnation import IncarnationService
from foxops.settings import (
    DatabaseSettings,
    GitlabHosterSettings,
    HosterType,
    LocalHosterSettings,
    Settings,
)

logger = get_logger(__name__)


def get_settings() -> Settings:
    return Settings()  # type: ignore


def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()


######
# Global Dependencies (those that are only created once and then cached for later requests)
######


def get_database_engine(request: Request, settings: DatabaseSettings = Depends(get_database_settings)) -> AsyncEngine:
    if hasattr(request.app.state, "database"):
        return request.app.state.database

    async_engine = create_async_engine(settings.url.get_secret_value(), future=True, echo=False, pool_pre_ping=True)

    request.app.state.database = async_engine
    return async_engine


def get_hoster(request: Request, settings: Annotated[Settings, Depends(get_settings)]) -> Hoster:
    if hasattr(request.app.state, "hoster"):
        return request.app.state.hoster

    hoster: Hoster
    match settings.hoster_type:
        case HosterType.LOCAL:
            local_settings = LocalHosterSettings()

            logger.warning(
                "Using local hoster. This is for DEVELOPMENT use only!", directory=str(local_settings.directory)
            )

            hoster = LocalHoster(local_settings.directory)
        case HosterType.GITLAB:
            gitlab_settings = GitlabHosterSettings()
            logger.info("Using GitLab hoster", address=gitlab_settings.address)

            hoster = GitlabHoster(gitlab_settings.address, gitlab_settings.token.get_secret_value())
        case _:
            raise NotImplementedError(f"Unknown hoster type {settings.hoster_type}")

    request.app.state.hoster = hoster
    return hoster


######
# Per-Request Dependencies
######


def get_incarnation_repository(database_engine: AsyncEngine = Depends(get_database_engine)) -> IncarnationRepository:
    return IncarnationRepository(database_engine)


def get_change_repository(database_engine: AsyncEngine = Depends(get_database_engine)) -> ChangeRepository:
    return ChangeRepository(database_engine)


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

import re
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.base import SecurityBase
from sqlalchemy.ext.asyncio import AsyncEngine

from foxops.database.engine import create_engine
from foxops.database.repositories.change.repository import ChangeRepository
from foxops.database.repositories.group.errors import GroupNotFoundError
from foxops.database.repositories.group.repository import GroupRepository
from foxops.database.repositories.incarnation.repository import IncarnationRepository
from foxops.database.repositories.user.errors import UserNotFoundError
from foxops.database.repositories.user.repository import UserRepository
from foxops.hosters import Hoster
from foxops.hosters.gitlab import GitlabHoster
from foxops.hosters.local import LocalHoster
from foxops.logger import get_logger
from foxops.models.group import Group
from foxops.models.user import User, UserWithGroups
from foxops.services.authorization import AuthorizationService
from foxops.services.change import ChangeService
from foxops.services.group import GroupService
from foxops.services.incarnation import IncarnationService
from foxops.services.user import UserService
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

    async_engine = create_engine(settings.url.get_secret_value())

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


def get_user_repository(database_engine: AsyncEngine = Depends(get_database_engine)) -> UserRepository:
    return UserRepository(database_engine)


def get_group_repository(database_engine: AsyncEngine = Depends(get_database_engine)) -> GroupRepository:
    return GroupRepository(database_engine)


def get_group_service(
    group_repository: GroupRepository = Depends(get_group_repository),
    user_repository: UserRepository = Depends(get_user_repository),
) -> GroupService:
    return GroupService(group_repository=group_repository, user_repository=user_repository)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    group_repository: GroupRepository = Depends(get_group_repository),
) -> UserService:
    return UserService(user_repository=user_repository, group_repository=group_repository)


def get_incarnation_service(
    incarnation_repository: IncarnationRepository = Depends(get_incarnation_repository),
    hoster: Hoster = Depends(get_hoster),
    user_repository: UserRepository = Depends(get_user_repository),
    group_repository: GroupRepository = Depends(get_group_repository),
) -> IncarnationService:
    return IncarnationService(
        incarnation_repository=incarnation_repository,
        hoster=hoster,
        user_repository=user_repository,
        group_repository=group_repository,
    )


def get_change_service(
    hoster: Hoster = Depends(get_hoster),
    change_repository: ChangeRepository = Depends(get_change_repository),
    incarnation_repository: IncarnationRepository = Depends(get_incarnation_repository),
    user_repository: UserRepository = Depends(get_user_repository),
) -> ChangeService:
    return ChangeService(
        hoster=hoster,
        incarnation_repository=incarnation_repository,
        change_repository=change_repository,
        user_repository=user_repository,
    )


class StaticTokenHeaderAuth(SecurityBase):
    def __init__(self):
        self.model = APIKey(
            **{
                "in": APIKeyIn.header,
                "description": (
                    "The static token for authentication. This field is required for all endpoints which require authentication. "
                    "It has to be provided in the format `Bearer <token>`."
                ),
            },
            name="Authorization",
        )
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


class UserHeaderAuth(SecurityBase):
    def __init__(self):
        self.model = APIKey(
            **{
                "in": APIKeyIn.header,
                "description": (
                    "The Username of the current user. This field is required for all endpoints which require authentication."
                ),
            },
            name="User",
        )
        self.scheme_name = self.__class__.__name__

    async def __call__(self) -> None:
        # This class only defines the scheme, the actual validation is done in the GroupHeaderAuth class.
        pass


class GroupHeaderAuth(SecurityBase):
    def __init__(self):
        self.model = APIKey(
            **{
                "in": APIKeyIn.header,
                "description": (
                    "The Groups of the current user. Multiple groups can be specified by separating them with commas. "
                    "This field is optional and may be empty. "
                    "The groupname must be alphanumeric and may contain underscores, colons and dashes. "
                    "The groupname **is** case sensitive."
                ),
            },
            name="Groups",
        )
        self.scheme_name = self.__class__.__name__

    async def get_user(self, user_header: str | None, user_service: UserService) -> User:
        if not user_header:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing User header")

        try:
            return await user_service.get_user_by_username(user_header)

        except UserNotFoundError:
            return await user_service.create_user(username=user_header)

    async def get_groups(self, group_header: str | None, group_service: GroupService) -> list[Group]:
        if not group_header or group_header.strip() == "":
            # Group header is optional. So it could also be empty/non existing
            return []

        groups = []

        for group in group_header.split(","):
            group = group.strip()

            if not re.match(r"^[a-zA-Z0-9_\-:]+$", group):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Group names must be alphanumeric and may contain underscores and dashes",
                )

            try:
                groups.append(await group_service.get_group_by_system_name(group))
            except GroupNotFoundError:
                groups.append(await group_service.create_group(system_name=group, display_name=group))

        return groups

    async def user_join_groups(self, user: User, groups: list[Group], user_service: UserService) -> None:
        await user_service.join_groups(user.username, [group.id for group in groups], remove_old_ref=True)

    async def __call__(
        self,
        request: Request,
        group_service: GroupService = Depends(get_group_service),
        user_service: UserService = Depends(get_user_service),
    ) -> UserWithGroups:
        user_header: str | None = request.headers.get("User")

        user = await self.get_user(user_header, user_service)

        group_header: str | None = request.headers.get("Groups")

        groups = await self.get_groups(group_header, group_service)

        if len(groups) > 0:
            await self.user_join_groups(user, groups, user_service)
        else:
            await user_service.remove_all_groups_from_user(user.id)

        return UserWithGroups(groups=groups, **user.model_dump())


static_token_auth_scheme = StaticTokenHeaderAuth()
user_auth_scheme = UserHeaderAuth()
group_auth_scheme = GroupHeaderAuth()


def authorization(
    _static_token: None = Depends(static_token_auth_scheme),
    _user_schema: None = Depends(user_auth_scheme),
    current_user: UserWithGroups = Depends(group_auth_scheme),
) -> AuthorizationService:
    return AuthorizationService(current_user=current_user)

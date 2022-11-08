from functools import cache
from typing import Dict, Optional

from authlib.integrations.starlette_client import OAuth, OAuthError  # type: ignore
from authlib.oidc.core.claims import UserInfo  # type: ignore
from fastapi import APIRouter, Depends, Request
from pydantic import AnyUrl, ValidationError
from starlette.responses import RedirectResponse

from foxops.auth import AuthData, AuthHTTPException
from foxops.jwt import JWTTokenData, create_jwt_token, get_jwt_settings
from foxops.logger import get_logger
from foxops.models import User

from .settings import GitLabSettings, get_gitlab_settings

#: Holds the module logger
logger = get_logger(__name__)

#: Holds the router for the gitlab authentication endpoints
router = APIRouter()

#: Hold static OAuth registry instance
oauth = OAuth()


def get_oauth_gitlab(settings: GitLabSettings = Depends(get_gitlab_settings)):
    """returns the Gitlab authlib client, configured from oidc well-known.
    The function depends on *Gitlab settings*
    authlib is caching the object is a registry, object is created at first call
    """
    conf_url = f"{settings.address}/.well-known/openid-configuration"
    # object is cached in OAuth registry
    return oauth.register(
        name="gitlab",
        server_metadata_url=conf_url,
        client_id=settings.client_id,
        client_secret=settings.client_secret.get_secret_value(),
        client_kwargs={"scope": settings.client_scope},
    )


@router.get("/login")
async def login(
    request: Request,
    redirect_uri: Optional[AnyUrl] = None,
    gitlab=Depends(get_oauth_gitlab),
) -> RedirectResponse:
    """Redirects to hoster login page.
    *redirect_uri* is the uri called back with authorization code when user is authenticated,
    if empty it will use */token*
    """
    redir: str = request.url_for("token")
    if redirect_uri:
        redir = str(redirect_uri)
    return await gitlab.authorize_redirect(request, redir)  # type: ignore


@router.get("/token")
async def token(
    request: Request,
    code: str,  # not used but here for proper openapi documentation
    state: str,  # idem
    gitlab=Depends(get_oauth_gitlab),
    jwt_settings=Depends(get_jwt_settings),
) -> str:
    """Generates JWT token to be used by fronted for authorization.
    This route is called back by hoster authentication page.
    *code* is used to request an access token for this user
    """
    try:
        # we get access token from hoster, it provides authorization & refresh token
        access_token: Dict = await gitlab.authorize_access_token(request)  # type: ignore
        # gather user info from oidc endpoint
        user_info: UserInfo = await gitlab.userinfo(token=access_token)
        user = User(**user_info)
        # TODO: get scopes from database?
        # scopes is foxops specific - TBD
        user.scopes = ["user"]
        # we cache hoster token in AuthData registry
        # we cannot afford to expose the access token in the JWT token (JWT token is not encrypted)
        await AuthData.register(
            AuthData(user=user, hoster_token=access_token["access_token"], refresh_token=access_token["refresh_token"])
        )
    except (OAuthError, ValidationError) as e:
        raise AuthHTTPException(detail=f"{e}")

    # we generate a JWT token for the frontend
    # user_email is used as key for the cache
    data = JWTTokenData(sub=user.email, scopes=user.scopes)
    return create_jwt_token(settings=jwt_settings, data=data)


@cache
def get_gitlab_auth_router() -> APIRouter:
    """returns Gitlab authentication routes."""
    return router

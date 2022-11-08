from fastapi import APIRouter, Depends, Security
from fastapi.responses import PlainTextResponse

from foxops.dependencies import (
    get_current_user,
    get_hoster_auth_router,
    get_hoster_token,
)

#: Holds the router for the version endpoint
router = APIRouter(prefix="/auth", tags=["authentication"])

# here we include the hoster authentication router, will use /auth prefix
router.include_router(get_hoster_auth_router())


@router.get(
    "/test", response_class=PlainTextResponse, dependencies=[Depends(get_hoster_token), Security(get_current_user)]
)
def test_authentication_route():
    return "OK"

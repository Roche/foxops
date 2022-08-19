from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from foxops.dependencies import static_token_auth_scheme

#: Holds the router for the version endpoint
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/test", response_class=PlainTextResponse, dependencies=[Depends(static_token_auth_scheme)])
def test_authentication_route():
    return "OK"

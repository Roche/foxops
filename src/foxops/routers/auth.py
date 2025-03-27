from fastapi import APIRouter, Depends

from foxops.dependencies import authorization
from foxops.models.user import UserWithGroups
from foxops.services.authorization import AuthorizationService

#: Holds the router for the version endpoint
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/test")
def test_authentication_route(authorization_service: AuthorizationService = Depends(authorization)) -> UserWithGroups:
    return authorization_service.current_user

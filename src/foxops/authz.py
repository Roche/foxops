from fastapi import Depends

from foxops.dependencies import authorization, get_incarnation_service
from foxops.errors import ResourceForbiddenError
from foxops.services.authorization import AuthorizationService
from foxops.services.incarnation import IncarnationService


async def read_access_on_incarnation(
    incarnation_id: int,
    authorization_service: AuthorizationService = Depends(authorization),
    incarnation_service: IncarnationService = Depends(get_incarnation_service),
) -> None:
    permissions = await incarnation_service.get_permissions(incarnation_id)

    if not authorization_service.has_read_access(permissions):
        raise ResourceForbiddenError


async def write_access_on_incarnation(
    incarnation_id: int,
    authorization_service: AuthorizationService = Depends(authorization),
    incarnation_service: IncarnationService = Depends(get_incarnation_service),
) -> None:
    permissions = await incarnation_service.get_permissions(incarnation_id)

    if not authorization_service.has_write_access(permissions):
        raise ResourceForbiddenError

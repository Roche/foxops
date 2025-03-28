from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel

from foxops.authz import access_to_admin_only
from foxops.dependencies import authorization, get_user_service
from foxops.models.errors import ApiError
from foxops.models.user import User, UserWithGroups
from foxops.services.authorization import AuthorizationService
from foxops.services.user import UserService

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get(
    "",
    dependencies=[Depends(access_to_admin_only)],
    responses={
        status.HTTP_200_OK: {
            "description": "List of users",
            "model": list[User],
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "You exceeded the number of pages",
            "model": ApiError,
        },
    },
)
async def list_users(
    response: Response,
    user_service: UserService = Depends(get_user_service),
    limit: int = Query(25, ge=1, le=200, description="Number of users to return"),
    page: int = Query(1, ge=1, description="Page number"),
):
    users = await user_service.list_users_paginated(limit, page)

    # There is not case, where 0 users exist in the db, since at least
    # the user, who is calling the api, has to exist.
    if len(users) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ApiError(
            message="You exceeded the number of pages",
        )

    return users


@router.get(
    "/{user_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "User information",
            "model": UserWithGroups,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User not found",
            "model": ApiError,
        },
    },
    dependencies=[Depends(access_to_admin_only)],
)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    resolve_groups: bool = Query(False, description="Resolve the groups of the user"),
):
    if resolve_groups:
        return await user_service.get_user_by_id_with_groups(user_id)

    return await user_service.get_user_by_id(user_id)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "User deleted",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "You can't delete yourself",
            "model": ApiError,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User not found",
            "model": ApiError,
        },
        status.HTTP_409_CONFLICT: {
            "description": "User is still owner of some resources",
            "model": ApiError,
        },
    },
    dependencies=[Depends(access_to_admin_only)],
)
async def delete_user(
    user_id: int,
    response: Response,
    user_service: UserService = Depends(get_user_service),
    authorization_service: AuthorizationService = Depends(authorization),
):
    if authorization_service.id == user_id:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ApiError(message="You can't delete yourself")

    await user_service.delete_user(user_id)


class UserPatchRequest(BaseModel):
    is_admin: bool


@router.patch(
    "/{user_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "User information",
            "model": UserWithGroups,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "You can't change your own admin status",
            "model": ApiError,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User not found",
            "model": ApiError,
        },
    },
    dependencies=[Depends(access_to_admin_only)],
)
async def update_user(
    response: Response,
    user_id: int,
    request: UserPatchRequest,
    user_service: UserService = Depends(get_user_service),
    authorization_service: AuthorizationService = Depends(authorization),
):
    if authorization_service.id == user_id:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ApiError(message="You can't change your own admin status")

    return await user_service.set_is_admin(user_id, request.is_admin)

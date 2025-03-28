from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel

from foxops.authz import access_to_admin_only
from foxops.dependencies import get_group_service
from foxops.models.errors import ApiError
from foxops.models.group import Group
from foxops.models.user import GroupWithUsers
from foxops.services.group import GroupService

router = APIRouter(prefix="/api/group", tags=["group"])


@router.get(
    "",
    responses={
        status.HTTP_200_OK: {
            "description": "List of groups",
            "model": list[Group],
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "You exceeded the number of pages",
            "model": ApiError,
        },
    },
    dependencies=[Depends(access_to_admin_only)],
)
async def list_groups(
    response: Response,
    group_service: GroupService = Depends(get_group_service),
    limit: int = Query(25, ge=1, le=200, description="Number of groups to return"),
    page: int = Query(1, ge=1, description="Page number"),
):
    groups = await group_service.list_groups_paginated(limit, page)

    # It is possible, that 0 groups exist in the db.
    # So we don't return a 400 if the user is on the first page
    if len(groups) == 0 and page > 1:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ApiError(
            message="You exceeded the number of pages",
        )

    return groups


@router.get(
    "/{group_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "Group information",
            "model": GroupWithUsers,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Group not found",
            "model": ApiError,
        },
    },
    dependencies=[Depends(access_to_admin_only)],
)
async def get_group(
    group_id: int,
    group_service: GroupService = Depends(get_group_service),
    resolve_users: bool = Query(False, description="Resolve the users of the group"),
):
    if resolve_users:
        return await group_service.get_group_by_id_with_users(group_id)

    return await group_service.get_group_by_id(group_id)


@router.delete(
    "/{group_id}",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Group deleted",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Group not found",
            "model": ApiError,
        },
    },
    dependencies=[Depends(access_to_admin_only)],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_group(
    group_id: int,
    group_service: GroupService = Depends(get_group_service),
):
    await group_service.delete_group(group_id)


class GroupPatchRequest(BaseModel):
    display_name: str


@router.patch(
    "/{group_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "Group information",
            "model": Group,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Group not found",
            "model": ApiError,
        },
    },
    dependencies=[Depends(access_to_admin_only)],
)
async def patch_group(
    group_id: int,
    request: GroupPatchRequest,
    group_service: GroupService = Depends(get_group_service),
):
    return await group_service.set_display_name(group_id, request.display_name)

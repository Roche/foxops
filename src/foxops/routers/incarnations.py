from typing import Self

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, model_validator

from foxops.authz import read_access_on_incarnation, write_access_on_incarnation
from foxops.dependencies import (
    authorization,
    get_change_service,
    get_hoster,
    get_incarnation_service,
)
from foxops.engine import TemplateData
from foxops.engine.errors import ProvidedTemplateDataInvalidError
from foxops.errors import GeneralForbiddenError
from foxops.errors import IncarnationNotFoundError as IncarnationNotFoundLegacyError
from foxops.hosters import Hoster
from foxops.logger import bind, get_logger
from foxops.models import IncarnationWithDetails
from foxops.models.errors import ApiError
from foxops.models.incarnation import (
    IncarnationWithLatestChangeDetails,
    UnresolvedGroupPermissions,
    UnresolvedUserPermissions,
)
from foxops.routers import changes
from foxops.services.authorization import AuthorizationService
from foxops.services.change import (
    ChangeRejectedDueToNoChanges,
    ChangeRejectedDueToPreviousUnfinishedChange,
    ChangeService,
    IncarnationAlreadyExists,
)
from foxops.services.incarnation import IncarnationService

#: Holds the router for the incarnations API endpoints
router = APIRouter(prefix="/api/incarnations", tags=["incarnations"])
router.include_router(changes.router, prefix="/{incarnation_id}/changes", tags=["changes"])

#: Holds the logger for these routes
logger = get_logger(__name__)


class IncarnationWithPermissions(IncarnationWithDetails):
    current_user_permissions: dict[str, bool]


@router.get(
    "",
    responses={
        status.HTTP_200_OK: {
            "description": "The list of incarnations in the inventory",
            "model": list[IncarnationWithLatestChangeDetails],
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "The `incarnation_repository` and `target_directory` settings where inconsistent",
            "model": ApiError,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "An incarnation with the `incarnation_repository` and `target_directory` does not exist",
            "model": ApiError,
        },
    },
)
async def list_incarnations(
    response: Response,
    incarnation_repository: str | None = None,
    target_directory: str = ".",
    change_service: ChangeService = Depends(get_change_service),
    incarnation_service: IncarnationService = Depends(get_incarnation_service),
    authorization_service: AuthorizationService = Depends(authorization),
):
    """Returns a list of all known incarnations.

    The list is sorted by incarnartion ID, with the oldest incarnation first.

    TODO: implement pagination
    """
    if incarnation_repository is None and authorization_service.admin:
        return await change_service.list_incarnations()
    elif incarnation_repository is None:
        return await change_service.list_incarnations_with_user_access(authorization_service.current_user)

    try:
        incarnation = await change_service.get_incarnation_by_repo_and_target_directory(
            incarnation_repository, target_directory
        )

    except IncarnationNotFoundLegacyError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ApiError(message="No incarnation found for the given repository and target directory")

    permissions = await incarnation_service.get_permissions(incarnation.id)

    if authorization_service.has_read_access(permissions):
        return [incarnation]

    # We don't want to leak metadata to prevent side channel attacks
    return ApiError(message="No incarnation found for the given repository and target directory")


class CreateIncarnationRequest(BaseModel):
    incarnation_repository: str
    target_directory: str = "."

    template_repository: str
    template_repository_version: str

    template_data: TemplateData


@router.post(
    "",
    responses={
        status.HTTP_201_CREATED: {
            "description": "The incarnation has been successfully initialized and was added to the inventory.",
            "model": IncarnationWithDetails,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "The desired incarnation state is invalid",
            "model": ApiError,
        },
        status.HTTP_409_CONFLICT: {
            "description": "There is already a foxops incarnation with the same repository and target directory",
            "model": ApiError,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "The reconciliation failed",
            "model": ApiError,
        },
    },
    status_code=status.HTTP_201_CREATED,
)
async def create_incarnation(
    response: Response,
    request: CreateIncarnationRequest,
    change_service: ChangeService = Depends(get_change_service),
    authorization_serive: AuthorizationService = Depends(authorization),
):
    """Initializes a new incarnation and adds it to the inventory.

    If the initialization fails, foxops will return the error in a `4xx` or `5xx` status code response.
    """
    bind(incarnation_repository=request.incarnation_repository)
    bind(target_directory=request.target_directory)

    template_data = request.template_data or {}

    try:
        change = await change_service.create_incarnation(
            incarnation_repository=request.incarnation_repository,
            target_directory=request.target_directory,
            template_repository=request.template_repository,
            template_repository_version=request.template_repository_version,
            template_data=template_data,
            owner_id=authorization_serive.current_user.id,
        )
    except ProvidedTemplateDataInvalidError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        error_messages = e.get_readable_error_messages()
        return ApiError(
            message=f"could not initialize the incarnation as the provided template data "
            f"is invalid: {'; '.join(error_messages)}"
        )
    except IncarnationAlreadyExists:
        response.status_code = status.HTTP_409_CONFLICT
        return ApiError(
            message=(
                f"There is already a foxops incarnation at {request.incarnation_repository} "
                f"with target directory {request.target_directory}"
            )
        )

    response.status_code = status.HTTP_201_CREATED
    return await change_service.get_incarnation_with_details(change.incarnation_id)


@router.get(
    "/{incarnation_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "The actual state of the incarnation from the inventory",
            "model": IncarnationWithDetails,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The incarnation was not found in the inventory",
            "model": ApiError,
        },
    },
    dependencies=[Depends(read_access_on_incarnation)],
)
async def read_incarnation(
    incarnation_id: int,
    show_permissions: bool = False,
    change_service: ChangeService = Depends(get_change_service),
    authorization_service: AuthorizationService = Depends(authorization),
):
    """Returns the details of the incarnation from the inventory."""
    incarnation = await change_service.get_incarnation_with_details(incarnation_id)

    if not show_permissions:
        return incarnation

    can_write = authorization_service.has_write_access(incarnation)

    return IncarnationWithPermissions(
        **incarnation.model_dump(),
        current_user_permissions={
            "can_read": True,
            "can_update": can_write,
            "can_delete": can_write,
            "can_reset": can_write,
        },
    )


class IncarnationResetRequest(BaseModel):
    requested_version: str
    requested_data: TemplateData


class IncarnationResetResponse(BaseModel):
    incarnation_id: int
    merge_request_id: str
    merge_request_url: str


@router.post(
    "/{incarnation_id}/reset",
    responses={
        status.HTTP_200_OK: {
            "description": "The incarnation was successfully reset",
            "model": IncarnationResetResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The incarnation was not found in the inventory",
            "model": ApiError,
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "The incarnation does not have any customizations and there is nothing to reset",
            "model": ApiError,
        },
    },
    dependencies=[Depends(write_access_on_incarnation)],
)
async def reset_incarnation(
    incarnation_id: int,
    response: Response,
    request: IncarnationResetRequest,
    incarnation_service: IncarnationService = Depends(get_incarnation_service),
    change_service: ChangeService = Depends(get_change_service),
    hoster: Hoster = Depends(get_hoster),
    authorization_service: AuthorizationService = Depends(authorization),
):
    try:
        change = await change_service.reset_incarnation(
            incarnation_id,
            request.requested_version,
            request.requested_data,
            initialized_by=authorization_service.current_user.id,
        )
    except ProvidedTemplateDataInvalidError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        error_messages = e.get_readable_error_messages()
        return ApiError(
            message=f"could not initialize the incarnation as the provided template data "
            f"is invalid: {'; '.join(error_messages)}"
        )
    except ChangeRejectedDueToNoChanges:
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return ApiError(message="The incarnation does not have any customizations. Nothing to reset.")

    incarnation = await incarnation_service.get_by_id(incarnation_id)
    return IncarnationResetResponse(
        incarnation_id=incarnation_id,
        merge_request_id=change.merge_request_id,
        merge_request_url=await hoster.get_merge_request_url(
            incarnation.incarnation_repository, change.merge_request_id
        ),
    )


async def _create_change(
    incarnation_id: int,
    requested_version: str | None,
    requested_data: TemplateData,
    automerge: bool,
    patch: bool,
    response: Response,
    change_service: ChangeService,
    initialized_by: int,
) -> IncarnationWithDetails | ApiError:
    try:
        await change_service.create_change_merge_request(
            incarnation_id=incarnation_id,
            requested_version=requested_version,
            requested_data=requested_data,
            automerge=automerge,
            patch=patch,
            initialized_by=initialized_by,
        )
    except ProvidedTemplateDataInvalidError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        error_messages = e.get_readable_error_messages()
        return ApiError(
            message=f"could not initialize the incarnation as the provided template data "
            f"is invalid: {'; '.join(error_messages)}"
        )
    except ChangeRejectedDueToPreviousUnfinishedChange:
        response.status_code = status.HTTP_409_CONFLICT
        return ApiError(message="There is a previous change that is still open. Please merge/close it first.")
    except ChangeRejectedDueToNoChanges:
        logger.info(
            "A change was requested, but there were no changes to apply",
            incarnation_id=incarnation_id,
            requested_version=requested_version,
            requested_data=requested_data,
        )

    return await change_service.get_incarnation_with_details(incarnation_id)


class UpdateIncarnationRequest(BaseModel):
    """A DesiredIncarnationStatePatch represents the patch for the desired state of an incarnation."""

    template_repository_version: str
    template_data: TemplateData
    owner_id: int

    user_permissions: list[UnresolvedUserPermissions]
    group_permissions: list[UnresolvedGroupPermissions]

    automerge: bool


@router.put(
    "/{incarnation_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "The incarnation was successfully updated",
            "model": IncarnationWithDetails,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "The desired incarnation state was not valid",
            "model": ApiError,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The incarnation was not found in the inventory",
            "model": ApiError,
        },
        status.HTTP_409_CONFLICT: {
            "description": "The incarnation already has a change in progress",
            "model": ApiError,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "The update failed",
            "model": ApiError,
        },
    },
    dependencies=[Depends(write_access_on_incarnation)],
)
async def update_incarnation(
    response: Response,
    incarnation_id: int,
    request: UpdateIncarnationRequest,
    change_service: ChangeService = Depends(get_change_service),
    incarnation_service: IncarnationService = Depends(get_incarnation_service),
    authorization_serive: AuthorizationService = Depends(authorization),
):
    """Updates the incarnation to the given version and data.

    The provided version and template data must represent the full desired target state of the incarnation.
    If you only want to do surgical patches (e.g. updating a single variable or bump the template version while
    reusing the previously set variable values), use the PATCH endpoint instead.
    """

    old_incarnation = await incarnation_service.get_by_id(incarnation_id)

    await incarnation_service.remove_all_permissions(incarnation_id)
    await incarnation_service.set_user_permissions(incarnation_id, request.user_permissions)

    await incarnation_service.set_group_permissions(incarnation_id, request.group_permissions)

    if old_incarnation.owner.id != request.owner_id:
        if authorization_serive.admin or old_incarnation.owner.id == authorization_serive.id:
            await incarnation_service.set_owner(incarnation_id, request.owner_id)
        else:
            raise GeneralForbiddenError(
                "Updating the 'owner' field can only be performed by the current owner or an administator."
            )

    return await _create_change(
        incarnation_id=incarnation_id,
        requested_version=request.template_repository_version,
        requested_data=request.template_data,
        automerge=request.automerge,
        patch=False,
        response=response,
        change_service=change_service,
        initialized_by=authorization_serive.current_user.id,
    )


class PatchIncarnationRequest(BaseModel):
    """A DesiredIncarnationStatePatch represents the patch for the desired state of an incarnation."""

    requested_version: str | None = None
    requested_data: TemplateData | None = None
    user_permissions: list[UnresolvedUserPermissions] | None = None
    group_permissions: list[UnresolvedGroupPermissions] | None = None
    owner_id: int | None = None

    automerge: bool | None = None

    @model_validator(mode="after")
    def check_either_version_or_data_change_requested(self) -> Self:
        if (
            self.requested_version is None
            and self.requested_data is None
            and self.user_permissions is None
            and self.group_permissions is None
            and self.owner_id is None
        ):
            raise ValueError(
                "One of the following fields must be set: requested_version, "
                "requested_data, user_permission, group_permission, owner_id"
            )

        if (self.requested_data is not None or self.requested_version is not None) and self.automerge is None:
            raise ValueError("The 'automerge' field must be set if a change is requested")

        return self


@router.patch(
    "/{incarnation_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "The incarnation was successfully updated",
            "model": IncarnationWithDetails,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "The desired incarnation state was not valid",
            "model": ApiError,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The incarnation was not found in the inventory",
            "model": ApiError,
        },
        status.HTTP_409_CONFLICT: {
            "description": "The incarnation already has a change in progress",
            "model": ApiError,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "The update failed",
            "model": ApiError,
        },
    },
    dependencies=[Depends(write_access_on_incarnation)],
)
async def patch_incarnation(
    response: Response,
    incarnation_id: int,
    request: PatchIncarnationRequest,
    change_service: ChangeService = Depends(get_change_service),
    incarnation_service: IncarnationService = Depends(get_incarnation_service),
    authorization_serive: AuthorizationService = Depends(authorization),
):
    """Updates the incarnation to the given version and data.

    Other than the PUT endpoint, this endpoint allows to only update a subset of the incarnation state (e.g. only
    the template version (without having to respecify all template data) or only individual template data values
    """

    requested_data = request.requested_data or {}

    old_incarnation = await incarnation_service.get_by_id(incarnation_id)

    if request.group_permissions is not None:
        await incarnation_service.remove_all_group_permissions(incarnation_id)
        await incarnation_service.set_group_permissions(incarnation_id, request.group_permissions)

    if request.user_permissions is not None:
        await incarnation_service.remove_all_user_permissions(incarnation_id)
        await incarnation_service.set_user_permissions(incarnation_id, request.user_permissions)

    if request.owner_id is not None:
        if authorization_serive.admin or authorization_serive.id == old_incarnation.owner.id:
            await incarnation_service.set_owner(incarnation_id, request.owner_id)
        else:
            raise GeneralForbiddenError(
                "Updating the 'owner' field can only be performed by the current owner or an administator."
            )

    if request.requested_version is not None or request.requested_data is not None:
        return await _create_change(
            incarnation_id=incarnation_id,
            requested_version=request.requested_version,
            requested_data=requested_data,
            automerge=request.automerge or False,
            patch=True,
            response=response,
            change_service=change_service,
            initialized_by=authorization_serive.current_user.id,
        )

    return await change_service.get_incarnation_with_details(incarnation_id)


@router.delete(
    "/{incarnation_id}",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "The incarnation was successfully deleted",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The incarnation was not found in the inventory",
            "model": ApiError,
        },
        status.HTTP_409_CONFLICT: {
            "description": "The incarnation already has a reconciliation in progress",
            "model": ApiError,
        },
    },
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(write_access_on_incarnation)],
)
async def delete_incarnation(
    incarnation_id: int,
    incarnation_service: IncarnationService = Depends(get_incarnation_service),
):
    """Deletes the incarnation from the inventory.

    The incarnation cannot be deleted if a reconciliation is in progress.

    This won't delete the incarnation repository itself, but only deletes the
    incarnation from the inventory.
    """
    incarnation = await incarnation_service.get_by_id(incarnation_id)

    await incarnation_service.delete(incarnation)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{incarnation_id}/diff",
    responses={
        status.HTTP_200_OK: {
            "description": "The diffs manually applied to the incarnation",
            "model": str,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The incarnation was not found in the inventory",
            "model": ApiError,
        },
    },
    dependencies=[Depends(read_access_on_incarnation)],
)
async def diff_incarnation(
    incarnation_id: int,
    change_service: ChangeService = Depends(get_change_service),
):
    """Returns the diff which shows all changes manually applied to the incarnation."""

    diff = await change_service.diff_incarnation(incarnation_id)

    return Response(
        content=diff,
        media_type="text/plain",
    )

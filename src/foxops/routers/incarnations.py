from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from foxops.database.repositories.incarnation.errors import IncarnationNotFoundError
from foxops.dependencies import get_change_service, get_hoster, get_incarnation_service
from foxops.engine import TemplateData
from foxops.errors import IncarnationNotFoundError as IncarnationNotFoundLegacyError
from foxops.hosters import Hoster
from foxops.logger import bind, get_logger
from foxops.models import (
    DesiredIncarnationState,
    DesiredIncarnationStatePatch,
    IncarnationBasic,
    IncarnationWithDetails,
)
from foxops.models.errors import ApiError
from foxops.routers import changes
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


@router.get(
    "",
    responses={
        status.HTTP_200_OK: {
            "description": "The list of incarnations in the inventory",
            "model": list[IncarnationBasic],
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
):
    """Returns a list of all known incarnations.

    The list is sorted by incarnartion ID, with the oldest incarnation first.

    TODO: implement pagination
    """
    if incarnation_repository is None:
        return await change_service.list_incarnations()

    try:
        return [
            await change_service.get_incarnation_by_repo_and_target_directory(incarnation_repository, target_directory)
        ]
    except IncarnationNotFoundLegacyError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ApiError(message="No incarnation found for the given repository and target directory")


@router.post(
    "",
    responses={
        status.HTTP_201_CREATED: {
            "description": "The incarnation has been successfully initialized and was added to the inventory.",
            "model": IncarnationWithDetails,
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
)
async def create_incarnation(
    response: Response,
    desired_incarnation_state: DesiredIncarnationState,
    allow_import: bool = False,
    change_service: ChangeService = Depends(get_change_service),
):
    """Initializes a new incarnation and adds it to the inventory.

    If the initialization fails, foxops will return the error in a `4xx` or `5xx` status code response.
    """
    bind(incarnation_repository=desired_incarnation_state.incarnation_repository)
    bind(target_directory=desired_incarnation_state.target_directory)

    if allow_import is True:
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return ApiError(message="The `allow_import` parameter is no longer supported")

    template_data = desired_incarnation_state.template_data or {}

    try:
        change = await change_service.create_incarnation(
            incarnation_repository=desired_incarnation_state.incarnation_repository,
            target_directory=desired_incarnation_state.target_directory,
            template_repository=desired_incarnation_state.template_repository,
            template_repository_version=desired_incarnation_state.template_repository_version,
            template_data=template_data,
        )
    except IncarnationAlreadyExists:
        response.status_code = status.HTTP_409_CONFLICT
        return ApiError(
            message=(
                f"There is already a foxops incarnation at {desired_incarnation_state.incarnation_repository} "
                f"with target directory {desired_incarnation_state.target_directory}"
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
)
async def read_incarnation(
    response: Response,
    incarnation_id: int,
    change_service: ChangeService = Depends(get_change_service),
):
    """Returns the details of the incarnation from the inventory."""
    try:
        return await change_service.get_incarnation_with_details(incarnation_id)
    except IncarnationNotFoundError as exc:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ApiError(message=str(exc))


class IncarnationResetRequest(BaseModel):
    override_version: str | None = None
    override_template_data: TemplateData | None = None


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
)
async def reset_incarnation(
    incarnation_id: int,
    response: Response,
    request: IncarnationResetRequest | None = None,
    incarnation_service: IncarnationService = Depends(get_incarnation_service),
    change_service: ChangeService = Depends(get_change_service),
    hoster: Hoster = Depends(get_hoster),
):
    to_version = request.override_version if request else None
    to_data = request.override_template_data if request else None

    try:
        change = await change_service.reset_incarnation(incarnation_id, to_version, to_data)
    except IncarnationNotFoundError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ApiError(message="The incarnation was not found in the inventory")
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


@router.put(
    "/{incarnation_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "The incarnation was successfully reconciled",
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
            "description": "The incarnation already has a reconciliation in progress",
            "model": ApiError,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "The reconciliation failed",
            "model": ApiError,
        },
    },
)
async def update_incarnation(
    response: Response,
    incarnation_id: int,
    desired_incarnation_state_patch: DesiredIncarnationStatePatch,
    change_service: ChangeService = Depends(get_change_service),
):
    """Reconciles the incarnation.

    If the reconciliation fails, foxops will return the error in a `4xx` or `5xx` status code response.

    If a reconciliation for the incarnation is already in progress a `409 CONFLICT` status code will be returned.

    If no *desired incarnation state* is provided in the request body, foxops will use the
    persisted *actual state* and perform a reconciliation. This is seldomly useful, but can be used
    to update when a moving Git revision (e.g. a branch) is used.
    """

    try:
        await change_service.create_change_merge_request(
            incarnation_id=incarnation_id,
            requested_version=desired_incarnation_state_patch.template_repository_version,
            requested_data=desired_incarnation_state_patch.template_data,
            automerge=desired_incarnation_state_patch.automerge,
        )
    except IncarnationNotFoundError as exc:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ApiError(message=str(exc))
    except ChangeRejectedDueToPreviousUnfinishedChange:
        response.status_code = status.HTTP_409_CONFLICT
        return ApiError(message="There is a previous change that is still open. Please merge/close it first.")
    except ChangeRejectedDueToNoChanges:
        logger.info(
            "A change was requested, but there were no changes to apply",
            incarnation_id=incarnation_id,
            requested_version=desired_incarnation_state_patch.template_repository_version,
            requested_data=desired_incarnation_state_patch.template_data,
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
)
async def delete_incarnation(
    response: Response,
    incarnation_id: int,
    incarnation_service: IncarnationService = Depends(get_incarnation_service),
):
    """Deletes the incarnation from the inventory.

    The incarnation cannot be deleted if a reconciliation is in progress.

    This won't delete the incarnation repository itself, but only deletes the
    incarnation from the inventory.
    """

    try:
        incarnation = await incarnation_service.get_by_id(incarnation_id)
    except IncarnationNotFoundError as exc:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ApiError(message=str(exc))

    await incarnation_service.delete(incarnation)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

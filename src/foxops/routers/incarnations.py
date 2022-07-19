from fastapi import APIRouter, Depends, Response, status

import foxops.reconciliation as reconciliation
from foxops.dal import DAL, get_dal
from foxops.errors import IncarnationNotFoundError
from foxops.hosters import GitLab, Hoster
from foxops.logging import bind, get_logger
from foxops.models import (
    DesiredIncarnationState,
    DesiredIncarnationStatePatch,
    Incarnation,
)
from foxops.models.errors import ApiError

#: Holds the router for the incarnations API endpoints
router = APIRouter(
    prefix="/api/incarnations",
    tags=["incarnations"],
)

#: Holds the logger for these routes
logger = get_logger(__name__)


def get_hoster() -> Hoster:
    # NOTE: Yes, you may absolutely use proper dependency injection at some point.
    return GitLab(
        address="",
        token="",
    )


def get_reconciliation():
    # NOTE: Yes, you may absolutely use proper dependency injection at some point.
    return reconciliation


@router.get(
    "/",
    responses={
        status.HTTP_200_OK: {
            "description": "The list of incarnations in the inventory",
            "model": list[Incarnation],
        },
    },
)
async def list_incarnations(dal: DAL = Depends(get_dal)):
    """Returns a list of all known incarnations.

    The list is sorted by creation date, with the oldest incarnation first.

    TODO: implement pagination
    """
    return [i async for i in dal.get_incarnations()]


@router.post(
    "/",
    responses={
        status.HTTP_201_CREATED: {
            "description": "The incarnation has been successfully initialized and was added to the inventory.",
            "model": Incarnation,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "The desired incarnation state was not valid.",
            "model": ApiError,
        },
        status.HTTP_409_CONFLICT: {
            "description": "The incarnation is already initialized.",
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
    dal: DAL = Depends(get_dal),
    hoster: Hoster = Depends(get_hoster),
    reconciliation=Depends(get_reconciliation),
):
    """Initializes a new incarnation and adds it to the inventory.

    If the incarnation Git repository does not yet exist, a `400 BAD REQUEST` error is returned.

    If the incarnation is already initialized or already exists in the inventory, a `409 CONFLICT` error is returned.

    If the initialization fails, foxops will return the error in a `4xx` or `5xx` status code response.
    """
    bind(incarnation_repository=desired_incarnation_state.incarnation_repository)
    bind(target_directory=desired_incarnation_state.target_directory)

    try:
        revision = await reconciliation.initialize_incarnation(
            hoster, desired_incarnation_state
        )
    except Exception as exc:
        logger.exception(str(exc))
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ApiError(message=str(exc))

    incarnation = await dal.create_incarnation(desired_incarnation_state, revision)

    bind(incarnation_id=incarnation.id)
    response.status_code = status.HTTP_201_CREATED
    return incarnation


@router.get(
    "/{incarnation_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "The actual state of the incarnation from the inventory",
            "model": Incarnation,
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
    dal: DAL = Depends(get_dal),
):
    """Returns the details of the incarnation from the inventory."""
    try:
        incarnation = await dal.get_incarnation(incarnation_id)
    except IncarnationNotFoundError as exc:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ApiError(message=str(exc))
    else:
        return incarnation


@router.put(
    "/{incarnation_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "The incarnation was successfully reconciled",
            "model": Incarnation,
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
    dal: DAL = Depends(get_dal),
    hoster: Hoster = Depends(get_hoster),
):
    """Reconciles the incarnation.

    If the reconciliation fails, foxops will return the error in a `4xx` or `5xx` status code response.

    If a reconciliation for the incarnation is already in progress a `409 CONFLICT` status code will be returned.

    If no *desired incarnation state* is provided in the request body, foxops will use the
    persisted *actual state* and perform a reconciliation. This is seldomly useful, but can be used
    to update when a moving Git revision (e.g. a branch) is used.
    """
    try:
        incarnation = await dal.get_incarnation(incarnation_id)
    except IncarnationNotFoundError as exc:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ApiError(message=str(exc))

    try:
        _ = reconciliation.update_incarnation(
            hoster, incarnation, desired_incarnation_state_patch
        )
    except Exception as exc:
        logger.exception(str(exc))
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ApiError(message=str(exc))

    return incarnation


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
    dal: DAL = Depends(get_dal),
):
    """Deletes the incarnation from the inventory.

    The incarnation cannot be deleted if a reconciliation is in progress.

    This won't delete the incarnation repository itself, but only deletes the
    incarnation from the inventory.
    """
    try:
        incarnation = await dal.get_incarnation(incarnation_id)
    except IncarnationNotFoundError as exc:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ApiError(message=str(exc))

    await dal.delete_incarnation(incarnation.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

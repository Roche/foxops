from fastapi import APIRouter, Depends, Response, status

from foxops.database import DAL
from foxops.dependencies import get_dal, get_hoster, get_reconciliation
from foxops.errors import (
    IncarnationAlreadyInitializedError,
    IncarnationNotFoundError,
    ReconciliationUserError,
)
from foxops.hosters import Hoster
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


@router.get(
    "/",
    responses={
        status.HTTP_200_OK: {
            "description": "The list of incarnations in the inventory",
            "model": list[Incarnation],
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
    dal: DAL = Depends(get_dal),
):
    """Returns a list of all known incarnations.

    The list is sorted by creation date, with the oldest incarnation first.

    TODO: implement pagination
    """
    if incarnation_repository is not None:
        async with dal.connection() as conn:
            incarnation = await dal.get_incarnation_by_identity(incarnation_repository, target_directory, conn)
            if incarnation is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return ApiError(message="No incarnation found for the given repository and target directory")

    return [i async for i in dal.get_incarnations()]


@router.post(
    "/",
    responses={
        status.HTTP_200_OK: {
            "description": "The incarnation is already initialized and was imported to the inventory. Only applicable with `allow_import=True`.",
            "model": Incarnation,
        },
        status.HTTP_201_CREATED: {
            "description": "The incarnation has been successfully initialized and was added to the inventory.",
            "model": Incarnation,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "The desired incarnation state was not valid or the incarnation already exists and import was not allowed.",
            "model": ApiError,
        },
        status.HTTP_409_CONFLICT: {
            "description": "The incarnation is already initialized and has a template configuration mismatch.",
            "model": Incarnation,
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
        revision = await reconciliation.initialize_incarnation(hoster, desired_incarnation_state)
    except IncarnationAlreadyInitializedError as exc:
        if not allow_import:
            logger.warning(f"User error happened during initialization of incarnation: {exc}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ApiError(message=str(exc))

        revision = exc.revision
        if exc.has_mismatch:
            response.status_code = status.HTTP_409_CONFLICT
        else:
            response.status_code = status.HTTP_200_OK
    except ReconciliationUserError as exc:
        logger.warning(f"User error happened during initialization of incarnation: {exc}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ApiError(message=str(exc))
    except Exception as exc:
        logger.exception(str(exc))
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ApiError(message=str(exc))
    else:
        response.status_code = status.HTTP_201_CREATED

    incarnation = await dal.create_incarnation(desired_incarnation_state, revision)

    bind(incarnation_id=incarnation.id)
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
    reconciliation=Depends(get_reconciliation),
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
        _ = await reconciliation.update_incarnation(hoster, incarnation, desired_incarnation_state_patch)
    except ReconciliationUserError as exc:
        logger.warning(f"User error happened during initialization of incarnation: {exc}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ApiError(message=str(exc))
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

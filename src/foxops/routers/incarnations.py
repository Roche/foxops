from datetime import timedelta

from fastapi import APIRouter, Depends, Response, status

from foxops.database import DAL
from foxops.dependencies import get_dal, get_hoster, get_reconciliation
from foxops.errors import IncarnationAlreadyInitializedError, IncarnationNotFoundError
from foxops.hosters import Hoster
from foxops.logger import bind, get_logger
from foxops.models import (
    DesiredIncarnationState,
    DesiredIncarnationStatePatch,
    Incarnation,
    IncarnationBasic,
    IncarnationWithDetails,
)
from foxops.models.errors import ApiError

#: Holds the router for the incarnations API endpoints
router = APIRouter(prefix="/api/incarnations", tags=["incarnations"])

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
    dal: DAL = Depends(get_dal),
    hoster: Hoster = Depends(get_hoster),
) -> list[IncarnationBasic] | ApiError:
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

            return [await get_incarnation_basic(incarnation, hoster)]

    return [await get_incarnation_basic(i, hoster) async for i in dal.get_incarnations()]


@router.post(
    "",
    responses={
        status.HTTP_200_OK: {
            "description": "The incarnation is already initialized and was imported to the inventory. "
            "Only applicable with `allow_import=True`.",
            "model": IncarnationWithDetails,
        },
        status.HTTP_201_CREATED: {
            "description": "The incarnation has been successfully initialized and was added to the inventory.",
            "model": IncarnationWithDetails,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "The desired incarnation state was not valid or the incarnation already exists "
            "and import was not allowed.",
            "model": ApiError,
        },
        status.HTTP_409_CONFLICT: {
            "description": "The incarnation is already initialized and has a template configuration mismatch.",
            "model": IncarnationBasic,
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
) -> IncarnationWithDetails | ApiError:
    """Initializes a new incarnation and adds it to the inventory.

    If the incarnation Git repository does not yet exist, a `400 BAD REQUEST` error is returned.

    If the incarnation is already initialized or already exists in the inventory, a `409 CONFLICT` error is returned.

    If the initialization fails, foxops will return the error in a `4xx` or `5xx` status code response.
    """
    bind(incarnation_repository=desired_incarnation_state.incarnation_repository)
    bind(target_directory=desired_incarnation_state.target_directory)

    try:
        commit_sha, merge_request_id = await reconciliation.initialize_incarnation(hoster, desired_incarnation_state)
    except IncarnationAlreadyInitializedError as exc:
        if not allow_import:
            logger.warning(f"User error happened during initialization of incarnation: {exc}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ApiError(message=str(exc))

        commit_sha = exc.commit_sha
        merge_request_id = None
        if exc.has_mismatch:
            response.status_code = status.HTTP_409_CONFLICT
        else:
            response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_201_CREATED

    incarnation = await dal.create_incarnation(desired_incarnation_state, commit_sha, merge_request_id)

    bind(incarnation_id=incarnation.id)
    return await get_incarnation_with_details(incarnation, hoster)


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
    dal: DAL = Depends(get_dal),
    hoster: Hoster = Depends(get_hoster),
) -> IncarnationWithDetails | ApiError:
    """Returns the details of the incarnation from the inventory."""
    try:
        incarnation = await dal.get_incarnation(incarnation_id)
    except IncarnationNotFoundError as exc:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ApiError(message=str(exc))

    return await get_incarnation_with_details(incarnation, hoster)


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
    dal: DAL = Depends(get_dal),
    hoster: Hoster = Depends(get_hoster),
    reconciliation=Depends(get_reconciliation),
) -> IncarnationWithDetails | ApiError:
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

    update = await reconciliation.update_incarnation(hoster, incarnation, desired_incarnation_state_patch)

    if update is not None:
        incarnation = await dal.update_incarnation(incarnation.id, commit_sha=update[0], merge_request_id=update[1])

    return await get_incarnation_with_details(incarnation, hoster)


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


async def get_incarnation_with_details(incarnation: Incarnation, hoster: Hoster) -> IncarnationWithDetails:
    reconciliation_status = await hoster.get_reconciliation_status(
        incarnation.incarnation_repository,
        incarnation.target_directory,
        incarnation.commit_sha,
        incarnation.merge_request_id,
        pipeline_timeout=timedelta(minutes=1),
    )
    response = IncarnationWithDetails(
        **(await get_incarnation_basic(incarnation, hoster)).dict(),
        status=reconciliation_status,
    )

    incarnation_state = await hoster.get_incarnation_state(
        incarnation.incarnation_repository, incarnation.target_directory
    )
    if incarnation_state is not None:
        state = incarnation_state[1]
        response.template_repository = state.template_repository
        response.template_repository_version = state.template_repository_version
        response.template_repository_version_hash = state.template_repository_version_hash
        response.template_data = state.template_data

    return response


async def get_incarnation_basic(incarnation: Incarnation, hoster: Hoster) -> IncarnationBasic:
    return IncarnationBasic(
        **incarnation.dict(),
        commit_url=await hoster.get_commit_url(incarnation.incarnation_repository, incarnation.commit_sha),
        merge_request_url=(
            await hoster.get_merge_request_url(incarnation.incarnation_repository, incarnation.merge_request_id)
        )
        if incarnation.merge_request_id
        else None,
    )

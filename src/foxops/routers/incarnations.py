from datetime import timedelta

from fastapi import APIRouter, Depends, Response, status

from foxops.database import DAL
from foxops.dependencies import (
    get_change_service,
    get_dal,
    get_hoster,
    get_reconciliation,
)
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
from foxops.routers import changes
from foxops.services.change import ChangeService, IncarnationAlreadyExists

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
    dal: DAL = Depends(get_dal),
    change_service: ChangeService = Depends(get_change_service),
) -> list[IncarnationBasic] | ApiError:
    """Returns a list of all known incarnations.

    The list is sorted by creation date, with the oldest incarnation first.

    TODO: implement pagination
    """
    if incarnation_repository is None:
        incarnation_ids = [i.id async for i in dal.get_incarnations()]
    else:
        async with dal.connection() as conn:
            incarnation = await dal.get_incarnation_by_identity(incarnation_repository, target_directory, conn)
            if incarnation is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return ApiError(message="No incarnation found for the given repository and target directory")

        incarnation_ids = [incarnation.id]

    return [await change_service.get_incarnation_basic(i) for i in incarnation_ids]


@router.post(
    "legacy",
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
async def create_incarnation_legacy(
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
) -> IncarnationWithDetails | ApiError:
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
) -> IncarnationWithDetails | ApiError:
    """Returns the details of the incarnation from the inventory."""
    try:
        return await change_service.get_incarnation_with_details(incarnation_id)
    except IncarnationNotFoundError as exc:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ApiError(message=str(exc))


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
) -> IncarnationWithDetails | ApiError:
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
    incarnation_basic = await get_incarnation_basic(incarnation, hoster)

    reconciliation_status = await hoster.get_reconciliation_status(
        incarnation.incarnation_repository,
        incarnation.target_directory,
        incarnation.commit_sha,
        incarnation.merge_request_id,
        pipeline_timeout=timedelta(minutes=1),
    )
    response = IncarnationWithDetails(
        **incarnation_basic.dict(),
        status=reconciliation_status,
    )

    if incarnation.merge_request_id is not None:
        response.merge_request_status = await hoster.get_merge_request_status(
            incarnation.incarnation_repository,
            incarnation.merge_request_id,
        )

    incarnation_state = await hoster.get_incarnation_state(
        incarnation.incarnation_repository, incarnation.target_directory
    )
    if incarnation_state is not None:
        state = incarnation_state[1]
        response.template_repository = state.template_repository
        response.template_repository_version = state.template_repository_version
        response.template_repository_version_hash = state.template_repository_version_hash
        if state.template_data is not None:
            response.template_data = dict(state.template_data)

    return response


async def get_incarnation_basic(incarnation: Incarnation, hoster: Hoster) -> IncarnationBasic:
    result = IncarnationBasic(
        id=incarnation.id,
        incarnation_repository=incarnation.incarnation_repository,
        target_directory=incarnation.target_directory,
        commit_sha=incarnation.commit_sha,
        commit_url=await hoster.get_commit_url(incarnation.incarnation_repository, incarnation.commit_sha),
        merge_request_id=incarnation.merge_request_id,
        merge_request_url=await hoster.get_merge_request_url(
            incarnation.incarnation_repository, incarnation.merge_request_id
        )
        if incarnation.merge_request_id
        else None,
    )

    return result

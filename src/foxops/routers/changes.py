import enum
from datetime import datetime
from typing import Annotated, Self

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, model_validator

from foxops.database.repositories.change import ChangeNotFoundError
from foxops.dependencies import get_change_service
from foxops.engine import TemplateData
from foxops.hosters.types import MergeRequestStatus
from foxops.models.change import Change, ChangeWithMergeRequest
from foxops.services.change import CannotRepairChangeException, ChangeService

router = APIRouter()


async def get_change(
    incarnation_id: Annotated[int, Path()],
    revision: Annotated[int, Path(description="Change revision within the given incarnation")],
    change_service: Annotated[ChangeService, Depends(get_change_service)],
) -> Change:
    try:
        change_id = await change_service.get_change_id_by_revision(incarnation_id, revision)
        return await change_service.get_change(change_id)
    except ChangeNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change not found")


class CreateChangeType(enum.Enum):
    DIRECT = "direct"
    MERGE_REQUEST_MANUAL = "merge_request_manual"
    MERGE_REQUEST_AUTOMERGE = "merge_request_automerge"


class CreateChangeRequest(BaseModel):
    requested_version: str | None = None
    requested_data: dict[str, str] | None = None
    change_type: CreateChangeType = CreateChangeType.DIRECT

    @model_validator(mode="after")
    def check_either_version_or_data_change_requested(self) -> Self:
        if self.requested_version is None and self.requested_data is None:
            raise ValueError("Either requested_version or requested_data must be set")

        return self


class ChangeType(enum.Enum):
    DIRECT = "direct"
    MERGE_REQUEST = "merge_request"


class ChangeDetails(BaseModel):
    id: int
    type: ChangeType

    incarnation_id: int
    revision: int

    requested_version: str
    requested_version_hash: str
    requested_data: TemplateData

    created_at: datetime
    commit_sha: str

    merge_request_id: str | None = None
    merge_request_branch_name: str | None = None
    merge_request_status: MergeRequestStatus | None = None

    @classmethod
    def from_service_object(cls, obj: Change | ChangeWithMergeRequest) -> Self:
        match obj:
            case ChangeWithMergeRequest():
                return cls(type=ChangeType.MERGE_REQUEST, **obj.model_dump())
            case Change():
                return cls(type=ChangeType.DIRECT, **obj.model_dump())
            case _:
                raise NotImplementedError(f"Unknown change type {type(obj)}")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_change(
    incarnation_id: int,
    request: CreateChangeRequest,
    change_service: ChangeService = Depends(get_change_service),
) -> ChangeDetails:
    match request.change_type:
        case CreateChangeType.DIRECT:
            change = await change_service.create_change_direct(
                incarnation_id, request.requested_version, request.requested_data
            )
        case CreateChangeType.MERGE_REQUEST_MANUAL:
            change = await change_service.create_change_merge_request(
                incarnation_id, request.requested_version, request.requested_data, automerge=False
            )
        case CreateChangeType.MERGE_REQUEST_AUTOMERGE:
            change = await change_service.create_change_merge_request(
                incarnation_id, request.requested_version, request.requested_data, automerge=True
            )
        case _:
            raise NotImplementedError(f"Unknown change type {request.change_type}")

    return ChangeDetails.from_service_object(change)


@router.get("")
async def list_changes(
    incarnation_id: int,
    change_service: ChangeService = Depends(get_change_service),
) -> list[ChangeDetails]:
    changes = await change_service.list_changes(incarnation_id)

    return [ChangeDetails.from_service_object(change) for change in changes]


@router.get(
    "/{revision}",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Change not found"},
    },
)
async def get_change_details(
    change: Change = Depends(get_change),
) -> ChangeDetails:
    return ChangeDetails.from_service_object(change)


@router.post(
    "/{revision}/fix",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Fix a change that is stuck in an incomplete state. "
    "This can happen if the change was started in foxops, but then pushing the change to the "
    "incarnation repository failed, for example because the hoster was down.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Change not found"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "The change cannot be repaired automatically"},
    },
)
async def fix_incomplete_change(
    change: Change = Depends(get_change),
    change_service: ChangeService = Depends(get_change_service),
):
    try:
        await change_service.update_incomplete_change(change.id)
    except CannotRepairChangeException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

import enum

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from foxops.dependencies import get_change_service
from foxops.services.change import CannotRepairChangeException, ChangeService

router = APIRouter()


class ChangeType(enum.Enum):
    DIRECT = "direct"
    MERGE_REQUEST_MANUAL = "merge_request_manual"
    MERGE_REQUEST_AUTOMERGE = "merge_request_automerge"


class CreateChangeRequest(BaseModel):
    requested_version: str
    requested_data: dict[str, str]
    change_type: ChangeType = ChangeType.DIRECT


@router.post("")
async def create_change(
    incarnation_id: int,
    request: CreateChangeRequest,
    change_service: ChangeService = Depends(get_change_service),
):
    if request.change_type != ChangeType.DIRECT:
        raise NotImplementedError("Only direct changes are supported at the moment.")

    await change_service.create_change_direct(incarnation_id, request.requested_version, request.requested_data)


@router.post(
    "/{change_id}/fix",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Fix a change that is stuck in an incomplete state. "
    "This can happen if the change was started in foxops, but then pushing the change to the "
    "incarnation repository failed, for example because the hoster was down.",
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "The change cannot be repaired automatically"}},
)
async def fix_incomplete_change(
    change_id: int,
    change_service: ChangeService = Depends(get_change_service),
):
    try:
        await change_service.update_incomplete_change(change_id, grace_period_minutes=0)
    except CannotRepairChangeException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

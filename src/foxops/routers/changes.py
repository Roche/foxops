import enum

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from foxops.dependencies import get_change_service
from foxops.services.change import ChangeService

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

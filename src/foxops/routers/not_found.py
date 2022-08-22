from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/api")


@router.get(
    "/{full_path:path}",
    include_in_schema=False,
    status_code=status.HTTP_404_NOT_FOUND,
    response_class=PlainTextResponse,
)
def api_not_found(full_path: str):
    return "not found"

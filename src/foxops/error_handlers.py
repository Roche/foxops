from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from foxops.errors import FoxopsUserError
from foxops.logger import get_logger

#: Holds the module logger instance
logger = get_logger(__name__)


async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(exc)})


async def foxops_user_error(_: Request, exc: FoxopsUserError):
    logger.warning(f"User error happened: {exc}")
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(exc)})


async def catch_all(_: Request, exc: Exception):
    logger.exception(str(exc))
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(exc)})


__error_handlers__ = {
    RequestValidationError: validation_exception_handler,
    FoxopsUserError: foxops_user_error,
    Exception: catch_all,
}

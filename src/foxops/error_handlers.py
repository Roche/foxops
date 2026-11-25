from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from foxops.errors import FoxopsUserError
from foxops.logger import get_logger

#: Holds the module logger instance
logger = get_logger(__name__)


async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(exc)})


def _request_context(request: Request) -> dict:
    return {
        "method": request.method,
        "path": request.url.path,
        # Read from request.state, not from the contextvars: the middleware binds those in a child task,
        # and catch_all runs outside of it.
        "request_id": getattr(request.state, "request_id", None),
        **request.path_params,
    }


async def foxops_user_error(request: Request, exc: FoxopsUserError):
    logger.warning(f"User error happened: {exc}", **_request_context(request))
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(exc)})


async def catch_all(request: Request, exc: Exception):
    logger.exception(str(exc), **_request_context(request))
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(exc)})


__error_handlers__ = {
    RequestValidationError: validation_exception_handler,
    FoxopsUserError: foxops_user_error,
    Exception: catch_all,
}

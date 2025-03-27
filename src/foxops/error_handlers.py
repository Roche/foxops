from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from foxops.database.repositories.change.errors import (
    ChangeCommitAlreadyPushedError,
    ChangeNotFoundError,
    IncarnationHasNoChangesError,
)
from foxops.database.repositories.group.errors import (
    GroupAlreadyExistsError,
    GroupNotFoundError,
)
from foxops.database.repositories.incarnation.errors import IncarnationNotFoundError
from foxops.database.repositories.user.errors import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from foxops.errors import (
    ForbiddenError,
    FoxopsError,
    FoxopsUserError,
    GeneralForbiddenError,
    ResourceForbiddenError,
)
from foxops.logger import get_logger

#: Holds the module logger instance
logger = get_logger(__name__)

EXCEPTION_TO_STATUS_CODE = {
    # Incarnation errors
    IncarnationNotFoundError: status.HTTP_404_NOT_FOUND,
    # Group errors
    GroupNotFoundError: status.HTTP_404_NOT_FOUND,
    GroupAlreadyExistsError: status.HTTP_409_CONFLICT,
    # Change errors
    ChangeNotFoundError: status.HTTP_404_NOT_FOUND,
    ChangeCommitAlreadyPushedError: status.HTTP_409_CONFLICT,
    IncarnationHasNoChangesError: status.HTTP_400_BAD_REQUEST,
    # User errors
    UserNotFoundError: status.HTTP_404_NOT_FOUND,
    UserAlreadyExistsError: status.HTTP_409_CONFLICT,
    # Access
    ForbiddenError: status.HTTP_403_FORBIDDEN,
    GeneralForbiddenError: status.HTTP_403_FORBIDDEN,
    ResourceForbiddenError: status.HTTP_403_FORBIDDEN,
}


async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(exc)})


async def foxops_user_error(_: Request, exc: FoxopsUserError):
    logger.warning(f"User error happened: {exc}")
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(exc)})


async def catch_all_foxops_exception(_: Request, exc: FoxopsError):
    if exc.__class__ in EXCEPTION_TO_STATUS_CODE:
        return JSONResponse(
            status_code=EXCEPTION_TO_STATUS_CODE[exc.__class__],
            content={"message": str(exc)},
        )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(exc)})


async def catch_all(_: Request, exc: Exception):
    logger.exception(str(exc))
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(exc)})


__error_handlers__ = {
    RequestValidationError: validation_exception_handler,
    FoxopsUserError: foxops_user_error,
    FoxopsError: catch_all_foxops_exception,
    Exception: catch_all,
}

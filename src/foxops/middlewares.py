import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from structlog.contextvars import bind_contextvars, clear_contextvars

from foxops.logger import get_logger

Middleware = Callable[[Request], Awaitable[Response]]

logger = get_logger(__name__)


async def request_middleware(request: Request, call_next: Middleware) -> Response:
    """FastAPI Middleware to set a unique id to identify a request."""
    clear_contextvars()

    request_id = str(uuid.uuid4())
    bind_contextvars(request_id=request_id)

    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response

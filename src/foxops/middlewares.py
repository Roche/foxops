import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from structlog.contextvars import bind_contextvars, clear_contextvars

from foxops.logger import get_logger

Middleware = Callable[[Request], Awaitable[Response]]

logger = get_logger(__name__)


async def request_id_middleware(request: Request, call_next: Middleware) -> Response:
    """FastAPI Middleware to set a unique id to identify a request."""
    clear_contextvars()

    request_id = str(uuid.uuid4())
    bind_contextvars(request_id=request_id)

    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


async def request_time_middleware(request: Request, call_next: Middleware) -> Response:
    """FastAPI Middleware to set the request time."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    response.headers["X-Request-Time"] = str(duration)
    return response

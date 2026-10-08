import logging
from typing import Sequence

import structlog
from structlog.contextvars import (
    bind_contextvars,
    bound_contextvars,
    merge_contextvars,
    unbind_contextvars,
)
from structlog.types import Processor


def configure_sqlalchemy_logging():
    logging.getLogger("sqlalchemy.engine.Engine").handlers.clear()

    # set aiosqlite logs to WARNING. They are very noisy otherwise.
    aiosqlite_logger = logging.getLogger("aiosqlite")
    aiosqlite_logger.setLevel(logging.WARNING)


def configure_uvicorn_logging():
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.propagate = True
    uvicorn_logger.handlers.clear()

    uvicorn_error_logger = logging.getLogger("uvicron.error")
    uvicorn_error_logger.propagate = True
    uvicorn_error_logger.handlers.clear()

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.propagate = True
    uvicorn_access_logger.handlers.clear()


def build_console_renderer() -> structlog.dev.ConsoleRenderer:
    """Build the console renderer used for all foxops log output.

    The `exception_formatter` must be passed explicitly. Left to itself, ConsoleRenderer
    picks rich's traceback formatter whenever `rich` is installed (it is, as a direct
    dependency), and that formatter renders every stack frame's local variables. In foxops
    those locals hold rendered template data, httpx responses and SQLAlchemy objects, so
    repr()-ing them took ~26 seconds per traceback -- twice per failed request, because
    Starlette re-raises after our `catch_all` handler and uvicorn logs the same exception
    again. Rendering is synchronous on the event loop, so it stalls every other in-flight
    request, and the first render happens before the error response is sent, which pushed
    replies past the reverse proxy's 60s timeout. Plain tracebacks render in microseconds.
    """
    return structlog.dev.ConsoleRenderer(exception_formatter=structlog.dev.plain_traceback)


def setup_logging(level: int | str) -> None:
    if structlog.is_configured():
        return

    shared_processors: Sequence[Processor] = [
        merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.stdlib.add_logger_name,
    ]

    structlog.configure(
        processors=shared_processors  # type: ignore
        + [
            # Prepare event dict for `ProcessorFormatter`.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on `logging` entries that do NOT originate within
        # structlog.
        foreign_pre_chain=shared_processors,
        # These run on ALL entries after the pre_chain is done.
        processors=[
            # Remove _record & _from_structlog.
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            build_console_renderer(),
        ],
    )

    configure_sqlalchemy_logging()
    configure_uvicorn_logging()

    handler = logging.StreamHandler()

    # Use OUR `ProcessorFormatter` to format all `logging` entries.
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    foxops_logger = logging.getLogger("foxops")
    foxops_logger.setLevel(level)
    foxops_logger.propagate = True


bind = bind_contextvars
unbind = unbind_contextvars
bound = bound_contextvars


def get_logger(*args, **kwargs) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(*args, **kwargs)

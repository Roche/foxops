import pytest
from structlog.stdlib import BoundLogger

from foxops import logging


@pytest.fixture(name="logger", scope="session")
def get_logger() -> BoundLogger:
    logger = logging.get_logger("test")
    return logger

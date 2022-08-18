import pytest
from structlog.stdlib import BoundLogger

from foxops import loggingcfg


@pytest.fixture(name="logger", scope="session")
def get_logger() -> BoundLogger:
    logger = loggingcfg.get_logger("test")
    return logger

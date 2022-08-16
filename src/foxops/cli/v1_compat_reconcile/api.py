import os
from contextlib import contextmanager
from subprocess import Popen
from time import sleep
from typing import Iterator

import httpx

from foxops.logger import get_logger

#: Holds the module logger
logger = get_logger(__name__)


@contextmanager
def foxops_api(foxops_api_url: str | None) -> Iterator[httpx.Client]:
    proc = None

    if not foxops_api_url:
        host = "127.0.0.1"
        port = "5005"
        proc = Popen(["uvicorn", "foxops.__main__:app", "--host", host, "--port", port])
        foxops_api_url = f"http://{host}:{port}/api"

        logger.info("Waiting 5 seconds for API server to start ...", url=foxops_api_url)
        sleep(5)

    client = httpx.Client(
        base_url=foxops_api_url,
        follow_redirects=True,
        timeout=None,
        headers={"Authorization": f"Bearer {os.environ['FOXOPS_STATIC_TOKEN']}"},
    )

    try:
        yield client
    finally:
        if proc is not None:
            logger.info("Killing API server ...")
            proc.kill()

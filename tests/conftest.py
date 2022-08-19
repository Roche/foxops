import logging
import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from foxops.__main__ import create_app
from foxops.database import DAL
from foxops.dependencies import get_dal
from foxops.logger import setup_logging


@pytest.fixture(scope="session", autouse=True)
def setup_logging_for_tests():
    setup_logging(level=logging.DEBUG)


@pytest.fixture(scope="session", name="test_run_id")
def create_unique_test_run_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture(scope="module", autouse=True)
def use_testing_gitconfig():
    orig_config_global = os.environ.get("GIT_CONFIG_GLOBAL")

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            test_gitconfig_path = Path(tmpdir) / "test.gitconfig"
            test_gitconfig_path.touch()
            os.environ["GIT_CONFIG_GLOBAL"] = str(test_gitconfig_path)
            subprocess.check_call(["git", "config", "--global", "user.name", "Test User"])
            subprocess.check_call(["git", "config", "--global", "user.email", "test@user.com"])
            subprocess.check_call(["git", "config", "--global", "init.defaultBranch", "main"])
            yield
        finally:
            if orig_config_global is not None:
                os.environ["GIT_CONFIG_GLOBAL"] = orig_config_global


@pytest.fixture(name="test_async_engine")
async def test_async_engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine, None]:
    local_db_file = tmp_path / "unit-test.db"
    test_database_url = f"sqlite+aiosqlite:///{str(local_db_file)}"

    async_engine = create_async_engine(test_database_url, future=True, echo=False, pool_pre_ping=True)

    yield async_engine


@pytest.fixture(name="api_app")
def get_api_app() -> FastAPI:
    return create_app()


@pytest.fixture(name="dal")
async def create_dal(test_async_engine: AsyncEngine) -> AsyncGenerator[DAL, None]:
    dal = DAL(test_async_engine)

    await dal.initialize_db()

    yield dal


@pytest.fixture(name="static_api_token", scope="session")
def get_static_api_token() -> str:
    return "test-token"


@pytest.fixture(scope="module", autouse=True)
def set_settings_env(static_api_token: str):
    os.environ["FOXOPS_GITLAB_ADDRESS"] = "https://nonsense.com/api/v4"
    os.environ["FOXOPS_GITLAB_TOKEN"] = "nonsense"
    os.environ["FOXOPS_STATIC_TOKEN"] = static_api_token


@pytest.fixture(name="api_client")
async def api_client(dal: DAL, api_app: FastAPI, static_api_token: str) -> AsyncGenerator[AsyncClient, None]:
    def _test_get_dal() -> DAL:
        return dal

    api_app.dependency_overrides[get_dal] = _test_get_dal

    async with AsyncClient(
        app=api_app,
        base_url="http://test/api",
        headers={"Authorization": f"Bearer {static_api_token}"},
    ) as ac:
        yield ac

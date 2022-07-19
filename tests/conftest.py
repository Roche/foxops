import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from foxops.__main__ import app
from foxops.dal import DAL, get_dal
from foxops.database.config import meta
from foxops.logging import setup_logging


@pytest.fixture(scope="module", autouse=True)
def setup_logging_for_tests():
    setup_logging(level=logging.DEBUG)


@pytest.fixture(scope="module", autouse=True)
def set_settings_env():
    os.environ["FOXOPS_GITLAB_ADDRESS"] = "http://127.0.0.1:5002"
    os.environ["FOXOPS_GITLAB_TOKEN"] = "ACCTEST1234567890123"


@pytest.fixture(scope="module", autouse=True)
def use_testing_gitconfig():
    orig_config_global = os.environ.get("GIT_CONFIG_GLOBAL")

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            test_gitconfig_path = Path(tmpdir) / "test.gitconfig"
            test_gitconfig_path.touch()
            os.environ["GIT_CONFIG_GLOBAL"] = str(test_gitconfig_path)
            subprocess.check_call(
                ["git", "config", "--global", "user.name", "Test User"]
            )
            subprocess.check_call(
                ["git", "config", "--global", "user.email", "test@user.com"]
            )
            subprocess.check_call(
                ["git", "config", "--global", "init.defaultBranch", "main"]
            )
            yield
        finally:
            if orig_config_global is not None:
                os.environ["GIT_CONFIG_GLOBAL"] = orig_config_global


@pytest.fixture(scope="function")
async def test_async_engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine, None]:
    local_db_file = Path("./unit-test.db")
    test_database_url = f"sqlite+aiosqlite:///./{str(local_db_file)}"

    async_engine = create_async_engine(
        test_database_url, future=True, echo=False, pool_pre_ping=True
    )

    async with async_engine.begin() as conn:
        await conn.run_sync(meta.create_all)

    try:
        yield async_engine
    finally:
        async with async_engine.begin() as conn:
            await conn.run_sync(meta.drop_all)
        local_db_file.unlink()


@pytest.fixture(name="api_app")
def get_api_app() -> FastAPI:
    return app


@pytest.fixture(name="dal", scope="function")
async def create_dal(test_async_engine: AsyncEngine) -> AsyncGenerator[DAL, None]:
    yield DAL(test_async_engine)


@pytest.fixture()
async def api_client(dal: DAL, api_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    def _test_get_dal() -> DAL:
        return dal

    api_app.dependency_overrides[get_dal] = _test_get_dal

    async with AsyncClient(
        app=api_app, base_url="http://test/api", follow_redirects=True
    ) as ac:
        yield ac

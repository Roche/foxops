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
from sqlalchemy.ext.asyncio import AsyncEngine

from foxops.__main__ import create_app
from foxops.database.engine import create_engine
from foxops.database.repositories.change.repository import ChangeRepository
from foxops.database.repositories.group.repository import GroupRepository
from foxops.database.repositories.incarnation.repository import IncarnationRepository
from foxops.database.repositories.user.repository import UserRepository
from foxops.database.schema import meta
from foxops.dependencies import (
    get_change_repository,
    get_database_engine,
    get_hoster,
    get_incarnation_repository,
)
from foxops.hosters.local import LocalHoster
from foxops.logger import setup_logging
from foxops.services.group import GroupService
from foxops.services.user import UserService

pytest_plugins = [
    "tests._plugins.fixtures_database",
    "tests._plugins.fixtures_gitlab",
]


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
async def test_async_engine() -> AsyncGenerator[AsyncEngine, None]:
    async_engine = create_engine("sqlite+aiosqlite://")

    async with async_engine.begin() as conn:
        await conn.run_sync(meta.create_all)

    yield async_engine


@pytest.fixture(name="app")
def create_foxops_app(static_api_token: str, monkeypatch) -> FastAPI:
    monkeypatch.setenv("FOXOPS_STATIC_TOKEN", static_api_token)

    return create_app()


@pytest.fixture
async def incarnation_repository(test_async_engine: AsyncEngine) -> IncarnationRepository:
    return IncarnationRepository(test_async_engine)


@pytest.fixture
async def change_repository(test_async_engine: AsyncEngine) -> ChangeRepository:
    return ChangeRepository(test_async_engine)


@pytest.fixture
async def user_repository(test_async_engine: AsyncEngine) -> UserRepository:
    return UserRepository(test_async_engine)


@pytest.fixture
async def group_repository(test_async_engine: AsyncEngine) -> GroupRepository:
    return GroupRepository(test_async_engine)


@pytest.fixture
async def user_service(user_repository: UserRepository, group_repository: GroupRepository) -> UserService:
    return UserService(user_repository, group_repository)


@pytest.fixture
async def group_service(group_repository: GroupRepository) -> GroupService:
    return GroupService(group_repository)


@pytest.fixture
def local_hoster(tmp_path: Path) -> LocalHoster:
    return LocalHoster(tmp_path)


@pytest.fixture(name="static_api_token", scope="session")
def get_static_api_token() -> str:
    return "test-token"


@pytest.fixture(name="unauthenticated_client")
async def create_unauthenticated_client(
    app: FastAPI,
    incarnation_repository: IncarnationRepository,
    change_repository: ChangeRepository,
    local_hoster: LocalHoster,
    test_async_engine: AsyncEngine,
) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_incarnation_repository] = lambda: incarnation_repository
    app.dependency_overrides[get_change_repository] = lambda: change_repository
    app.dependency_overrides[get_hoster] = lambda: local_hoster
    app.dependency_overrides[
        get_database_engine
    ] = (
        lambda: test_async_engine
    )  # We need this, since the api now requires a working db -> to create the user in the request\

    async with AsyncClient(
        app=app,
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture(name="authenticated_client")
async def create_authenticated_client(unauthenticated_client: AsyncClient, static_api_token: str) -> AsyncClient:
    unauthenticated_client.headers["Authorization"] = f"Bearer {static_api_token}"
    unauthenticated_client.headers["User"] = "root"
    return unauthenticated_client


@pytest.fixture(name="api_client")
async def create_api_client(authenticated_client: AsyncClient) -> AsyncClient:
    authenticated_client.base_url = f"{authenticated_client.base_url}/api"  # type: ignore
    return authenticated_client

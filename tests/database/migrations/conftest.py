import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from alembic.config import Config


@pytest.fixture
def database_path(tmp_path) -> str:
    return str(tmp_path / "foxops.db")


@pytest.fixture
def database_engine(database_path):
    engine_url = f"sqlite:///{database_path}"
    engine = create_engine(engine_url, future=True, echo=False, pool_pre_ping=True)

    yield engine


@pytest.fixture
def async_database_engine(database_path):
    engine_url = f"sqlite+aiosqlite:///{database_path}"
    engine = create_async_engine(engine_url, future=True, echo=False, pool_pre_ping=True)

    yield engine


@pytest.fixture
def alembic_config(database_engine):
    repo_root_dir = Path(__file__).parent.parent.parent.parent
    os.chdir(repo_root_dir)

    return Config(
        "alembic.ini",
        attributes={
            "connection": database_engine,
        },
    )

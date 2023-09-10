import pytest
from sqlalchemy import Engine, event
from sqlalchemy.ext.asyncio import create_async_engine

from foxops.database.schema import meta


@pytest.fixture
async def foxops_database(tmp_path):
    """Prepares a temporary database for foxops and returns the engine URL"""

    engine_url = f"sqlite+aiosqlite:///{str(tmp_path)}/foxops.db"

    # enforce foreign key constraints on SQLite:
    # https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#foreign-key-support
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async_engine = create_async_engine(engine_url, future=True, echo=False, pool_pre_ping=True)
    async with async_engine.begin() as conn:
        await conn.run_sync(meta.create_all)

    yield engine_url

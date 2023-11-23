from sqlalchemy import Pool
from sqlalchemy.event import listen
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def create_engine(connection_string: str) -> AsyncEngine:
    # enforce foreign key constraints on SQLite:
    # https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#foreign-key-support
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    if connection_string.startswith("sqlite+"):
        listen(Pool, "connect", set_sqlite_pragma)

    return create_async_engine(connection_string, future=True, echo=False, pool_pre_ping=True)

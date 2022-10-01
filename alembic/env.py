import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context
from foxops.database import schema
from foxops.settings import DatabaseSettings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = schema.meta

database_settings = DatabaseSettings()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=database_settings.url.get_secret_value(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(engine: AsyncEngine):
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # pytest-alembic will inject a connection at runtime
    engine = context.config.attributes.get("connection", None)

    if engine is None:
        engine = create_async_engine(
            database_settings.url.get_secret_value(),
            future=True,
            poolclass=pool.NullPool,
        )

    # we support both, async and sync engines - pytest-alembic will inject a sync engine
    if isinstance(engine, AsyncEngine):
        asyncio.run(run_async_migrations(engine))
    else:
        do_run_migrations(engine.connect())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

# Installation

The **foxops** Python package can be installed from the PyPI:

```bash
pip install foxops
```

The foxops Python package contains multiple console scripts:

* `fengine` - exposes the initialize and update APIs to manually execute the template rendering
* `foxops` - the legacy command line

And the main foxops API server can be started using uvicorn:

```
uvicorn foxops.__main__:app --host localhost --port 5001 --reload
```

## Docker

`foxops` is also deployed in the GitHub Container Registry and can be pulled from there:

```bash
docker pull ghcr.io/roche/foxops:<version>
```

```{note}
Make sure to replace the `<version>` with a [valid version](https://github.com/Roche/foxops/releases).
```

## Preparing the database

An SQL database is required to run foxops. [PostgreSQL](https://www.postgresql.org/) is the recommended choice.

* The database connection is configured using the `FOXOPS_DATABASE_URL` environment variable, which should contain a valid [SQLAlchemy database URL](https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls). Be aware that an asyncio-capable database driver is required. Examples are:
  * PostgreSQL: `postgresql+asyncpg://user:password@host:port/database`
  * SQLite (not recommended for production): `sqlite+aiosqlite:///path/to/database.db`
  * SQLite in memory (not recommended for production): `sqlite+aiosqlite:///:memory:`

With that environment variable set, the database can be initialized using the following [Alembic](https://alembic.sqlalchemy.org/en/latest/) command:

```shell
poetry run alembic upgrade head
```

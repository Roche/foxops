# Contributing

This project uses [Poetry](https://python-poetry.org/)
and [poetry-dynamic-versioning](https://pypi.org/project/poetry-dynamic-versioning/)
for dependency management and the package building process.

## Run foxops locally

### With docker-compose

The easiest way to get started is to run foxops locally via docker-compose. Just execute this command in the root folder of the project:

```shell
docker compose up
```

It will build the docker image and run foxops with an SQlite database and a local hoster configuration.

Now foxops can be accessed at `http://localhost:8000` with `dummy` as the token.

### Directly with Python

First, start by making sure that your virtual Python environment is up to date by running

```shell
poetry install
```

Then, you can run foxops with

```shell
export FOXOPS_DATABASE_URL=sqlite+aiosqlite:///./foxops.db
export FOXOPS_HOSTER_TYPE=local
export FOXOPS_HOSTER_LOCAL_DIRECTORY=<path to a local directory where foxops can store the repositories>
export FOXOPS_STATIC_TOKEN=dummy

# initialize sqlite database in ./foxops.db
poetry run alembic upgrade head

# run foxops webserver
poetry run uvicorn foxops.__main__:create_app --host localhost --port 5001 --reload --factory
```

## Running Tests

The test suite uses `pytest` as a test runner and it's located under `tests/`.

Simply execute the following commands to run the entire foxops test suite:

```shell
pytest
```

Tests can also run with parallelization enabled to speed up execution. To do so, simply add the `-n` flag with the number of parallel processes to use:

```shell
pytest -n 4
```

Some tests require a Gitlab instance to be available and will be skipped automatically if it's not the case.

### Run Tests that Require Gitlab

To run tests that require a Gitlab instance, you can either [run one locally](https://docs.gitlab.com/ee/install/docker.html) or use the public [gitlab.com](https://gitlab.com) instance. The latter is typically recommended for ease of use.

On that Gitlab instance, a "root group" is required, in which foxops can create temporary projects for test templates and incarnations (these will be automatically cleaned after the test execution). Also an access token is required that has access to that group.

Once you have all this, add the following environment variables and rerun the tests:

```shell
# defaults to "https://gitlab.com" if not specified
export FOXOPS_TESTS_GITLAB_ADDRESS=<address of the Gitlab instance>
export FOXOPS_TESTS_GITLAB_ROOT_GROUP_ID=<ID of the root group>
export FOXOPS_TESTS_GITLAB_TOKEN=<access token that can create projects>

# these variables can also be set in a file called `.env.test` in the root folder of the project

# execute tests (parallelization is recommended)
pytest -n 4
```

### Documentation

run `make live` in the `docs/` subfolder to start a web server that hosts a live-build of the documentation. It even auto-reloads in case of changes!

## Changing the database schema

This project uses [Alembic](https://alembic.sqlalchemy.org/en/latest/) for database migrations. If you change the database schema, you need to create a new migration script that contains steps to migrate existing databases to the new schema.

To create a new migration script, run the following command (adjusting the message):

```
poetry run alembic revision --autogenerate -m "Add a new table"
```

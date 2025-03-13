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

## Hoster types

Running FoxOps with the CLI or Docker Compose locally uses the so-called `Local Hoster`. FoxOps currently supports multiple hoster implementations, which can be configured via the `FOXOPS_HOSTER_TYPE` environment variable.

The supported hoster types are the following:

- `local`: The local hoster stores the repositories in a local directory. The path to this directory can be configured via the `FOXOPS_HOSTER_LOCAL_DIRECTORY` environment variable.
- `gitlab`: The GitLab hoster uses a GitLab instance to store the repositories. The GitLab instance can be configured via the `FOXOPS_HOSTER_GITLAB_ADDRESS`, `FOXOPS_HOSTER_GITLAB_TOKEN` and `FOXOPS_HOSTER_GITLAB_ROOT_GROUP_ID` environment variables.
- More hoster types might be added in the future (for example GitHub, Bitbucket, etc.)

> For local development, using the `local` hoster is recommended. See the section "How to setup the local hoster" for more information.

## How to setup the local hoster

Using the `local` hoster is recommended for local development. The local hoster stores the repositories in a local directory. The path to this directory can be configured via the `FOXOPS_HOSTER_LOCAL_DIRECTORY` environment variable.

Using the `local` hoster requires a certain project structure in order to work correctly.

1. Create a directory where the repositories should be stored. This directory will be used as the `FOXOPS_HOSTER_LOCAL_DIRECTORY` environment variable.
2. Inside this directory create a subdirectory for each "git" project. It doesn't matter if this "git" project is used as a template or an incarnation.
3. The next steps depend on what the type of the "git" project should be. It could either be used as a template or an incarnation.

### Template

If it is a template, all you have to do is to create a directory called `git`. This directory needs to contain the git template repository.

For this, you first have to create an empty git repository. You can do this by running the following commands:

```shell
git init git
```

Now inside this directory, run the following command to create an empty template repository:

```shell
fengine new
```

If you don't have the `fengine` command installed, you can install it by running the following command:

```shell
pip install foxops
```

### Incarnation

An incarnation directory needs to follow a slightly different structure. It needs to contain a `git` directory and a `merge_request` directory. Since merge requests are a concept of GitLab, the `merge_request` directory is used as a wrapper to simulate the merge request functionality.

> A locally hosted git repository supports merging branches. **BUT** it doesn't support merge requests (the concept of reviewing a merge before it is merged). This is why the `merge_request` directory is used as a wrapper to simulate the merge request functionality.

To do this, run the following commands:

```shell
mkdir -p merge_request
```

The next step is to create the git repository. You can do this by running the following commands:

```shell
git init --bare git
```

> Note: This is a bare repository. A bare repository doesn't have a working directory. But it can be used to push and pull changes to and from. If you would like to check out the repository, you can clone it to a different directory.

Now that we have this structure, we can start to create your first incarnation in the FoxOps UI.

## Running the UI locally
Running the UI localy requires having node.js installed. 

Running the UI usualy requires the API to be running. So if you don't have the API running on port 5001, follow the steps above to run the API locally.

To run the UI locally, navigate to the `ui` directory and run the following commands:

```shell
npm install
npm run start
```

This will start the UI on `http://localhost:3000`.

The UI will automatically proxy requests to the API running on `http://localhost:5001`.

## Running the UI through the API
It is also possible to serve the UI through the API. This is usually done when running the API in production. However it is not recommended to do this for local developement, since it requires quite some time to rebuild the UI.

However if you would like to test this, you can run the following commands:

```shell
cd ui
npm run build
```

> Note this requires the API to be running. If you don't have the API running, follow the steps above to run the API locally.

You can now access the UI on the port the API is running on. Usually this is `http://localhost:5001`.


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

fmt:
	poetry run black src tests alembic/versions
	poetry run isort src tests alembic/versions

lint:
	poetry run black --check --diff src tests alembic/versions
	poetry run isort --check-only src tests alembic/versions
	poetry run flake8 src tests alembic/versions

typecheck:
	poetry run dmypy run -- src tests

pre-commit: fmt lint typecheck

test:
	poetry run pytest tests

# gitlab-up and test-gitlab must agree on these, otherwise the tests authenticate
# against an instance that was started with a different root password.
GITLAB_CE_VERSION = 17.2.8-ce.0
GITLAB_ROOT_PASSWORD = dummyPassword

gitlab-up:
	GITLAB_CE_VERSION=$(GITLAB_CE_VERSION) GITLAB_ROOT_PASSWORD=$(GITLAB_ROOT_PASSWORD) \
		docker compose -f docker-compose.tests.yml up -d --wait

gitlab-down:
	docker compose -f docker-compose.tests.yml down -v

test-gitlab:
	FOXOPS_TESTS_GITLAB_ADDRESS=http://127.0.0.1:8929 \
	FOXOPS_TESTS_GITLAB_USERNAME=root \
	FOXOPS_TESTS_GITLAB_PASSWORD=$(GITLAB_ROOT_PASSWORD) \
		poetry run pytest $(PYTEST_ARGS)

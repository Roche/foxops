fmt:
	poetry run black src tests alembic/versions
	poetry run isort src tests alembic/versions

lint:
	poetry run black --check --diff src tests alembic/versions
	poetry run isort --check-only src tests alembic/versions
	poetry run flake8 src tests alembic/versions

typecheck:
	poetry run dmypy run -- src tests

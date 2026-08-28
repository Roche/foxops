fmt:
	poetry run black src tests alembic/versions
	poetry run isort src tests alembic/versions

lint:
	poetry run black --check --diff src tests alembic/versions
	poetry run isort --check-only src tests alembic/versions
	poetry run flake8 src tests alembic/versions

typecheck:
	poetry run dmypy run -- src tests

pre-commit: fmt lint typecheck tools-config-check

tools-config-check:
	poetry run actionlint
	poetry run check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/*.y*ml
	poetry run check-jsonschema --builtin-schema vendor.dependabot .github/dependabot.y*ml

test:
	poetry run pytest tests

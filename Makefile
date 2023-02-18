fmt:
	poetry run black src tests
	poetry run isort src tests

lint:
	poetry run black --check --diff src tests
	poetry run isort --check-only src tests
	poetry run flake8 src tests

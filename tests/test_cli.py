import pytest
from typer.testing import CliRunner

from foxops.__main__ import app


@pytest.fixture(scope="module")
def cli_runner() -> CliRunner:
    runner = CliRunner()
    return runner


def test_app_can_be_called(cli_runner):
    # WHEN
    result = cli_runner.invoke(app)

    # THEN
    assert result.exit_code == 0
    assert result.stdout.startswith("🦊")

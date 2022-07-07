import json
import logging
from pathlib import Path

import pytest
from typer.testing import CliRunner

from foxops.__main__ import app
from foxops.reconciliation import ReconciliationState


@pytest.fixture(scope="module")
def cli_runner() -> CliRunner:
    runner = CliRunner()
    return runner


def test_app_has_reconcile_command(cli_runner):
    # WHEN
    result = cli_runner.invoke(app, ["reconcile", "--help"])

    # THEN
    assert result.exit_code == 0
    assert result.stdout.startswith("Usage: ")


def test_app_fails_to_reconcile_when_gitlab_token_missing_in_env(cli_runner):
    # WHEN
    result = cli_runner.invoke(app, ["reconcile", "any-project-definition-config"])

    # THEN
    assert result.exit_code == 1


def test_app_exits_with_exit_code_1_for_unhandled_exceptions(
    cli_runner, tmp_path, mocker
):
    # GIVEN
    project_definition_config = tmp_path / "project-definition-config.yaml"
    project_definition_config.write_text(
        """
incarnations:
  - gitlab_project: some/project1
    template_repository: any-repository
    template_repository_version: any-version
    template_data: {}
  - gitlab_project: some/project2
    template_repository: any-repository
    template_repository_version: any-version
    template_data: {}
"""
    )

    mocker.patch(
        "foxops.__main__.reconcile",
        side_effect=Exception("any-exception"),
    )

    # WHEN
    result = cli_runner.invoke(
        app,
        ["reconcile", str(project_definition_config)],
        env={"FOXOPS_GITLAB_TOKEN": "any-token"},
    )

    # THEN
    assert result.exit_code == 1


def test_app_exits_with_exit_code_2_if_a_project_fails_to_reconcile(
    cli_runner, tmp_path, mocker
):
    # GIVEN
    project_definition_config = tmp_path / "project-definition-config.yaml"
    project_definition_config.write_text(
        """
incarnations:
  - gitlab_project: some/project1
    template_repository: any-repository
    template_repository_version: any-version
    template_data: {}
  - gitlab_project: some/project2
    template_repository: any-repository
    template_repository_version: any-version
    template_data: {}
"""
    )

    mocker.patch(
        "foxops.__main__.reconcile",
        return_value=[ReconciliationState.FAILED, ReconciliationState.UNCHANGED],
    )

    # WHEN
    result = cli_runner.invoke(
        app,
        ["reconcile", str(project_definition_config)],
        env={"FOXOPS_GITLAB_TOKEN": "any-token"},
    )

    # THEN
    assert result.exit_code == 2


def test_app_prints_reconciliation_summary_for_all_projects(
    cli_runner: CliRunner,
    tmp_path: Path,
    mocker,
    caplog,
):
    # GIVEN
    project_definition_config = tmp_path / "incarnations.yaml"
    project_definition_config.write_text(
        """
incarnations:
  - gitlab_project: test1
    template_repository: any-repository
    template_repository_version: any-repository-version
    template_data:
        any: any
  - gitlab_project: test2
    template_repository: any-repository
    template_repository_version: any-repository-version
    template_data:
        any: any
"""
    )

    mocker.patch(
        "foxops.__main__.reconcile",
        return_value=[ReconciliationState.UNSUPPORTED, ReconciliationState.UNCHANGED],
    )

    # WHEN
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(
            app,
            ["--json-logs", "reconcile", str(project_definition_config)],
            env={"FOXOPS_GITLAB_TOKEN": "any-token"},
        )

    # THEN
    summary_log_records = [
        r for r in caplog.records if json.loads(r.message).get("category") == "summary"
    ]
    assert result.exit_code == 0
    assert len(summary_log_records) == 2

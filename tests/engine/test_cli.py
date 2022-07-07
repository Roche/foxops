import json
import logging
from dataclasses import asdict
from pathlib import Path
from subprocess import check_output
from textwrap import dedent

import pytest
from typer.testing import CliRunner

from foxops.engine.__main__ import app
from foxops.engine.models import (
    IncarnationState,
    load_incarnation_state,
    save_incarnation_state,
)


@pytest.fixture(scope="module")
def cli_runner() -> CliRunner:
    runner = CliRunner()
    return runner


def init_repository(repository_dir):
    check_output(["git", "init", str(repository_dir)])
    check_output(["git", "config", "user.name", "test"], cwd=repository_dir)
    check_output(["git", "config", "user.email", "test@test.com"], cwd=repository_dir)


def commit_version(repository_dir, version):
    check_output(["git", "add", "."], cwd=repository_dir)
    check_output(["git", "commit", "-m", f"version: {version}"], cwd=repository_dir)
    check_output(["git", "tag", version], cwd=repository_dir)


@pytest.fixture()
def template_repository_without_variables(tmp_path: Path):
    template_repository_dir = tmp_path / "template-repository"
    init_repository(template_repository_dir)
    (template_repository_dir / "fengine.yaml").write_text("variables: {}")
    (template_repository_dir / "template").mkdir()
    (template_repository_dir / "template" / "README.md").write_text("# Hello World")
    commit_version(template_repository_dir, "v1")

    yield template_repository_dir


@pytest.fixture()
def template_repository(tmp_path: Path):
    template_repository_dir = tmp_path / "template-repository"
    init_repository(template_repository_dir)
    (template_repository_dir / "fengine.yaml").write_text(
        dedent(
            """
            variables:
                name:
                    type: str
                    description: the name

                age:
                    type: int
                    description: the age
            """
        )
    )
    (template_repository_dir / "template").mkdir()
    (template_repository_dir / "template" / "README.md").write_text(
        "# Hello, {{ name }} of age {{ age }}!"
    )
    commit_version(template_repository_dir, "v1")

    yield template_repository_dir


@pytest.fixture()
def template_repository_with_two_versions(template_repository: Path):
    (template_repository / "template" / "info.txt").write_text(
        "some info for {{ name }}."
    )
    commit_version(template_repository, "v2")

    yield template_repository


@pytest.fixture()
def template_repository_with_two_versions_different_variables(
    template_repository: Path,
):
    (template_repository / "fengine.yaml").write_text(
        (template_repository / "fengine.yaml").read_text()
        + """
    new:
        type: str
        description: the new
"""
    )
    (template_repository / "template" / "info.txt").write_text(
        "some info for {{ name }} with {{ new }}."
    )
    commit_version(template_repository, "v2")

    yield template_repository


@pytest.mark.parametrize("command", ["new", "initialize", "update"])
def test_app_has_commands(command, cli_runner: CliRunner):
    # WHEN
    result = cli_runner.invoke(app, [command, "--help"])

    # THEN
    assert result.exit_code == 0
    assert result.stdout.startswith("Usage: ")


def test_app_should_create_template(
    cli_runner: CliRunner,
    tmp_path: Path,
):
    # WHEN
    result = cli_runner.invoke(app, ["new", str(tmp_path)])

    # THEN
    assert result.exit_code == 0
    assert (tmp_path / "fengine.yaml").exists()
    assert (tmp_path / "template" / "README.md").exists()


def test_app_should_initialize_incarnation_from_template_without_variables(
    cli_runner: CliRunner,
    template_repository_without_variables: Path,
    tmp_path: Path,
):
    # GIVEN
    incarnation_dir = tmp_path / "incarnation"

    # WHEN
    result = cli_runner.invoke(
        app,
        [
            "initialize",
            str(template_repository_without_variables),
            str(incarnation_dir),
        ],
    )

    # THEN
    assert result.exit_code == 0
    assert (incarnation_dir / "README.md").read_text() == "# Hello World"


def test_app_should_initialize_incarnation_from_template_with_variables(
    cli_runner: CliRunner,
    template_repository: Path,
    tmp_path: Path,
):
    # GIVEN
    incarnation_dir = tmp_path / "incarnation"

    # WHEN
    result = cli_runner.invoke(
        app,
        [
            "initialize",
            str(template_repository),
            str(incarnation_dir),
            "-d",
            "name=jon",
            "-d",
            "age=42",
        ],
    )

    # THEN
    assert result.exit_code == 0
    assert (incarnation_dir / "README.md").read_text() == "# Hello, jon of age 42!"


def test_app_should_initialize_incarnation_of_specific_template_version(
    cli_runner: CliRunner,
    template_repository_with_two_versions: Path,
    tmp_path: Path,
):
    # GIVEN
    incarnation_dir = tmp_path / "incarnation"

    # WHEN
    result = cli_runner.invoke(
        app,
        [
            "initialize",
            str(template_repository_with_two_versions),
            str(incarnation_dir),
            "-d",
            "name=jon",
            "-d",
            "age=42",
            "--template-version",
            "v1",
        ],
    )

    # THEN
    assert result.exit_code == 0
    assert not (incarnation_dir / "info.txt").exists()


def test_app_should_update_incarnation_to_head_in_template_repository(
    cli_runner: CliRunner,
    template_repository_with_two_versions: Path,
    tmp_path: Path,
):
    # GIVEN
    incarnation_dir = tmp_path / "incarnation"

    cli_runner.invoke(
        app,
        [
            "initialize",
            str(template_repository_with_two_versions),
            str(incarnation_dir),
            "-d",
            "name=jon",
            "-d",
            "age=42",
            "--template-version",
            "v1",
        ],
    )
    init_repository(incarnation_dir)
    commit_version(incarnation_dir, "v1")

    # WHEN
    result = cli_runner.invoke(
        app,
        [
            "update",
            str(incarnation_dir),
        ],
    )

    # THEN
    assert result.exit_code == 0
    assert (incarnation_dir / "info.txt").read_text() == "some info for jon."


def test_app_should_update_incarnation_to_specific_version_in_template_repository(
    cli_runner: CliRunner,
    template_repository_with_two_versions: Path,
    tmp_path: Path,
):
    # GIVEN
    incarnation_dir = tmp_path / "incarnation"

    cli_runner.invoke(
        app,
        [
            "initialize",
            str(template_repository_with_two_versions),
            str(incarnation_dir),
            "-d",
            "name=jon",
            "-d",
            "age=42",
            "--template-version",
            "v1",
        ],
    )
    init_repository(incarnation_dir)
    commit_version(incarnation_dir, "v1")

    # WHEN
    result = cli_runner.invoke(
        app,
        [
            "update",
            str(incarnation_dir),
            "-u",
            "v2",
        ],
    )

    # THEN
    assert result.exit_code == 0
    assert (incarnation_dir / "info.txt").read_text() == "some info for jon."
    incarnation_state = load_incarnation_state(incarnation_dir / ".fengine.yaml")
    assert incarnation_state.template_repository_version == "v2"
    assert incarnation_state.template_repository_version_hash != "v2"


def test_app_should_update_incarnation_to_version_with_new_variable(
    cli_runner: CliRunner,
    template_repository_with_two_versions_different_variables: Path,
    tmp_path: Path,
):
    # GIVEN
    incarnation_dir = tmp_path / "incarnation"

    cli_runner.invoke(
        app,
        [
            "initialize",
            str(template_repository_with_two_versions_different_variables),
            str(incarnation_dir),
            "-d",
            "name=jon",
            "-d",
            "age=42",
            "--template-version",
            "v1",
        ],
    )
    init_repository(incarnation_dir)
    commit_version(incarnation_dir, "v1")

    # WHEN
    result = cli_runner.invoke(
        app,
        [
            "update",
            str(incarnation_dir),
            "-d",
            "new=foobar",
            "-u",
            "v2",
        ],
    )

    # THEN
    assert result.exit_code == 0
    assert (
        incarnation_dir / "info.txt"
    ).read_text() == "some info for jon with foobar."


def test_app_should_update_incarnation_to_version_with_removed_variable(
    cli_runner: CliRunner,
    template_repository_with_two_versions_different_variables: Path,
    tmp_path: Path,
):
    # GIVEN
    incarnation_dir = tmp_path / "incarnation"

    cli_runner.invoke(
        app,
        [
            "initialize",
            str(template_repository_with_two_versions_different_variables),
            str(incarnation_dir),
            "-d",
            "name=jon",
            "-d",
            "age=42",
            "-d",
            "new=foobar",
            "--template-version",
            "v2",
        ],
    )
    init_repository(incarnation_dir)
    commit_version(incarnation_dir, "v1")

    # WHEN
    result = cli_runner.invoke(
        app,
        [
            "update",
            str(incarnation_dir),
            "--remove-data",
            "new",
            "-u",
            "v1",
        ],
    )

    # THEN
    assert result.exit_code == 0
    assert not (incarnation_dir / "info.txt").exists()


def test_app_should_update_incarnation_with_new_variable_data(
    cli_runner: CliRunner,
    template_repository: Path,
    tmp_path: Path,
):
    # GIVEN
    incarnation_dir = tmp_path / "incarnation"

    cli_runner.invoke(
        app,
        [
            "initialize",
            str(template_repository),
            str(incarnation_dir),
            "-d",
            "name=jon",
            "-d",
            "age=42",
            "--template-version",
            "v1",
        ],
    )
    init_repository(incarnation_dir)
    commit_version(incarnation_dir, "v1")

    # WHEN
    result = cli_runner.invoke(
        app,
        [
            "update",
            str(incarnation_dir),
            "-d",
            "name=ygritte",
            "-u",
            "v1",
        ],
    )

    # THEN
    assert result.exit_code == 0
    assert (incarnation_dir / "README.md").read_text() == "# Hello, ygritte of age 42!"


def test_app_update_incarnation_should_complain_if_template_repository_is_not_a_local_path(
    cli_runner: CliRunner,
    template_repository_with_two_versions: Path,
    tmp_path: Path,
    caplog,
):
    # GIVEN
    incarnation_dir = tmp_path / "incarnation"

    cli_runner.invoke(
        app,
        [
            "initialize",
            str(template_repository_with_two_versions),
            str(incarnation_dir),
            "-d",
            "name=jon",
            "-d",
            "age=42",
            "--template-version",
            "v1",
        ],
    )

    # NOTE(TF): patch the `.fengine.yaml` file to point to a remote Git template repository.
    #           This would be the case if the template wasn't initialized locally, but with
    #           foxops and later on cloned to develop locally using the `fengine` cli tool.
    incarnation_state = load_incarnation_state(incarnation_dir / ".fengine.yaml")
    patched_incarnation_state = IncarnationState(
        **{
            **asdict(incarnation_state),  # type: ignore
            "template_repository": "https://any-remote-repository.com/any-repository.git",
        }
    )
    save_incarnation_state(incarnation_dir / ".fengine.yaml", patched_incarnation_state)

    init_repository(incarnation_dir)
    commit_version(incarnation_dir, "v1")

    # WHEN
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(
            app,
            [
                "--json-logs",
                "update",
                str(incarnation_dir),
                "-u",
                "v2",
            ],
        )

    # THEN
    assert result.exit_code == 1
    assert caplog.records[-1].levelname == "ERROR"
    assert (
        "is not a local directory. Might it be an URL?"
        in json.loads(caplog.records[-1].message)["event"]
    )


def test_app_should_update_incarnation_with_overridden_template_repository(
    cli_runner: CliRunner,
    template_repository_with_two_versions: Path,
    tmp_path: Path,
):
    # GIVEN
    incarnation_dir = tmp_path / "incarnation"

    cli_runner.invoke(
        app,
        [
            "initialize",
            str(template_repository_with_two_versions),
            str(incarnation_dir),
            "-d",
            "name=jon",
            "-d",
            "age=42",
            "--template-version",
            "v1",
        ],
    )

    # NOTE(TF): patch the `.fengine.yaml` file to point to a remote Git template repository.
    #           This would be the case if the template wasn't initialized locally, but with
    #           foxops and later on cloned to develop locally using the `fengine` cli tool.
    incarnation_state = load_incarnation_state(incarnation_dir / ".fengine.yaml")
    patched_incarnation_state = IncarnationState(
        **{
            **asdict(incarnation_state),  # type: ignore
            "template_repository": "https://any-remote-repository.com/any-repository.git",
        }
    )
    save_incarnation_state(incarnation_dir / ".fengine.yaml", patched_incarnation_state)

    init_repository(incarnation_dir)
    commit_version(incarnation_dir, "v1")

    # WHEN
    result = cli_runner.invoke(
        app,
        [
            "update",
            str(incarnation_dir),
            "-u",
            "v2",
            "-r",
            str(template_repository_with_two_versions),
        ],
    )

    # THEN
    assert result.exit_code == 0
    assert (incarnation_dir / "info.txt").read_text() == "some info for jon."

from pathlib import Path

import pytest

from foxops import utils
from foxops.engine import IncarnationState, initialize_incarnation
from foxops.engine.errors import ProvidedTemplateDataInvalidError
from foxops.engine.models.template_config import (
    IntegerVariableDefinition,
    StringVariableDefinition,
    TemplateConfig,
)


async def init_repository(repository_dir: Path) -> str:
    await utils.check_call("git", "init", cwd=repository_dir)
    await utils.check_call("git", "config", "user.name", "test", cwd=repository_dir)
    await utils.check_call("git", "config", "user.email", "test@test.com", cwd=repository_dir)
    await utils.check_call("git", "add", ".", cwd=repository_dir)
    await utils.check_call("git", "commit", "-m", "initial commit", cwd=repository_dir)
    proc = await utils.check_call("git", "rev-parse", "HEAD", cwd=repository_dir)
    return (await proc.stdout.read()).decode().strip()  # type: ignore


async def test_initialize_template_at_root_of_incarnation_repository(tmp_path: Path):
    # GIVEN
    (tmp_path / "fengine.yaml").write_text(
        """
variables:
  author:
    type: str
    description: dummy
  three:
    type: int
    description: dummy"""
    )

    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "README.md").write_text("{{ author }} knows that 1+2 = {{ three }}")
    repository_head = await init_repository(tmp_path)

    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    # WHEN
    await initialize_incarnation(
        template_root_dir=tmp_path,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={"author": "John Doe", "three": 3},
        incarnation_root_dir=incarnation_dir,
    )

    # THEN
    assert (incarnation_dir / "README.md").read_text() == "John Doe knows that 1+2 = 3"

    incarnation_state = IncarnationState.from_file(incarnation_dir / ".fengine.yaml")
    assert incarnation_state.template_repository == "any-repository-url"
    assert incarnation_state.template_repository_version == "any-version"
    assert incarnation_state.template_repository_version_hash == repository_head

    assert incarnation_state.template_data["author"] == "John Doe"
    assert incarnation_state.template_data["three"] == 3
    assert "fengine" not in incarnation_state.template_data

    assert incarnation_state.template_data_full["author"] == "John Doe"
    assert incarnation_state.template_data_full["three"] == 3
    assert incarnation_state.template_data_full["fengine"]["template"]["repository"] == "any-repository-url"
    assert incarnation_state.template_data_full["fengine"]["template"]["repository_version"] == "any-version"


async def test_initialize_template_at_root_of_incarnation_repository_using_fengine_metadata(tmp_path: Path):
    # GIVEN
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "template_repository").write_text("{{ _fengine_template_repository }}")
    (template_dir / "template_repository_version").write_text("{{ _fengine_template_repository_version }}")
    await init_repository(tmp_path)

    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    # WHEN
    await initialize_incarnation(
        template_root_dir=tmp_path,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={"author": "John Doe", "three": 3},
        incarnation_root_dir=incarnation_dir,
    )

    # THEN
    assert (incarnation_dir / "template_repository").read_text() == "any-repository-url"
    assert (incarnation_dir / "template_repository_version").read_text() == "any-version"


async def test_initialize_template_at_root_of_incarnation_repository_with_existing_file(
    tmp_path: Path,
):
    # GIVEN
    TemplateConfig(
        variables={
            "author": StringVariableDefinition(description="dummy"),
            "three": IntegerVariableDefinition(description="dummy"),
        }
    ).save(tmp_path / "fengine.yaml")

    await init_repository(tmp_path)
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "README.md").write_text("{{ author }} knows that 1+2 = {{ three }}")

    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()
    (incarnation_dir / "README.md").write_text("I exist already")
    (incarnation_dir / "config.yaml").write_text("existing: true")

    # WHEN
    await initialize_incarnation(
        template_root_dir=tmp_path,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={"author": "John Doe", "three": 3},
        incarnation_root_dir=incarnation_dir,
    )

    # THEN
    assert (incarnation_dir / "config.yaml").read_text() == "existing: true"
    assert (incarnation_dir / "README.md").read_text() == "John Doe knows that 1+2 = 3"


async def test_initialize_template_fails_when_variables_are_not_set(tmp_path):
    # GIVEN
    (tmp_path / "fengine.yaml").write_text(
        """
variables:
  author:
    type: str
    description: dummy
  three:
    type: int
    description: dummy"""
    )

    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "README.md").write_text("{{ author }} knows that 1+2 = {{ three }}")

    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    # THEN
    with pytest.raises(ProvidedTemplateDataInvalidError):
        await initialize_incarnation(
            template_root_dir=tmp_path,
            template_repository="any-repository-url",
            template_repository_version="any-version",
            template_data={"author": "John Doe"},
            incarnation_root_dir=incarnation_dir,
        )


async def test_initialize_template_used_passed_value_instead_default_for_optional_variables(
    tmp_path,
):
    # GIVEN
    (tmp_path / "fengine.yaml").write_text(
        """
variables:
  author:
    type: str
    description: dummy
  three:
    type: int
    description: dummy
    default: 42"""
    )

    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "README.md").write_text("{{ author }} knows that 1+2 = {{ three }}")
    await init_repository(tmp_path)

    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    # WHEN
    await initialize_incarnation(
        template_root_dir=tmp_path,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={"author": "John Doe", "three": 3},
        incarnation_root_dir=incarnation_dir,
    )

    # THEN
    assert (incarnation_dir / "README.md").read_text() == "John Doe knows that 1+2 = 3"


async def test_initialize_template_allows_optional_variables(tmp_path):
    # GIVEN
    (tmp_path / "fengine.yaml").write_text(
        """
variables:
  author:
    type: str
    description: dummy
  three:
    type: int
    description: dummy
    default: 42"""
    )

    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "README.md").write_text("{{ author }} knows that 1+2 = {{ three }}")
    await init_repository(tmp_path)

    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    # WHEN
    await initialize_incarnation(
        template_root_dir=tmp_path,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={"author": "John Doe"},
        incarnation_root_dir=incarnation_dir,
    )

    # THEN
    assert (incarnation_dir / "README.md").read_text() == "John Doe knows that 1+2 = 42"


async def test_initialize_template_ignores_but_warns_about_additional_variables(tmp_path, mocker):
    # GIVEN
    (tmp_path / "fengine.yaml").write_text(
        """
variables:
  author:
    type: str
    description: dummy
  three:
    type: int
    description: dummy
    default: 42"""
    )

    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "README.md").write_text("{{ author }} knows that 1+2 = {{ three }}")
    await init_repository(tmp_path)

    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    template_data_with_additional_values = {
        "author": "John Doe",
        "additional_variable_1": "any value",
        "additional_variable_2": 42,
    }

    # WHEN
    incarnation_state = await initialize_incarnation(
        template_root_dir=tmp_path,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data=template_data_with_additional_values,
        incarnation_root_dir=incarnation_dir,
    )

    # THEN
    assert incarnation_state is not None

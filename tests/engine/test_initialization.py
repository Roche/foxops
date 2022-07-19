from pathlib import Path

import pytest

from foxops import utils
from foxops.engine import initialize_incarnation


async def init_repository(repository_dir: Path) -> None:
    await utils.check_call("git", "init", cwd=repository_dir)
    await utils.check_call("git", "config", "user.name", "test", cwd=repository_dir)
    await utils.check_call(
        "git", "config", "user.email", "test@test.com", cwd=repository_dir
    )
    await utils.check_call("git", "add", ".", cwd=repository_dir)
    await utils.check_call("git", "commit", "-m", "initial commit", cwd=repository_dir)
    proc = await utils.check_call("git", "rev-parse", "HEAD", cwd=repository_dir)
    return (await proc.stdout.read()).decode().strip()  # type: ignore


@pytest.mark.asyncio
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
        template_data={"author": "John Doe", "three": "3"},
        incarnation_root_dir=incarnation_dir,
    )

    # THEN
    assert (incarnation_dir / "README.md").read_text() == "John Doe knows that 1+2 = 3"
    assert (
        (incarnation_dir / ".fengine.yaml").read_text()
        == f"""# This file is auto-generated and owned by foxops.
# DO NOT EDIT MANUALLY.
template_data:
  author: John Doe
  three: '3'
template_repository: any-repository-url
template_repository_version: any-version
template_repository_version_hash: {repository_head}
"""
    )


@pytest.mark.asyncio
async def test_initialize_template_at_root_of_incarnation_repository_with_existing_file(
    tmp_path: Path,
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
    description: dummy"""
    )

    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "README.md").write_text("{{ author }} knows that 1+2 = {{ three }}")
    repository_head = await init_repository(tmp_path)

    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()
    (incarnation_dir / "README.md").write_text("I exist already")
    (incarnation_dir / "config.yaml").write_text("existing: true")

    # WHEN
    await initialize_incarnation(
        template_root_dir=tmp_path,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={"author": "John Doe", "three": "3"},
        incarnation_root_dir=incarnation_dir,
    )

    # THEN
    assert (incarnation_dir / "config.yaml").read_text() == "existing: true"
    assert (incarnation_dir / "README.md").read_text() == "John Doe knows that 1+2 = 3"
    assert (
        (incarnation_dir / ".fengine.yaml").read_text()
        == f"""# This file is auto-generated and owned by foxops.
# DO NOT EDIT MANUALLY.
template_data:
  author: John Doe
  three: '3'
template_repository: any-repository-url
template_repository_version: any-version
template_repository_version_hash: {repository_head}
"""
    )


@pytest.mark.asyncio
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
    with pytest.raises(ValueError):
        await initialize_incarnation(
            template_root_dir=tmp_path,
            template_repository="any-repository-url",
            template_repository_version="any-version",
            template_data={"author": "John Doe"},
            incarnation_root_dir=incarnation_dir,
        )


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_initialize_template_ignores_but_warns_about_additional_variables(
    tmp_path, mocker
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


@pytest.mark.asyncio
async def test_initialize_template_with_variables_from_fvars_file(tmp_path: Path):
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
    (incarnation_dir / "default.fvars").write_text(
        """
        author=John Doe
        """
    )

    # WHEN
    await initialize_incarnation(
        template_root_dir=tmp_path,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={"three": "3"},
        incarnation_root_dir=incarnation_dir,
    )

    # THEN
    assert (incarnation_dir / "README.md").read_text() == "John Doe knows that 1+2 = 3"
    assert (
        (incarnation_dir / ".fengine.yaml").read_text()
        == f"""# This file is auto-generated and owned by foxops.
# DO NOT EDIT MANUALLY.
template_data:
  author: John Doe
  three: '3'
template_repository: any-repository-url
template_repository_version: any-version
template_repository_version_hash: {repository_head}
"""
    )


@pytest.mark.asyncio
async def test_initialize_template_template_data_precedence_over_fvars(tmp_path: Path):
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
    (incarnation_dir / "default.fvars").write_text(
        """
        author=John Doe
        """
    )

    # WHEN
    await initialize_incarnation(
        template_root_dir=tmp_path,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={"author": "Overridden John Doe", "three": "3"},
        incarnation_root_dir=incarnation_dir,
    )

    # THEN
    assert (
        incarnation_dir / "README.md"
    ).read_text() == "Overridden John Doe knows that 1+2 = 3"
    assert (
        (incarnation_dir / ".fengine.yaml").read_text()
        == f"""# This file is auto-generated and owned by foxops.
# DO NOT EDIT MANUALLY.
template_data:
  author: Overridden John Doe
  three: '3'
template_repository: any-repository-url
template_repository_version: any-version
template_repository_version_hash: {repository_head}
"""
    )


@pytest.mark.asyncio
async def test_initialize_template_empty_fvars_file(tmp_path: Path):
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
    (incarnation_dir / "default.fvars").write_text("")

    # WHEN
    await initialize_incarnation(
        template_root_dir=tmp_path,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={"author": "John Doe", "three": "3"},
        incarnation_root_dir=incarnation_dir,
    )

    # THEN
    assert (incarnation_dir / "README.md").read_text() == "John Doe knows that 1+2 = 3"
    assert (
        (incarnation_dir / ".fengine.yaml").read_text()
        == f"""# This file is auto-generated and owned by foxops.
# DO NOT EDIT MANUALLY.
template_data:
  author: John Doe
  three: '3'
template_repository: any-repository-url
template_repository_version: any-version
template_repository_version_hash: {repository_head}
"""
    )

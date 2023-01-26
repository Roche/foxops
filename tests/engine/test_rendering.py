import stat
from pathlib import Path
from tempfile import TemporaryDirectory

import jinja2
import pytest

from foxops.engine.rendering import (
    create_template_environment,
    render_template,
    render_template_file,
    render_template_symlink,
)


def supports_symlink_permissions():
    """Check if the current platform supports setting permissions on symlinks."""
    with TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "symlink"
        p.symlink_to(Path(tmpdir) / "target")
        try:
            p.chmod(0o755, follow_symlinks=False)
        except NotImplementedError:
            return False
        else:
            return True


async def test_rendering_a_template_file_renders_data_in_file_content(tmp_path: Path):
    # GIVEN
    template_file = tmp_path / "template.txt"
    template_file.write_text("{{ data }}")
    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    env = create_template_environment(tmp_path)

    # WHEN
    await render_template_file(
        env,
        template_file,
        incarnation_dir,
        {"data": "Hello World"},
        render_content=True,
    )

    # THEN
    assert (incarnation_dir / "template.txt").read_text() == "Hello World"


async def test_rendering_a_template_file_with_invalid_templating_syntax_raises_exception(
    tmp_path: Path,
):
    # GIVEN
    template_file = tmp_path / "template.txt"
    template_file.write_text("{{ data }")
    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    env = create_template_environment(tmp_path)

    # THEN
    with pytest.raises(jinja2.TemplateSyntaxError):
        # WHEN
        await render_template_file(
            env,
            template_file,
            incarnation_dir,
            {"data": "Hello World"},
            render_content=True,
        )


async def test_rendering_a_template_file_renders_data_in_filename(tmp_path: Path):
    # GIVEN
    template_file = tmp_path / "template-{{ idx }}.txt"
    template_file.touch()
    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    env = create_template_environment(tmp_path)

    # WHEN
    await render_template_file(
        env,
        template_file,
        incarnation_dir,
        {"idx": "42"},
        render_content=True,
    )

    # THEN
    assert (incarnation_dir / "template-42.txt").exists()


async def test_rendering_a_template_file_renders_data_in_entire_filepath(
    tmp_path: Path,
):
    # GIVEN
    template_file = tmp_path / "project-{{ name }}/{{ subdir }}/template-{{ idx }}.txt"
    template_file.parent.mkdir(parents=True)
    template_file.touch()
    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    env = create_template_environment(tmp_path)

    # WHEN
    await render_template_file(
        env,
        template_file,
        incarnation_dir,
        {"name": "jon", "subdir": "tests", "idx": "42"},
        render_content=True,
    )

    # THEN
    assert (incarnation_dir / "project-jon" / "tests" / "template-42.txt").exists()


async def test_rendering_a_template_symlink_renders_data_in_filename(tmp_path: Path):
    # GIVEN
    template_symlink = tmp_path / "template-symlink-{{ idx }}"
    template_symlink.symlink_to("template.txt")
    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    env = create_template_environment(tmp_path)

    # WHEN
    await render_template_symlink(env, template_symlink, incarnation_dir, {"idx": "42"})

    # THEN
    assert (incarnation_dir / "template-symlink-42").is_symlink()
    assert (incarnation_dir / "template-symlink-42").readlink() == Path("template.txt")


async def test_rendering_a_template_symlink_renders_data_in_target_filename(
    tmp_path: Path,
):
    # GIVEN
    template_symlink = tmp_path / "template-symlink"
    template_symlink.symlink_to("symlink-target-{{ idx }}.txt")
    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    env = create_template_environment(tmp_path)

    # WHEN
    await render_template_symlink(env, template_symlink, incarnation_dir, {"idx": "42"})

    # THEN
    assert (incarnation_dir / "template-symlink").is_symlink()
    assert (incarnation_dir / "template-symlink").readlink() == Path("symlink-target-42.txt")


async def test_rendering_an_entire_template_directory_with_excluded_file(
    tmp_path: Path,
):
    # GIVEN
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "README.md").write_text("{{ invalid syntax } {%")
    (template_dir / "code.c").write_text("{{ data }}")

    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    excludes = [
        "README.md",
    ]

    # WHEN
    await render_template(
        template_dir,
        incarnation_dir,
        {"data": "Hello World"},
        rendering_filename_exclude_patterns=excludes,
    )

    # THEN
    assert (incarnation_dir / "README.md").read_text() == "{{ invalid syntax } {%"
    assert (incarnation_dir / "code.c").read_text() == "Hello World"


async def test_rendering_an_entire_template_directory_with_excluded_file_in_rendered_subdir(
    tmp_path: Path,
):
    # GIVEN
    template_dir = tmp_path / "template"
    template_dir.mkdir()

    (template_dir / "{{ package_name }}").mkdir()
    (template_dir / "{{ package_name }}" / "README.md").write_text("{{ invalid syntax } {%")
    (template_dir / "code.c").write_text("{{ data }}")

    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    excludes = [
        "{{ package_name }}/*",
    ]

    # WHEN
    await render_template(
        template_dir,
        incarnation_dir,
        {"data": "Hello World", "package_name": "test"},
        rendering_filename_exclude_patterns=excludes,
    )

    # THEN
    assert (incarnation_dir / "test" / "README.md").read_text() == "{{ invalid syntax } {%"
    assert (incarnation_dir / "code.c").read_text() == "Hello World"


async def test_rendering_an_entire_template_directory(tmp_path: Path):
    # GIVEN
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "README.md").write_text("README: {{ data }}")
    (template_dir / "{{ name }}").mkdir()
    (template_dir / "{{ name }}" / "code.c").write_text("{{ data }}")
    (template_dir / "tests" / "{{ name }}").mkdir(parents=True)
    (template_dir / "tests" / "{{ name }}" / "test_code.c").write_text("Test: {{ data }}")
    (template_dir / "README-symlink").symlink_to("README.md")
    (template_dir / "test_code-symlink").symlink_to("tests/{{ name }}/test_code.c")

    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    # WHEN
    await render_template(
        template_dir,
        incarnation_dir,
        {"name": "jon", "data": "Hello World"},
        [],
    )

    # THEN
    assert (incarnation_dir / "README.md").read_text() == "README: Hello World"
    assert (incarnation_dir / "jon").exists()
    assert (incarnation_dir / "jon" / "code.c").read_text() == "Hello World"
    assert (incarnation_dir / "tests" / "jon" / "test_code.c").read_text() == "Test: Hello World"
    assert (incarnation_dir / "README-symlink").is_symlink()
    assert (incarnation_dir / "README-symlink").exists()
    assert (incarnation_dir / "README-symlink").readlink() == Path("README.md")
    assert (incarnation_dir / "test_code-symlink").is_symlink()
    assert (incarnation_dir / "test_code-symlink").exists()
    assert (incarnation_dir / "test_code-symlink").readlink() == Path("tests/jon/test_code.c")


async def test_rendering_a_template_file_inherits_file_permissions(tmp_path: Path):
    # GIVEN
    template_file = tmp_path / "template.txt"
    template_file.touch()
    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    # change permissions on template file
    mode_before_xusr = template_file.stat().st_mode
    template_file.chmod(template_file.stat().st_mode | stat.S_IXUSR)
    expected_mode = stat.S_IMODE(mode_before_xusr | stat.S_IXUSR)

    env = create_template_environment(tmp_path)

    # WHEN
    await render_template_file(env, template_file, incarnation_dir, {}, render_content=True)

    # THEN
    assert (incarnation_dir / "template.txt").exists()
    assert stat.S_IMODE((incarnation_dir / "template.txt").stat().st_mode) == expected_mode


@pytest.mark.skipif(
    not supports_symlink_permissions(),
    reason="Platform doesn't support setting symlink permissions",
)
async def test_rendering_a_template_symlink_inherits_file_permissions(tmp_path: Path):
    # GIVEN
    template_file = tmp_path / "template.txt"
    template_file.write_text("test")
    template_symlink = tmp_path / "template-symlink"
    template_symlink.symlink_to(template_file)
    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    # change permissions on template file
    template_file.chmod(template_file.stat().st_mode | stat.S_IXUSR)

    # change permissions on template symlink
    mode_before_woth = template_symlink.stat(follow_symlinks=False).st_mode  # type: ignore
    template_symlink.chmod(mode_before_woth | stat.S_IWOTH, follow_symlinks=False)  # type: ignore
    expected_symlink_mode = stat.S_IMODE(mode_before_woth | stat.S_IWOTH)

    env = create_template_environment(tmp_path)

    # WHEN
    await render_template_file(
        env,
        template_file,
        incarnation_dir,
        {},
        render_content=True,
    )
    await render_template_file(
        env,
        template_symlink,
        incarnation_dir,
        {},
        render_content=True,
    )

    # THEN
    assert (incarnation_dir / "template-symlink").exists()
    assert (
        stat.S_IMODE((incarnation_dir / "template-symlink").stat(follow_symlinks=False).st_mode)  # type: ignore
        == expected_symlink_mode
    )


async def test_rendering_a_template_directory_inherits_file_permissions(tmp_path: Path):
    # GIVEN
    template_dir = tmp_path / "template"
    template_subdir = template_dir / "subdir"
    template_file = template_subdir / "template.txt"
    template_dir.mkdir()
    template_subdir.mkdir()
    template_file.touch()

    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    # change permissions on template file
    subdir_mode_before_woth = template_subdir.stat().st_mode
    template_subdir.chmod(template_subdir.stat().st_mode | stat.S_IWOTH)
    expected_subdir_mode = stat.S_IMODE(subdir_mode_before_woth | stat.S_IWOTH)

    file_mode_before_xusr = template_file.stat().st_mode
    template_file.chmod(template_file.stat().st_mode | stat.S_IXUSR)
    expected_file_mode = stat.S_IMODE(file_mode_before_xusr | stat.S_IXUSR)

    # WHEN
    await render_template(template_dir, incarnation_dir, {}, [])

    # THEN
    assert (incarnation_dir / "subdir").exists()
    assert stat.S_IMODE((incarnation_dir / "subdir").stat().st_mode) == expected_subdir_mode
    assert (incarnation_dir / "subdir" / "template.txt").exists()
    assert stat.S_IMODE((incarnation_dir / "subdir" / "template.txt").stat().st_mode) == expected_file_mode


@pytest.mark.parametrize(
    "orig,statement,expected",
    [
        ("192.168.0.0", "{{ x | ip_add_integer }}", "192.168.0.1"),
        ("192.168.0.0", "{{ x | ip_add_integer(2) }}", "192.168.0.2"),
    ],
)
async def test_availability_of_custom_filters(tmp_path: Path, orig: str, statement: str, expected: str):
    # GIVEN
    template_file = tmp_path / "template.txt"
    template_file.write_text(statement)
    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    env = create_template_environment(tmp_path)

    # WHEN
    await render_template_file(
        env,
        template_file,
        incarnation_dir,
        {"x": orig},
        render_content=True,
    )
    # THEN
    assert (incarnation_dir / "template.txt").read_text() == expected

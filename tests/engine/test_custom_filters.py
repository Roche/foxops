from pathlib import Path

from foxops.engine.rendering import create_template_environment, render_template_file


async def test_custom_filter_ip_add_increase(tmp_path: Path):
    # GIVEN
    template_file = tmp_path / "template.txt"
    template_file.write_text("increased ip: {{ ip | ip_add_increase }}")
    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    env = create_template_environment(tmp_path)

    # WHEN
    await render_template_file(
        env,
        template_file,
        incarnation_dir,
        {"ip": "1.2.3.4"},
        render_content=True,
    )
    # THEN
    assert (incarnation_dir / "template.txt").read_text() == "increased ip: 1.2.3.5"


async def test_custom_filter_ip_add_increase_by_5(tmp_path: Path):
    # GIVEN
    template_file = tmp_path / "template.txt"
    template_file.write_text("increased ip by 5: {{ ip | ip_add_increase(5) }}")
    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    env = create_template_environment(tmp_path)

    # WHEN
    await render_template_file(
        env,
        template_file,
        incarnation_dir,
        {"ip": "1.2.3.4"},
        render_content=True,
    )
    # THEN
    assert (incarnation_dir / "template.txt").read_text() == "increased ip by 5: 1.2.3.9"

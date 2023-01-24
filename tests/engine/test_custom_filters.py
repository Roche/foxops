from pathlib import Path

from foxops.engine.rendering import create_template_environment, render_template_file


async def test_rendering_custom_filter_increase_ip_add(tmp_path: Path):
    # GIVEN
    template_file = tmp_path / "template.txt"
    template_file.write_text("increased ip: {{ ip | increase_ip_add }}")
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


async def test_rendering_custom_filter_increase_ip_add_by_5(tmp_path: Path):
    # GIVEN
    template_file = tmp_path / "template.txt"
    template_file.write_text("increased ip by 5: {{ ip | increase_ip_add(5) }}")
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


async def test_rendering_custom_filter_first_ip_address_is_greater(tmp_path: Path):
    # GIVEN
    template_file = tmp_path / "template.txt"
    template_file.write_text(
        "ip {{ ip }} is greater than {{second_ip}}: {{ip | first_ip_address_is_greater_than(second_ip)}}"
    )
    incarnation_dir = tmp_path / "incarnation"
    incarnation_dir.mkdir()

    env = create_template_environment(tmp_path)

    # WHEN
    await render_template_file(
        env,
        template_file,
        incarnation_dir,
        {"ip": "1.2.3.4", "second_ip": "1.2.3.5"},
        render_content=True,
    )
    # THEN
    assert (incarnation_dir / "template.txt").read_text() == "ip 1.2.3.4 is greater than 1.2.3.5: False"
